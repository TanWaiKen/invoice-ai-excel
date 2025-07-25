import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import only the 4 essential data models
from .data_models import InvoiceData, Customer, FormulaType

class GeminiOCRClient:
    """Gemini client for extracting structured JSON from invoices"""
    
    def __init__(self):
        self.setup_gemini()
    
    def setup_gemini(self):
        """Setup Gemini AI client"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Gemini OCR client initialized")
        except Exception as e:
            print(f"❌ Gemini OCR setup failed: {e}")
            self.model = None

    def extract_json_from_image(self, image_path: str) -> Optional[List[Dict]]:
        """Extract structured JSON data from invoice image - ALWAYS returns list"""
        if not self.model:
            raise Exception("Gemini AI not available")

        try:
            image = Image.open(image_path)
            
            prompt = """
            Extract data from this GYO TRANSPORT & SERVICES invoice image.
            
            **IMPORTANT: If multiple invoices/records in image, return as JSON array []. If single record, still wrap in array.**

            **CRITICAL EXTRACTION RULES:**

            1. **SERVICE TYPE IDENTIFICATION:**
            
            **WEIGHT-BASED SERVICES (is_count: false):**
            - Memetik Tandan Sawit: Extract KG weight and price per ton → Formula: (weight × price) ÷ 1000
            - Pengangkutan/Sewa Lori: Extract KG weight and price per ton → Formula: (weight × price) ÷ 1000
            
            **COUNT-BASED SERVICES (is_count: true):**
            - Memotong Pelepah Sawit: Extract pohon count and price per pohon → Formula: count × price
            - Meracun: Extract kebun count and price per kebun → Formula: count × price  
            - Membaja: Extract bungkus count and price per bungkus → Formula: count × price
            - **Lain-lain: SPECIAL CASE - Always count=1, extract only price per unit**

            2. **LAIN-LAIN SPECIAL HANDLING:**
            For Lain-lain service:
            - weight_kg: Always set to 1 (count is always 1)
            - price_per_ton: Extract the price value shown (e.g., if you see "10", this is the price per unit)
            - total: Should equal price_per_ton × 1 = price_per_ton

            **EXAMPLES:**

            **Single record (still wrap in array):**
            ```json
            [{
                "date": "14/12/2023",
                "invoice_no": "5354", 
                "customer_name": "En Sebin",
                "service_type": "Memetik Tandan Sawit",
                "is_count": false,
                "weight_kg": 4270,
                "price_per_ton": 103,
                "total": 439.81
            }]
            ```
            
            **Multiple records:**
            ```json
            [{
                "date": "14/12/2023",
                "invoice_no": "5351",
                "customer_name": "En MDAJI", 
                "service_type": "Memetik Tandan Sawit",
                "is_count": false,
                "weight_kg": 3580,
                "price_per_ton": 93,
                "total": 333.34
            }, {
                "date": "14/12/2023",
                "invoice_no": "5351",
                "customer_name": "En MDAJI", 
                "service_type": "Lain-lain",
                "is_count": true,
                "weight_kg": 1,
                "price_per_ton": 10,
                "total": 10
            }]
            ```

            Extract all data now and return as JSON array:
            """
        
            response = self.model.generate_content([prompt, image])
            response_content = response.text.strip()

            # Extract JSON from response
            if '```json' in response_content:
                json_start = response_content.find('```json') + 7
                json_end = response_content.find('```', json_start)
                json_str = response_content[json_start:json_end].strip()
            else:
                json_start = response_content.find('[')
                if json_start == -1:
                    json_start = response_content.find('{')
                json_end = response_content.rfind(']') + 1
                if json_end == 0:
                    json_end = response_content.rfind('}') + 1
                json_str = response_content[json_start:json_end]

            if json_str:
                parsed_data = json.loads(json_str)
                
                # Ensure we always return a list
                if isinstance(parsed_data, dict):
                    parsed_data = [parsed_data]
                
                # Process each record
                for record in parsed_data:
                    # Add fallback is_count detection if missing
                    if 'is_count' not in record:
                        record['is_count'] = self._determine_is_count(record.get('service_type', ''))
                    
                    # Special handling for Lain-lain
                    if 'lain' in record.get('service_type', '').lower():
                        if record.get('weight_kg', 0) != 1:
                            extracted_price = record.get('weight_kg', 10)
                            record['weight_kg'] = 1
                            if record.get('price_per_ton', 0) == 0:
                                record['price_per_ton'] = extracted_price
                            record['total'] = record['price_per_ton']
                
                return parsed_data

            return []
        
        except Exception as e:
            print(f"❌ Gemini JSON extraction failed: {e}")
            return []

    def _determine_is_count(self, service_type: str) -> bool:
        """Determine if service is count-based or weight-based"""
        service_lower = service_type.lower() if service_type else ""
        
        # Weight-based services (use /1000)
        weight_based_keywords = ["memetik", "tandan", "sawit", "pengangkutan", "sewa", "lori"]
        
        # If any weight-based keyword is found, it's not count-based
        if any(keyword in service_lower for keyword in weight_based_keywords):
            return False
        
        # Everything else is count-based
        return True

class InvoiceProcessorClient:
    """Main client for processing invoices with enhanced accuracy"""
    
    def __init__(self, knowledge_base_manager=None):
        self.ocr_client = GeminiOCRClient()
        self.kb_manager = knowledge_base_manager
        
        # Setup Gemini model for AI matching
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            else:
                self.model = None
        except:
            self.model = None
    
    def process_images_folder(self, folder_path: str) -> List[Dict]:
        """Process all images in folder with enhanced validation"""
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Get image files
        image_files = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                image_path = os.path.join(folder_path, filename).replace('\\', '/')
                image_files.append(image_path)
        
        if not image_files:
            raise ValueError("No image files found")
        
        print(f"🔍 Found {len(image_files)} images to process")
        
        all_processed_records = []
        
        for image_path in image_files:
            try:
                # Process single image (returns list of records)
                image_records = self.process_single_image(image_path)
                
                if image_records:
                    all_processed_records.extend(image_records)
                        
            except Exception as e:
                print(f"❌ Error processing {image_path}: {e}")
                continue
        
        print(f"🎯 Total records processed: {len(all_processed_records)} from {len(image_files)} images")
        return all_processed_records

    def process_single_image(self, image_path: str) -> List[Dict]:
        """Process a single invoice image - returns list of processed records"""
        try:
            print(f"\n🖼️ Processing: {os.path.basename(image_path)}")
            
            # Extract JSON data (always returns list)
            extracted_records = self.ocr_client.extract_json_from_image(image_path)
            
            # DEBUG: Check what OCR actually returns
            print(f"🔍 DEBUG - OCR returned type: {type(extracted_records)}")
            print(f"🔍 DEBUG - OCR returned data: {extracted_records}")
            
            if not extracted_records:
                print("❌ No data extracted from image")
                return []

            # Ensure it's a list
            if not isinstance(extracted_records, list):
                print(f"⚠️ Converting {type(extracted_records)} to list")
                extracted_records = [extracted_records] if extracted_records else []

            print(f"📋 Found {len(extracted_records)} record(s) in image")

            processed_records = []
            
            # Process each record separately
            for i, record in enumerate(extracted_records, 1):
                try:
                    print(f"\n📄 Processing record {i}/{len(extracted_records)}")
                    
                    # DEBUG: Check record type
                    print(f"🔍 DEBUG - Record type: {type(record)}")
                    print(f"🔍 DEBUG - Record data: {record}")
                    
                    # Ensure record is a dictionary
                    if not isinstance(record, dict):
                        print(f"❌ Record {i} is not a dict: {type(record)}")
                        continue
                    
                    # Get customer name and price with validation
                    customer_name = record.get("customer_name", "").strip()
                    price_per_ton = float(record.get("price_per_ton", 0)) if record.get("price_per_ton") else 0
                    
                    if not customer_name:
                        print(f"⚠️ Record {i}: No customer name found, skipping")
                        continue

                    print(f"📋 Record {i}: {customer_name} | Price: RM{price_per_ton}")

                    # Enhanced matching with exact price validation
                    match_result = self.find_best_customer_match(customer_name, price_per_ton)
                    
                    # Merge results
                    final_result = {**record, **match_result}
                    final_result["source_file"] = os.path.basename(image_path)
                    final_result["record_index"] = i
                    
                    # Enhanced logging
                    if match_result.get("status") == "match_found":
                        matched_name = match_result.get("matched_customer_name", "")
                        price_match = match_result.get("price_match", False)
                        customer_price = match_result.get("customer_price", 0)
                        confidence = match_result.get("confidence_score", 0)
                        
                        price_status = "✅ EXACT PRICE" if price_match else "❌ NAME ONLY"
                        print(f"🎯 Record {i}: {customer_name} → {matched_name}")
                        print(f"💰 {price_status} | Extracted: RM{price_per_ton} | Customer: RM{customer_price}")
                        print(f"📊 Confidence: {confidence:.3f}")
                    else:
                        print(f"🆕 Record {i}: New customer detected: {customer_name}")

                    processed_records.append(final_result)
                    
                except Exception as e:
                    print(f"❌ Error processing record {i}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            print(f"✅ Successfully processed {len(processed_records)}/{len(extracted_records)} records from image")
            return processed_records

        except Exception as e:
            print(f"❌ Error processing {image_path}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def find_best_customer_match(self, extracted_name: str, extracted_price: float = None) -> Dict:
        """Enhanced customer matching with exact price priority"""
        if not extracted_name:
            return {"status": "no_name_provided", "confidence": 0.0}

        print(f"🔍 MATCHING: {extracted_name} | Price: RM{extracted_price}")

        # Step 1: Vector search for name similarity
        vector_results = self.kb_manager.search_similar_customers(extracted_name, top_k=10)
        
        if not vector_results:
            print("❌ No similar names found in vector search")
            return {"status": "new_customer_detected", "confidence": 0.0}
        
        print(f"📊 Found {len(vector_results)} similar names")
        
        # Step 2: Separate exact price matches from name-only matches
        exact_price_matches = []
        name_only_matches = []
        
        for match in vector_results:
            customer_name = match.get('customer_name', '')
            similarity_score = match.get('confidence_score', 0.0)
            customer_price = match.get('price_per_ton', 0.0)
            
            print(f"   📝 {customer_name} | Similarity: {similarity_score:.3f} | Price: RM{customer_price}")
            
            # Check for EXACT price match
            exact_price_match = False
            if extracted_price and extracted_price > 0 and customer_price > 0:
                if abs(extracted_price - customer_price) < 0.01:
                    exact_price_match = True
                    print(f"   ✅ EXACT PRICE MATCH: {customer_name}")
                else:
                    print(f"   ❌ Price mismatch: Expected RM{extracted_price} | Found RM{customer_price}")
            
            candidate = {
                'customer_name': customer_name,
                'similarity_score': similarity_score,
                'customer_price': customer_price,
                'extracted_price': extracted_price,
                'exact_price_match': exact_price_match
            }
            
            if exact_price_match:
                candidate['combined_confidence'] = similarity_score * 0.95
                exact_price_matches.append(candidate)
            else:
                candidate['combined_confidence'] = similarity_score * 0.7
                name_only_matches.append(candidate)
    
        # Step 3: Prioritize exact price matches
        all_candidates = []
    
        if exact_price_matches:
            exact_price_matches.sort(key=lambda x: x['combined_confidence'], reverse=True)
            all_candidates.extend(exact_price_matches)
            print(f"🎯 Found {len(exact_price_matches)} exact price matches")
    
        if name_only_matches:
            name_only_matches.sort(key=lambda x: x['combined_confidence'], reverse=True)
            good_name_matches = [c for c in name_only_matches if c['combined_confidence'] > 0.6]
            all_candidates.extend(good_name_matches)
            print(f"📝 Found {len(good_name_matches)} good name-only matches")
    
        if not all_candidates:
            print("🚫 No suitable candidates found")
            return {"status": "new_customer_detected", "confidence": 0.0}
    
        # Step 4: AI decision with price context
        top_candidates = all_candidates[:3]
        ai_choice = self._ai_choose_best_match_with_price(extracted_name, top_candidates, extracted_price)
    
        if ai_choice:
            chosen_candidate = next((c for c in top_candidates if c['customer_name'] == ai_choice), None)
            if chosen_candidate and chosen_candidate['combined_confidence'] >= 0.5:
                return {
                    "status": "match_found",
                    "matched_customer_name": ai_choice,
                    "confidence_score": chosen_candidate['combined_confidence'],
                    "original_name": extracted_name,
                    "price_match": chosen_candidate['exact_price_match'],
                    "extracted_price": extracted_price,
                    "customer_price": chosen_candidate['customer_price']
                }
            else:
                print(f"🚫 Match rejected: confidence {chosen_candidate['combined_confidence']:.3f} < 0.5")
    
        return {"status": "new_customer_detected", "confidence": 0.0}

    def _ai_choose_best_match_with_price(self, original_name: str, candidates: List[Dict], extracted_price: float = None) -> Optional[str]:
        """AI matching with full price context for each candidate"""
        if not self.model or not candidates:
            # Fallback: prioritize exact price matches, then highest confidence
            exact_matches = [c for c in candidates if c.get('exact_price_match', False)]
            if exact_matches:
                return exact_matches[0]['customer_name']
            return candidates[0]['customer_name'] if candidates else None

        try:
            price_info = f" with extracted price RM{extracted_price}" if extracted_price else ""
            
            # Build detailed candidates list with price info
            candidates_list = []
            
            for i, c in enumerate(candidates, 1):
                price_match_status = "✅ EXACT PRICE" if c.get('exact_price_match', False) else "❌ PRICE MISMATCH"
                candidates_list.append(
                    f"{i}. {c['customer_name']} | Name similarity: {c['similarity_score']:.2f} | "
                    f"{price_match_status}: RM{c['customer_price']} | Combined confidence: {c['combined_confidence']:.2f}"
                )
            
            prompt = f"""
            CUSTOMER MATCHING WITH PRICE VALIDATION
            
            Query: "{original_name}"{price_info}
            
            Candidates:
            {chr(10).join(candidates_list)}
            
            MATCHING RULES:
            1. **EXACT PRICE MATCH = HIGHEST PRIORITY**: Choose candidates with ✅ EXACT PRICE if available
            2. **Price validation**: Price must match exactly (RM{extracted_price} = RM{extracted_price})
            3. **Name-only fallback**: Only if NO exact price match exists AND name similarity > 0.7
            4. **Reject poor matches**: If no good candidate, return "NONE"
            
            DECISION LOGIC:
            - If exact price matches exist → Choose the one with highest name similarity
            - If no exact price match → Choose name-only match ONLY if similarity > 0.7
            - If all matches are poor → Return "NONE"
            
            Return ONLY the exact customer name from candidates, or "NONE".
            """

            response = self.model.generate_content(prompt)
            ai_response = response.text.strip()
            
            print(f"🤖 AI decision: {ai_response}")
            
            # Validate AI response
            if ai_response.upper() == "NONE":
                return None
                
            # Check if AI chose a valid candidate
            for candidate in candidates:
                if candidate['customer_name'].lower() in ai_response.lower():
                    return candidate['customer_name']
            
            # Fallback: prefer exact price matches
            exact_matches = [c for c in candidates if c.get('exact_price_match', False)]
            if exact_matches:
                return exact_matches[0]['customer_name']
            
            return None
            
        except Exception as e:
            print(f"❌ AI matching error: {e}")
            # Fallback with price validation
            exact_matches = [c for c in candidates if c.get('exact_price_match', False)]
            if exact_matches:
                return exact_matches[0]['customer_name']
            return candidates[0]['customer_name'] if candidates else None