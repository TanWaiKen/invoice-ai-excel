from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum

class FormulaType(str, Enum):
    WEIGHT_PRICE = "Weight x Price per ton/1000kg"
    ADDITIONAL = "Additional"
    BAJA = "Baja"
    JCB = "JCB"
    LAIN_LAIN = "Lain Lain"
    BAYARAN_GREDIR = "Lain Lain (Bayaran Gredir)"
    MEMBAJA = "Membaja"
    MEMOTONG_PELEPAH = "Memotong pelepah sawit"
    MEMOTONG_PELEPAH_T = "Memotong pelepah sawit (T)"
    MERACUN = "Meracun"
    PAY_TO_GREDER = "Pay to Greder"
    PENGANGKUTAN_LORI = "Pengangkutan Lori"
    UPAH = "Upah"

# Only 4 Essential Data Models
class Customer(BaseModel):
    """Customer data model"""
    name: str
    price_per_ton: float  
    formula: str = "WEIGHT_PRICE"
    company_amount: Optional[float] = None  
    worker_amount: Optional[float] = None   
    confidence_score: Optional[float] = None
    original_customer_name: Optional[str] = None

    # Add computed properties for backward compatibility
    @property
    def price_per_unit(self) -> float:
        return self.price_per_ton
    
    @property 
    def company_price(self) -> Optional[float]:
        return self.company_amount
    
    @property
    def worker_price(self) -> Optional[float]:
        return self.worker_amount

class ProcessingRequest(BaseModel):
    """API request model"""
    image_folder: str
    excel_template_path: str
    output_excel_path: str

class FuzzyMatch(BaseModel):
    original: str
    matched: str
    confidence: float  # This should be float, not string

class ProcessingResult(BaseModel):
    """API response model"""
    success: bool
    total_processed: int
    successful_extractions: int
    failed_extractions: int
    excel_file_path: str
    new_customers_added: List[str] = []
    fuzzy_matches_found: List[FuzzyMatch] = []  # Use the proper model
    message: str = ""

class InvoiceData(BaseModel):
    """Simplified Invoice processing result"""
    date: str
    invoice_no: str
    customer_name: str
    weight_kg: int
    price_per_unit: float
    total_amount: float
    company_amount: Optional[float] = None
    worker_amount: Optional[float] = None
    source_file: str = ""
    confidence: float = 1.0
    is_count: bool = True