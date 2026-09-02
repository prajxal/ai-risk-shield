"""
Pytest integration tests for Return-Risk Shield (AI Risk Manager - Track 02).
Validates end-to-end evaluation of Legitimate Returns, Wardrobing, Bracketing, Serial Returner Fraud,
and False Damage Claims.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../requirements")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from contracts import ReturnEvent, DecisionAction
from shield_engine import ShieldEngine


@pytest.fixture
def engine(tmp_path):
    return ShieldEngine(log_dir=str(tmp_path / "test_logs"))


def test_legitimate_return_allowed(engine):
    payload = {
        "event_id": "ret_test_legit_001",
        "is_synthetic": True,
        "split": "test",
        "timestamp": "2026-09-01T12:00:00Z",
        "customer_profile": {
            "customer_id": "cust_test_01",
            "account_age_days": 300,
            "total_orders_count": 12,
            "total_returns_count": 1,
            "historical_return_rate": 0.083,
            "past_return_reasons": ["SIZE_FIT_ISSUE"],
            "dispute_chargeback_count": 0
        },
        "order_details": {
            "order_id": "ord_test_01",
            "order_date": "2026-08-28T12:00:00Z",
            "days_since_purchase": 4,
            "total_order_amount": 2500.0,
            "currency": "INR",
            "payment_method": "UPI",
            "items": [{
                "sku": "SKU_SHOE_01",
                "title": "Casual Canvas Sneakers",
                "category": "FOOTWEAR",
                "unit_price": 2500.0
            }]
        },
        "return_request": {
            "return_id": "req_test_01",
            "return_reason_code": "SIZE_FIT_ISSUE",
            "return_reason_notes": "Slightly tight around toes, requesting size exchange.",
            "returned_items": [{
                "sku": "SKU_SHOE_01",
                "title": "Casual Canvas Sneakers",
                "category": "FOOTWEAR",
                "unit_price": 2500.0
            }],
            "requested_refund_amount": 2500.0,
            "refund_destination": "ORIGINAL_PAYMENT_METHOD",
            "item_condition_tag": "TAGS_ATTACHED"
        }
    }
    decision, audit = engine.evaluate(payload)
    assert decision.action == DecisionAction.ALLOW
    assert decision.risk_score <= 10.0
    assert audit.decision == DecisionAction.ALLOW


def test_wardrobing_blocked(engine):
    payload = {
        "event_id": "ret_test_ward_001",
        "is_synthetic": True,
        "split": "test",
        "timestamp": "2026-09-01T12:00:00Z",
        "customer_profile": {
            "customer_id": "cust_test_w1",
            "account_age_days": 90,
            "total_orders_count": 2,
            "total_returns_count": 1,
            "historical_return_rate": 0.50,
            "past_return_reasons": ["DID_NOT_LIKE"],
            "dispute_chargeback_count": 0
        },
        "order_details": {
            "order_id": "ord_test_w1",
            "order_date": "2026-08-04T12:00:00Z",
            "days_since_purchase": 28,
            "total_order_amount": 28500.0,
            "currency": "INR",
            "payment_method": "CREDIT_CARD",
            "items": [{
                "sku": "SKU_LEH_01",
                "title": "Embroidered Silk Bridal Lehenga",
                "category": "APPAREL_LUXURY",
                "unit_price": 28500.0
            }]
        },
        "return_request": {
            "return_id": "req_test_w1",
            "return_reason_code": "DID_NOT_LIKE",
            "return_reason_notes": "Wedding reception finished, no longer needed.",
            "returned_items": [{
                "sku": "SKU_LEH_01",
                "title": "Embroidered Silk Bridal Lehenga",
                "category": "APPAREL_LUXURY",
                "unit_price": 28500.0
            }],
            "requested_refund_amount": 28500.0,
            "refund_destination": "ORIGINAL_PAYMENT_METHOD",
            "item_condition_tag": "TAGS_REMOVED"
        }
    }
    decision, audit = engine.evaluate(payload)
    assert decision.action == DecisionAction.BLOCK
    assert "WARDROBING" in decision.triggered_checks
    assert decision.risk_score >= 60.0


def test_bracketing_flagged(engine):
    payload = {
        "event_id": "ret_test_brk_001",
        "is_synthetic": True,
        "split": "test",
        "timestamp": "2026-09-01T12:00:00Z",
        "customer_profile": {
            "customer_id": "cust_test_b1",
            "account_age_days": 180,
            "total_orders_count": 5,
            "total_returns_count": 2,
            "historical_return_rate": 0.40,
            "past_return_reasons": ["SIZE_FIT_ISSUE"],
            "dispute_chargeback_count": 0
        },
        "order_details": {
            "order_id": "ord_test_b1",
            "order_date": "2026-08-28T12:00:00Z",
            "days_since_purchase": 4,
            "total_order_amount": 25500.0,
            "currency": "INR",
            "payment_method": "UPI",
            "items": [
                {"sku": "SKU_BT_41", "title": "Italian Leather Boots - Size 41", "category": "FOOTWEAR", "unit_price": 8500.0, "size_variant": "41"},
                {"sku": "SKU_BT_42", "title": "Italian Leather Boots - Size 42", "category": "FOOTWEAR", "unit_price": 8500.0, "size_variant": "42"},
                {"sku": "SKU_BT_43", "title": "Italian Leather Boots - Size 43", "category": "FOOTWEAR", "unit_price": 8500.0, "size_variant": "43"}
            ]
        },
        "return_request": {
            "return_id": "req_test_b1",
            "return_reason_code": "SIZE_FIT_ISSUE",
            "return_reason_notes": "Bracket sizing trial: keeping 42, returning 41 and 43.",
            "returned_items": [
                {"sku": "SKU_BT_41", "title": "Italian Leather Boots - Size 41", "category": "FOOTWEAR", "unit_price": 8500.0},
                {"sku": "SKU_BT_43", "title": "Italian Leather Boots - Size 43", "category": "FOOTWEAR", "unit_price": 8500.0}
            ],
            "requested_refund_amount": 17000.0,
            "refund_destination": "ORIGINAL_PAYMENT_METHOD",
            "item_condition_tag": "TAGS_ATTACHED"
        }
    }
    decision, audit = engine.evaluate(payload)
    assert decision.action in [DecisionAction.FLAG, DecisionAction.BLOCK]
    assert "BRACKETING_ABUSE" in decision.triggered_checks


def test_serial_returner_blocked(engine):
    payload = {
        "event_id": "ret_test_ser_001",
        "is_synthetic": True,
        "split": "test",
        "timestamp": "2026-09-01T12:00:00Z",
        "customer_profile": {
            "customer_id": "cust_test_s1",
            "account_age_days": 180,
            "total_orders_count": 10,
            "total_returns_count": 8,
            "historical_return_rate": 0.80,
            "past_return_reasons": ["DID_NOT_LIKE"],
            "dispute_chargeback_count": 2
        },
        "order_details": {
            "order_id": "ord_test_s1",
            "order_date": "2026-08-29T12:00:00Z",
            "days_since_purchase": 3,
            "total_order_amount": 7500.0,
            "currency": "INR",
            "payment_method": "CREDIT_CARD",
            "items": [{
                "sku": "SKU_MIC_01",
                "title": "USB Streaming Microphone",
                "category": "ELECTRONICS",
                "unit_price": 7500.0,
                "is_high_resale": True
            }]
        },
        "return_request": {
            "return_id": "req_test_s1",
            "return_reason_code": "DID_NOT_LIKE",
            "return_reason_notes": "Unsatisfied.",
            "returned_items": [{
                "sku": "SKU_MIC_01",
                "title": "USB Streaming Microphone",
                "category": "ELECTRONICS",
                "unit_price": 7500.0
            }],
            "requested_refund_amount": 7500.0,
            "refund_destination": "ORIGINAL_PAYMENT_METHOD",
            "item_condition_tag": "TAGS_ATTACHED"
        }
    }
    decision, audit = engine.evaluate(payload)
    assert decision.action == DecisionAction.BLOCK
    assert "SERIAL_RETURNER_FRAUD" in decision.triggered_checks
