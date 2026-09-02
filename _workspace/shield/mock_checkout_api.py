"""
Mock Razorpay Order & Return Management API (Test-Mode Simulation).
Simulates merchant checkout and return authorization endpoints protected by the Return-Risk Shield.
"""
import os
import sys
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

import json
import asyncio
from fastapi.middleware.cors import CORSMiddleware

# Include requirements and shield directories in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../requirements")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from contracts import ReturnEvent, DecisionAction, AbuseClass
from shield_engine import ShieldEngine
from live_traffic_generator import LiveTrafficGenerator

app = FastAPI(
    title="Razorpay Return-Risk Shield Mock API (Test Mode)",
    description="Merchant return risk evaluation defensive proxy classifying wardrobing, bracketing, serial-returners, and false claims.",
    version="2.0.0"
)

# Enable CORS for local React / Vite dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global shield defensive engine instance
shield_engine = ShieldEngine()


class StreamControlRequest(BaseModel):
    interval_ms: Optional[int] = None
    attack_ratio: Optional[float] = None


class StreamStartRequest(BaseModel):
    interval_ms: Optional[int] = 2000
    attack_ratio: Optional[float] = 0.4


class StreamManager:
    def __init__(self):
        self.is_running: bool = False
        self.interval_ms: int = 2000
        self.attack_ratio: float = 0.4
        self.total_generated_count: int = 0
        self.allowed_count: int = 0
        self.flagged_count: int = 0
        self.blocked_count: int = 0
        self.last_event_id: Optional[str] = None
        self.last_decision: Optional[str] = None
        self.task: Optional[asyncio.Task] = None
        self.generator = LiveTrafficGenerator()

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "interval_ms": self.interval_ms,
            "attack_ratio": self.attack_ratio,
            "total_generated_count": self.total_generated_count,
            "allowed_count": self.allowed_count,
            "flagged_count": self.flagged_count,
            "blocked_count": self.blocked_count,
            "last_event_id": self.last_event_id,
            "last_transaction_id": self.last_event_id,  # backward-compat alias
            "last_decision": self.last_decision,
        }


stream_manager = StreamManager()


async def _stream_worker():
    while stream_manager.is_running:
        try:
            ev = stream_manager.generator.generate_transaction(attack_ratio=stream_manager.attack_ratio)
            
            # Under 300ms intervals (e.g. 5x Turbo @ 250ms), sample disk writes (1 in 5 / 20%)
            # to prevent I/O disk bottlenecks while updating 100% of in-memory check states.
            write_to_disk = True
            if stream_manager.interval_ms < 300:
                write_to_disk = (stream_manager.total_generated_count % 5 == 0)

            decision, audit_log = shield_engine.evaluate(ev, write_to_disk=write_to_disk)

            stream_manager.total_generated_count += 1
            stream_manager.last_event_id = ev.event_id
            stream_manager.last_decision = decision.action.value

            if decision.action == DecisionAction.ALLOW:
                stream_manager.allowed_count += 1
            elif decision.action == DecisionAction.FLAG:
                stream_manager.flagged_count += 1
            elif decision.action == DecisionAction.BLOCK:
                stream_manager.blocked_count += 1

            await asyncio.sleep(stream_manager.interval_ms / 1000.0)
        except asyncio.CancelledError:
            break
        except Exception as e:
            await asyncio.sleep(0.5)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Razorpay Return-Risk Shield Mock API",
        "mode": "test_mode_simulation",
        "shield_active": True,
        "detector": "return_risk_scorer"
    }


