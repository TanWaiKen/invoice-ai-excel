from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

# Import required modules
try:
    from src.models.data_models import ProcessingRequest, ProcessingResult, InvoiceData
    from src.models.client_models import InvoiceProcessorClient
    from src.knowledge_base.kb_manager import KnowledgeBaseManager
    from src.excel.excel_creator import ExcelCreator
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="Invoice AI Processor", 
    version="1.0.0",
    description="Process invoice images using AI OCR and generate Excel reports"
)

# CRITICAL: Add CORS middleware BEFORE any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:34115", "http://wails.localhost:34115"],  # Add your Wails origin here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components (singleton pattern)
_kb_manager = None
_processor_client = None
_excel_creator = None

def get_components():
    """Initialize system components once"""
    global _kb_manager, _processor_client, _excel_creator
    
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager()
        _processor_client = InvoiceProcessorClient(_kb_manager)
        _excel_creator = ExcelCreator()
    
    return _kb_manager, _processor_client, _excel_creator

# Get components
kb_manager, processor_client, excel_creator = get_components()

# Add a test OPTIONS handler for debugging
@app.options("/process-invoices")
async def options_process_invoices():
    """Handle OPTIONS preflight request"""
    return {"message": "OPTIONS request successful"}

@app.post("/process-invoices", response_model=ProcessingResult)
async def process_invoices(request: ProcessingRequest):
    """
    Main service: Process invoice images with Excel template to generate Excel report
    """
    try:
        # Validate input paths
        if not os.path.exists(request.image_folder):
            raise HTTPException(status_code=404, detail="Image folder not found")
        
        if not os.path.exists(request.excel_template_path):
            raise HTTPException(status_code=404, detail="Excel template not found")
        
        # Load knowledge base from Excel template
        kb_manager.load_from_excel(request.excel_template_path)
        
        # Process all invoice images
        processed_data = processor_client.process_images_folder(request.image_folder)
        
        if not processed_data:
            raise HTTPException(status_code=400, detail="No invoices could be processed")
        
        print(f"🔍 Total images processed by OCR: {len(processed_data)}")
        for i, data in enumerate(processed_data):
            print(f"   {i+1}. Invoice: {data.get('invoice_no')} | Customer: {data.get('customer_name')} | Weight: {data.get('weight_kg')} | is_count: {data.get('is_count', 'Unknown')}")
        
        # Convert to InvoiceData objects (ONLY PASS INVOICEDATA OBJECTS TO EXCEL)
        invoice_objects = []
        fuzzy_matches = []
        new_customers = []
        
        for data in processed_data:
            try:
                # Clean and validate data first
                original_name = str(data.get("customer_name", "")).strip()
                matched_name = str(data.get("matched_customer_name", "")).strip()
                invoice_no = str(data.get("invoice_no", "")).strip()
                date = str(data.get("date", "")).strip()
                is_count = data.get("is_count", True)
                
                print(f"🔍 Processing invoice {invoice_no}: original='{original_name}', matched='{matched_name}', is_count={is_count}")
                
                # Use original name if matched name is empty or invalid
                final_customer_name = matched_name if matched_name and matched_name != original_name else original_name
                
                # Skip if no valid customer name
                if not final_customer_name or final_customer_name in ["", "Unknown"]:
                    print(f"⚠️ Skipping invoice with invalid customer name: {original_name} -> {matched_name}")
                    continue
                
                # Track matching results
                if data.get("status") == "new_customer_detected":
                    new_customers.append(original_name)
                
                if matched_name and matched_name != original_name and original_name:
                    fuzzy_matches.append({
                        "original": original_name,
                        "matched": matched_name,
                        "confidence": float(data.get("confidence_score", 0.85))
                    })
                
                # Validate numeric fields
                try:
                    weight_kg = int(float(data.get("weight_kg", 0))) if data.get("weight_kg") is not None else 0
                    price_per_unit = float(data.get("price_per_ton", 0)) if data.get("price_per_ton") is not None else 0
                    total_amount = float(data.get("total", data.get("calculated_total", 0))) if data.get("total") or data.get("calculated_total") else 0
                    
                    # FALLBACK: If weight is 0 but we have total and price, calculate weight
                    if weight_kg == 0 and total_amount > 0 and price_per_unit > 0:
                        if is_count:
                            calculated_weight = total_amount / price_per_unit
                        else:
                            calculated_weight = (total_amount * 1000) / price_per_unit
                        
                        weight_kg = int(calculated_weight)
                        print(f"📊 Calculated weight from total: {weight_kg} (total: {total_amount}, price: {price_per_unit}, is_count: {is_count})")
                    
                    # Handle company_amount and worker_amount
                    company_amount = None
                    worker_amount = None
                    
                    if data.get("company_amount") is not None:
                        try:
                            company_amount = float(data.get("company_amount"))
                        except (ValueError, TypeError):
                            company_amount = None
                    
                    if data.get("worker_amount") is not None:
                        try:
                            worker_amount = float(data.get("worker_amount"))
                        except (ValueError, TypeError):
                            worker_amount = None
                            
                except (ValueError, TypeError) as e:
                    print(f"❌ Invalid numeric data in invoice {invoice_no}: {e}")
                    continue
                
                # Create ONLY InvoiceData object (not dict)
                invoice_obj = InvoiceData(
                    date=date,
                    invoice_no=invoice_no,
                    customer_name=final_customer_name,
                    weight_kg=weight_kg,
                    price_per_unit=price_per_unit,
                    total_amount=total_amount,
                    company_amount=company_amount,
                    worker_amount=worker_amount,
                    source_file=str(data.get("source_file", "")),
                    confidence=0.95,
                    is_count=is_count
                )
                
                print(f"✅ Created invoice: {invoice_no} | Customer: {final_customer_name} | Weight: {weight_kg}kg | is_count: {is_count}")
                invoice_objects.append(invoice_obj)
                
            except Exception as e:
                print(f"❌ Error processing invoice data: {e}")
                continue
        
        if not invoice_objects:
            raise HTTPException(status_code=400, detail="No valid invoices could be processed")
        
        print(f"📊 Processing summary: {len(invoice_objects)} valid invoices from {len(processed_data)} total")
        
        # Create Excel report - PASS ONLY InvoiceData objects
        customers = kb_manager.get_all_customers()
        
        excel_path = excel_creator.create_excel_report(
            invoice_objects,  # Only InvoiceData objects, no dicts
            customers, 
            request.output_excel_path
        )
        
        # Create properly structured fuzzy matches
        from src.models.data_models import FuzzyMatch
        structured_fuzzy_matches = [
            FuzzyMatch(
                original=match["original"],
                matched=match["matched"], 
                confidence=match["confidence"]
            ) for match in fuzzy_matches
        ]
        
        # Return the actual file path that was created
        return {
        "success": True,
        "message": "Processing completed successfully",
        "total_processed": len(invoice_objects),
        "successful_extractions": len(invoice_objects),
        "failed_extractions": 0,
        "excel_file_path": excel_path,
        "new_customers_added": new_customers,
        "fuzzy_matches_found": structured_fuzzy_matches
    }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Invoice AI Processor is running"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Invoice AI Processor API", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)