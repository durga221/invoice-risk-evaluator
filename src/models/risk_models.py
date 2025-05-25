from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"

class CompanyInfo(BaseModel):
    name: str
    tax_id: str
    industry: str
    location: str
    registration_date: Optional[datetime] = None
    website: Optional[str] = None
    employee_count: Optional[int] = None

class InvoiceData(BaseModel):
    id: str
    amount: float
    currency: str = "USD"
    due_date: datetime
    buyer_info: CompanyInfo
    seller_info: CompanyInfo
    description: str
    payment_terms: str = "Net 30"
    created_at: datetime = Field(default_factory=datetime.now)

class FinancialMetrics(BaseModel):
    revenue: float
    growth_rate: float
    net_margin: float
    current_ratio: float
    debt_to_equity: float
    cash_reserves: float

class CreditProfile(BaseModel):
    credit_score: int
    rating: str
    financial_metrics: FinancialMetrics
    payment_history_score: float
    on_time_payment_rate: float
    late_payments_count: int
    default_history: List[Dict[str, Any]] = []
    banking_relationships: Dict[str, Any] = {}

class IdentityVerification(BaseModel):
    verified: bool
    kyc_level: str
    trust_score: int
    compliance_score: int
    document_verification: Dict[str, bool]
    wallet_address: Optional[str] = None
    risk_flags: List[str] = []

class MarketIntelligence(BaseModel):
    industry_growth_rate: float
    market_volatility: str
    economic_outlook: str
    sector_health: str
    geographic_risk_score: int
    supply_chain_status: str

class RiskFactor(BaseModel):
    name: str
    score: float
    weight: float
    impact: str
    description: str

class RiskAssessment(BaseModel):
    invoice_id: str
    overall_score: int
    risk_level: RiskLevel
    confidence: float
    recommendation: str
    factors: List[RiskFactor]
    ai_reasoning: str
    suggested_terms: Dict[str, Any]
    blockchain_record: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