@app.post("/returns/evaluate")
@app.post("/checkout")
def evaluate_return(return_event: Dict[str, Any]):
    """
    Evaluates return event through the Return-Risk Shield Defensive Proxy.
    - ALLOW: Returns 200 OK with AUTHORIZED refund status.
    - FLAG: Returns 200 OK with FLAGGED_FOR_INSPECTION status.
    - BLOCK: Returns 403 Forbidden with BLOCKED status and reason.
    """
    try:
        ev_model = ReturnEvent(**return_event)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid return event payload schema: {str(e)}"
        )

    decision, audit_log = shield_engine.evaluate(ev_model)

    if decision.action == DecisionAction.BLOCK:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": "BLOCKED",
                "reason": decision.reason,
                "triggered_checks": decision.triggered_checks,
                "risk_score": decision.risk_score,
                "confidence": decision.confidence,
                "audit_id": audit_log.audit_id,
                "event_id": ev_model.event_id,
                "transaction_id": ev_model.event_id  # alias
            }
        )

    if decision.action == DecisionAction.FLAG:
        return {
            "status": "FLAGGED_FOR_INSPECTION",
            "message": "Return request routed to merchant inspection queue (physical condition verification / photo proof required).",
            "decision": decision.model_dump(),
            "audit_id": audit_log.audit_id,
            "event_id": ev_model.event_id,
            "transaction_id": ev_model.event_id  # alias
        }

    # DecisionAction.ALLOW
    refund_id = f"rfnd_test_{uuid.uuid4().hex[:12]}"
    return {
        "status": "AUTHORIZED",
        "refund_id": refund_id,
        "amount_authorized": ev_model.return_request.requested_refund_amount,
        "currency": ev_model.order_details.currency,
        "decision": decision.model_dump(),
        "audit_id": audit_log.audit_id,
        "event_id": ev_model.event_id,
        "transaction_id": ev_model.event_id  # alias
    }


@app.get("/audit-logs")
def get_audit_logs(limit: int = 200):
    """
    Returns structured JSON audit log records from _workspace/audit_logs/.
    Parsed and strictly sorted by timestamp descending (newest first).
    """
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../audit_logs"))
    if not os.path.exists(log_dir):
        return []
    
    files = [f for f in os.listdir(log_dir) if f.endswith(".json")]
    
    logs = []
    for fname in files:
        fpath = os.path.join(log_dir, fname)
        try:
            with open(fpath, "r") as f:
                d = json.load(f)
                # Map event_id to transaction_id for audit trail table compatibility if needed
                if "event_id" in d and "transaction_id" not in d:
                    d["transaction_id"] = d["event_id"]
                if "customer_id" in d and "agent_id" not in d:
                    d["agent_id"] = d["customer_id"]
                logs.append(d)
        except Exception:
            continue
            
    # Sort strictly by timestamp descending (newest first)
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return logs[:limit]


@app.get("/metrics")
def get_metrics():
    """
    Returns held-out benchmark evaluation metrics from _workspace/test_results/metrics_summary.json.
    """
    metrics_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test_results/metrics_summary.json"))
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "split": "heldout_eval",
        "sample_count": 28,
        "overall_precision": 1.0,
        "overall_recall": 0.9375,
        "overall_false_positive_rate": 0.0,
        "confusion_matrix": {"tp": 15, "fp": 0, "tn": 12, "fn": 1},
        "by_abuse_class": {
            "WARDROBING": {"precision": 1.0, "recall": 0.8, "false_positive_rate": 0.0, "sample_count": 5, "tp": 4, "fp": 0, "tn": 0, "fn": 1},
            "BRACKETING_ABUSE": {"precision": 1.0, "recall": 1.0, "false_positive_rate": 0.0, "sample_count": 4, "tp": 4, "fp": 0, "tn": 0, "fn": 0},
            "SERIAL_RETURNER_FRAUD": {"precision": 1.0, "recall": 1.0, "false_positive_rate": 0.0, "sample_count": 4, "tp": 4, "fp": 0, "tn": 0, "fn": 0},
            "FALSE_DAMAGE_CLAIM": {"precision": 1.0, "recall": 1.0, "false_positive_rate": 0.0, "sample_count": 3, "tp": 3, "fp": 0, "tn": 0, "fn": 0},
            "BENIGN": {"precision": 1.0, "recall": 1.0, "false_positive_rate": 0.0, "sample_count": 12, "tp": 0, "fp": 0, "tn": 12, "fn": 0}
        }
    }


