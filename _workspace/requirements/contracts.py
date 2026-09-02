"""
Frozen Pydantic Data Contracts for Agentic Commerce AI Risk Shield.
Adheres strictly to _workspace/requirements/contracts.json.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AttackClass(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    INTENT_MISMATCH = "INTENT_MISMATCH"
    PRICE_QUANTITY_ESCALATION = "PRICE_QUANTITY_ESCALATION"
    VELOCITY_ABUSE = "VELOCITY_ABUSE"
    BENIGN = "BENIGN"


class DecisionAction(str, Enum):
    ALLOW = "ALLOW"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class AgentMetadata(BaseModel):
    agent_id: str
    session_id: str
    ip_address: Optional[str] = "127.0.0.1"
    retry_count: int = 0


class UserStatedIntent(BaseModel):
    requested_items: str
    max_budget: float
    currency: str = "INR"
    constraints: Optional[str] = None
    quantity: int = 1


class CartItem(BaseModel):
    sku: str
    title: str
    quantity: int
    unit_price: float
    item_description: str = ""


class CheckoutPayload(BaseModel):
    cart_items: List[CartItem]
    total_amount: float
    currency: str = "INR"
    shipping_address: Optional[str] = None


class GroundTruth(BaseModel):
    target_attack_class: Optional[AttackClass] = None
    expected_decision: DecisionAction
    failure_case: bool = False
    rationale: str


class Transaction(BaseModel):
    transaction_id: str
    is_synthetic: bool = True
    split: str = "dev"  # "dev", "heldout_eval", "demo"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    agent_metadata: AgentMetadata
    user_stated_intent: UserStatedIntent
    checkout_payload: CheckoutPayload
    ground_truth: Optional[GroundTruth] = None


class ShieldDecision(BaseModel):
    action: DecisionAction
    reason: str
    triggered_checks: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    risk_score: float = Field(ge=0.0, le=100.0, default=0.0)


class AuditEntry(BaseModel):
    audit_id: str
    timestamp: str
    transaction_id: str
    agent_id: str
    session_id: str
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
    by_attack_class: Dict[str, ClassMetric]
    sample_count: int
    failure_cases_detected: List[str] = Field(default_factory=list)
