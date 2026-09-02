"""
Pydantic Data Contracts for Return-Risk Shield (AI Risk Manager - Track 02).
Classifies merchant order/return events for return-abuse:
- Wardrobing (expensive occasionwear used and returned)
- Bracketing abuse (ordering multiple sizes/colors with intent to return almost all)
- Serial-returner fraud (chronic return velocity, empty boxes, high-value electronics)
- False damage claims (claiming non-returnable / pristine items arrived damaged for cash refund)
- Benign legitimate customer returns
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AbuseClass(str, Enum):
    WARDROBING = "WARDROBING"
    BRACKETING_ABUSE = "BRACKETING_ABUSE"
    SERIAL_RETURNER_FRAUD = "SERIAL_RETURNER_FRAUD"
    FALSE_DAMAGE_CLAIM = "FALSE_DAMAGE_CLAIM"
    BENIGN = "BENIGN"


class DecisionAction(str, Enum):
    ALLOW = "ALLOW"      # Accept return request immediately (auto-authorize refund)
    FLAG = "FLAG"        # Route to merchant fraud/review queue (require physical inspection/photos)
    BLOCK = "BLOCK"      # Reject automated return (enforce restocking fee / non-refundable policy)


class ItemCategory(str, Enum):
    APPAREL_LUXURY = "APPAREL_LUXURY"
    FAST_FASHION = "FAST_FASHION"
    ELECTRONICS = "ELECTRONICS"
    FOOTWEAR = "FOOTWEAR"
    ACCESSORIES = "ACCESSORIES"
    HOME_APPLIANCES = "HOME_APPLIANCES"
    BEAUTY_COSMETICS = "BEAUTY_COSMETICS"


class CustomerProfile(BaseModel):
    customer_id: str
    account_age_days: int
    total_orders_count: int
    total_returns_count: int
    historical_return_rate: float = Field(ge=0.0, le=1.0, description="Returns / Orders ratio")
    past_return_reasons: List[str] = Field(default_factory=list)
    dispute_chargeback_count: int = 0
    ip_country: Optional[str] = "IN"


class OrderItem(BaseModel):
    sku: str
    title: str
    category: str
    unit_price: float
    discount_pct: float = 0.0
    size_variant: Optional[str] = None
    color_variant: Optional[str] = None
    is_high_resale: bool = False


class OrderDetails(BaseModel):
    order_id: str
    order_date: str
    days_since_purchase: int
    total_order_amount: float
    currency: str = "INR"
    payment_method: str = "UPI"  # "COD", "UPI", "CREDIT_CARD", "DEBIT_CARD", "BNPL"
    items: List[OrderItem]


class ReturnRequest(BaseModel):
    return_id: str
    return_reason_code: str  # "DEFECTIVE_DAMAGED", "SIZE_FIT_ISSUE", "WARDROBING_SUSPECTED", "DID_NOT_LIKE", "ITEM_NOT_AS_DESCRIBED", "WRONG_ITEM_SENT"
    return_reason_notes: str
    returned_items: List[OrderItem]
    requested_refund_amount: float
    refund_destination: str = "ORIGINAL_PAYMENT_METHOD"  # "ORIGINAL_PAYMENT_METHOD", "STORE_CREDIT", "INSTANT_CASH"
    item_condition_tag: Optional[str] = "TAGS_ATTACHED"  # "UNOPENED", "TAGS_ATTACHED", "TAGS_REMOVED", "USED_ONCE", "HEAVILY_WORN", "MISSING_PARTS"
    return_pickup_pincode: Optional[str] = None


class GroundTruth(BaseModel):
    target_abuse_class: Optional[AbuseClass] = None
    expected_decision: DecisionAction
    failure_case: bool = False
    rationale: str


class ReturnEvent(BaseModel):
    event_id: str
    is_synthetic: bool = True
    split: str = "dev"  # "dev", "heldout_eval", "demo", "live"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    customer_profile: CustomerProfile
    order_details: OrderDetails
    return_request: ReturnRequest
    ground_truth: Optional[GroundTruth] = None


# Shield Decision & Audit
class ShieldDecision(BaseModel):
    action: DecisionAction
    reason: str
    triggered_checks: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    risk_score: float = Field(ge=0.0, le=100.0, default=0.0)


class AuditEntry(BaseModel):
    audit_id: str
    timestamp: str
    event_id: str
    customer_id: str
    order_id: str
    return_id: str
    decision: DecisionAction
    reason: str
    triggered_checks: List[str]
    check_details: Dict[str, Any]


class ConfusionMatrix(BaseModel):
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0


class ClassMetric(BaseModel):
    precision: float
    recall: float
    false_positive_rate: float
    total_cases: int
    tp: int
    fp: int
    tn: int
    fn: int


class EvaluationMetric(BaseModel):
    precision: float
    recall: float
    false_positive_rate: float
    confusion_matrix: ConfusionMatrix
    by_abuse_class: Dict[str, ClassMetric]
    sample_count: int
    failure_cases_detected: List[str] = Field(default_factory=list)