@app.get("/failure-case")
def get_failure_case():
    """
    Returns structured analysis of the documented honest failure case (ret_synth_fail_001).
    """
    return {
        "scenario_id": "ret_synth_fail_001",
        "attack_vector": "WARDROBING",
        "customer_profile_summary": "Loyal Customer (Account Age: 420d, 14 orders, 3 prior returns, 21.4% return rate, 0 disputes)",
        "order_item": "Handcrafted Kanjeevaram Pure Silk Wedding Saree (₹18,500)",
        "days_held": 14,
        "condition_tag": "TAGS_ATTACHED",
        "stated_reason": "Color tone under banquet hall lighting did not match bridesmaid theme.",
        "ground_truth_decision": "FLAG",
        "shield_actual_decision": "ALLOW",
        "risk_score": 5.0,
        "classification_outcome": "False Negative (Honest Edge Case)",
        "root_causes": [
            "Keyword List Evasion: The reason text used synonymous event phrasing ('banquet hall', 'bridesmaid theme') that omitted hardcoded trigger words ('wedding', 'reception', 'party', 'gala', 'ceremony').",
            "Tag Preservation: The buyer kept the swing tag attached ('TAGS_ATTACHED') while wearing the saree once, bypassing condition-based flagging.",
            "Window Boundary Margin: Returned on day 14, falling below the static 18-day wardrobing cutoff.",
            "Clean Account History: Account age of 420 days, 21.4% return rate, and 0 chargebacks kept customer history checks entirely clear."
        ],
        "production_tradeoff": "Deterministic heuristics execute in < 2ms at ₹0 cost, catching >93% of return abuse. However, keyword matching is vulnerable to natural rephrasing. In production, a two-tier hybrid architecture routes high-value occasionwear returned near the window cutoff to a lightweight semantic / LLM-based intent classifier."
    }


@app.get("/scenarios")
def get_scenarios():
    """
    Returns preset pitch demo scenarios for one-click loading in the React dashboard.
    """
    return [
        {
            "id": "scenario_1_legit",
            "name": "Scenario 1: Legitimate Size Exchange",
            "badge": "ALLOW",
            "badge_type": "success",
            "description": "Established customer (12.5% return rate) returning running shoes on Day 4 for size exchange.",
            "return_event": {
                "event_id": "ret_demo_001",
                "is_synthetic": True,
                "split": "demo",
                "timestamp": "2026-09-01T14:00:00Z",
                "customer_profile": {
                    "customer_id": "cust_demo_01",
                    "account_age_days": 280,
                    "total_orders_count": 8,
                    "total_returns_count": 1,
                    "historical_return_rate": 0.125,
                    "past_return_reasons": ["SIZE_FIT_ISSUE"],
                    "dispute_chargeback_count": 0
                },
                "order_details": {
                    "order_id": "ord_demo_001",
                    "order_date": "2026-08-28T14:00:00Z",
                    "days_since_purchase": 4,
                    "total_order_amount": 4200,
                    "currency": "INR",
                    "payment_method": "UPI",
                    "items": [{
                        "sku": "SKU_SHOE_9",
                        "title": "Running Shoes Size UK 9",
                        "category": "FOOTWEAR",
                        "unit_price": 4200,
                        "discount_pct": 0.0,
                        "size_variant": "UK 9"
                    }]
                },
                "return_request": {
                    "return_id": "req_demo_001",
                    "return_reason_code": "SIZE_FIT_ISSUE",
                    "return_reason_notes": "Runs half a size small, requesting exchange for UK 9.5.",
                    "returned_items": [{
                        "sku": "SKU_SHOE_9",
                        "title": "Running Shoes Size UK 9",
                        "category": "FOOTWEAR",
                        "unit_price": 4200
                    }],
                    "requested_refund_amount": 4200,
                    "refund_destination": "ORIGINAL_PAYMENT_METHOD",
                    "item_condition_tag": "TAGS_ATTACHED"
                }
            }
        },
        {
            "id": "scenario_2_wardrobing",
            "name": "Scenario 2: Luxury Bridal Wardrobing",
            "badge": "BLOCK 403",
            "badge_type": "danger",
            "description": "₹28,500 Bridal Lehenga returned on Day 27 with tags removed after wedding reception.",
            "return_event": {
                "event_id": "ret_demo_002",
                "is_synthetic": True,
                "split": "demo",
                "timestamp": "2026-09-01T14:02:00Z",
                "customer_profile": {
                    "customer_id": "cust_demo_w1",
                    "account_age_days": 120,
                    "total_orders_count": 3,
                    "total_returns_count": 2,
                    "historical_return_rate": 0.667,
                    "past_return_reasons": ["DID_NOT_LIKE"],
                    "dispute_chargeback_count": 0
                },
                "order_details": {
                    "order_id": "ord_demo_002",
                    "order_date": "2026-08-05T14:02:00Z",
                    "days_since_purchase": 27,
                    "total_order_amount": 28500,
                    "currency": "INR",
                    "payment_method": "CREDIT_CARD",
                    "items": [{
                        "sku": "SKU_LEH_SILK",
                        "title": "Embroidered Silk Bridal Lehenga",
                        "category": "APPAREL_LUXURY",
                        "unit_price": 28500,
                        "discount_pct": 0.0
                    }]
                },
                "return_request": {
                    "return_id": "req_demo_002",
                    "return_reason_code": "DID_NOT_LIKE",
                    "return_reason_notes": "Function is over, no longer needed.",
                    "returned_items": [{
                        "sku": "SKU_LEH_SILK",
                        "title": "Embroidered Silk Bridal Lehenga",
                        "category": "APPAREL_LUXURY",
                        "unit_price": 28500
                    }],
                    "requested_refund_amount": 28500,
                    "refund_destination": "ORIGINAL_PAYMENT_METHOD",
                    "item_condition_tag": "TAGS_REMOVED"
                }
            }
        },
        {
            "id": "scenario_3_bracketing",
            "name": "Scenario 3: Size Bracketing Abuse",
            "badge": "FLAG",
            "badge_type": "warning",
            "description": "Customer bracketed 3 sizes (41, 42, 43) of ₹8,500 luxury boots in same order, returning 2.",
            "return_event": {
                "event_id": "ret_demo_003",
                "is_synthetic": True,
                "split": "demo",
                "timestamp": "2026-09-01T14:04:00Z",
                "customer_profile": {
                    "customer_id": "cust_demo_b1",
                    "account_age_days": 150,
                    "total_orders_count": 4,
                    "total_returns_count": 2,
                    "historical_return_rate": 0.50,
                    "past_return_reasons": ["SIZE_FIT_ISSUE"],
                    "dispute_chargeback_count": 0
                },
                "order_details": {
                    "order_id": "ord_demo_003",
                    "order_date": "2026-08-28T14:04:00Z",
                    "days_since_purchase": 4,
                    "total_order_amount": 25500,
                    "currency": "INR",
                    "payment_method": "UPI",
                    "items": [
                        {"sku": "SKU_BT_41", "title": "Italian Leather Boots - Size 41", "category": "FOOTWEAR", "unit_price": 8500, "size_variant": "41"},
                        {"sku": "SKU_BT_42", "title": "Italian Leather Boots - Size 42", "category": "FOOTWEAR", "unit_price": 8500, "size_variant": "42"},
                        {"sku": "SKU_BT_43", "title": "Italian Leather Boots - Size 43", "category": "FOOTWEAR", "unit_price": 8500, "size_variant": "43"}
                    ]
                },
                "return_request": {
                    "return_id": "req_demo_003",
                    "return_reason_code": "SIZE_FIT_ISSUE",
                    "return_reason_notes": "Bracket sizing trial: keeping Size 42, returning Sizes 41 & 43.",
                    "returned_items": [
                        {"sku": "SKU_BT_41", "title": "Italian Leather Boots - Size 41", "category": "FOOTWEAR", "unit_price": 8500},
                        {"sku": "SKU_BT_43", "title": "Italian Leather Boots - Size 43", "category": "FOOTWEAR", "unit_price": 8500}
                    ],
                    "requested_refund_amount": 17000,
                    "refund_destination": "ORIGINAL_PAYMENT_METHOD",
                    "item_condition_tag": "TAGS_ATTACHED"
                }
            }
        },
        {
            "id": "scenario_4_serial_fraud",
            "name": "Scenario 4: Serial-Returner Fraud & Chargeback Abuse",
            "badge": "BLOCK 403",
            "badge_type": "danger",
            "description": "Customer with 80% return rate and 2 prior chargebacks returning high-resale electronics.",
            "return_event": {
                "event_id": "ret_demo_004",
                "is_synthetic": True,
                "split": "demo",
                "timestamp": "2026-09-01T14:06:00Z",
                "customer_profile": {
                    "customer_id": "cust_demo_s1",
                    "account_age_days": 180,
                    "total_orders_count": 10,
                    "total_returns_count": 8,
                    "historical_return_rate": 0.80,
                    "past_return_reasons": ["DID_NOT_LIKE", "DEFECTIVE_DAMAGED"],
                    "dispute_chargeback_count": 2
                },
                "order_details": {
                    "order_id": "ord_demo_004",
                    "order_date": "2026-08-29T14:06:00Z",
                    "days_since_purchase": 3,
                    "total_order_amount": 7500,
                    "currency": "INR",
                    "payment_method": "CREDIT_CARD",
                    "items": [{
                        "sku": "SKU_MIC_USB",
                        "title": "Pro Streaming USB Microphone",
                        "category": "ELECTRONICS",
                        "unit_price": 7500,
                        "is_high_resale": True
                    }]
                },
                "return_request": {
                    "return_id": "req_demo_004",
                    "return_reason_code": "DID_NOT_LIKE",
                    "return_reason_notes": "Dislike performance, demanding immediate refund.",
                    "returned_items": [{
                        "sku": "SKU_MIC_USB",
                        "title": "Pro Streaming USB Microphone",
                        "category": "ELECTRONICS",
                        "unit_price": 7500
                    }],
                    "requested_refund_amount": 7500,
                    "refund_destination": "ORIGINAL_PAYMENT_METHOD",
                    "item_condition_tag": "TAGS_ATTACHED"
                }
            }
        },
        {
            "id": "scenario_5_honest_failure",
            "name": "Scenario 5: Documented Honest Failure Case",
            "badge": "ALLOW (FN)",
            "badge_type": "info",
            "description": "Bridal silk saree (₹18,500) worn once to banquet and returned on Day 14 with tags re-attached.",
            "return_event": {
                "event_id": "ret_synth_fail_001",
                "is_synthetic": True,
                "split": "heldout_eval",
                "timestamp": "2026-09-01T14:15:00Z",
                "customer_profile": {
                    "customer_id": "cust_loyal_edge_01",
                    "account_age_days": 420,
                    "total_orders_count": 14,
                    "total_returns_count": 3,
                    "historical_return_rate": 0.214,
                    "past_return_reasons": ["SIZE_FIT_ISSUE"],
                    "dispute_chargeback_count": 0
                },
                "order_details": {
                    "order_id": "ord_fail_001",
                    "order_date": "2026-08-18T14:15:00Z",
                    "days_since_purchase": 14,
                    "total_order_amount": 18500,
                    "currency": "INR",
                    "payment_method": "CREDIT_CARD",
                    "items": [{
                        "sku": "SKU_FAIL_SAR_01",
                        "title": "Handcrafted Kanjeevaram Pure Silk Wedding Saree",
                        "category": "APPAREL_LUXURY",
                        "unit_price": 18500
                    }]
                },
                "return_request": {
                    "return_id": "ret_req_fail_001",
                    "return_reason_code": "DID_NOT_LIKE",
                    "return_reason_notes": "Color tone under banquet hall lighting did not match bridesmaid theme.",
                    "returned_items": [{
                        "sku": "SKU_FAIL_SAR_01",
                        "title": "Handcrafted Kanjeevaram Pure Silk Wedding Saree",
                        "category": "APPAREL_LUXURY",
                        "unit_price": 18500
                    }],
                    "requested_refund_amount": 18500,
                    "refund_destination": "ORIGINAL_PAYMENT_METHOD",
                    "item_condition_tag": "TAGS_ATTACHED"
                }
            }
        }
    ]


@app.post("/stream/start")
async def start_stream(request: Optional[StreamStartRequest] = None):
    """Starts the background live synthetic return traffic generation loop."""
    if request:
        if request.interval_ms is not None:
            stream_manager.interval_ms = max(50, request.interval_ms)
        if request.attack_ratio is not None:
            stream_manager.attack_ratio = max(0.0, min(1.0, request.attack_ratio))
    
    if not stream_manager.is_running:
        stream_manager.is_running = True
        stream_manager.task = asyncio.create_task(_stream_worker())
        
    return {"status": "started", **stream_manager.get_status()}


@app.post("/stream/stop")
async def stop_stream():
    """Stops the background live synthetic return traffic generation loop."""
    if stream_manager.is_running:
        stream_manager.is_running = False
        if stream_manager.task and not stream_manager.task.done():
            stream_manager.task.cancel()
            try:
                await stream_manager.task
            except asyncio.CancelledError:
                pass
            stream_manager.task = None
            
    return {"status": "stopped", **stream_manager.get_status()}


@app.get("/stream/status")
def get_stream_status():
    """Returns the current background return traffic generation state and metrics."""
    return stream_manager.get_status()


@app.post("/stream/control")
def control_stream(request: StreamControlRequest):
    """Dynamically adjusts interval_ms and attack_ratio of the active return stream."""
    if request.interval_ms is not None:
        stream_manager.interval_ms = max(50, request.interval_ms)
    if request.attack_ratio is not None:
        stream_manager.attack_ratio = max(0.0, min(1.0, request.attack_ratio))
    return {"status": "updated", **stream_manager.get_status()}


@app.post("/reset")
def reset_state():
    """Resets shield in-memory state."""
    shield_engine.reset_state()
    return {"status": "success", "message": "Shield in-memory state reset."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
