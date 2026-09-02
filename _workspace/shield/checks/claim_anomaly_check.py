"""
Claim Anomaly & Return Arbitrage Defensive Check for Return-Risk Shield.
Detects:
1. False Damage Claims on high-resale electronics/gadgets.
2. Missing parts / empty box return fraud.
3. High-risk refund routing (e.g. demanding untraceable cash/instant transfer on COD orders).
"""
from typing import Dict, Any
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../requirements")))
from contracts import ReturnEvent, DecisionAction, ItemCategory


class ClaimAnomalyCheck:
    def __init__(self, high_value_electronics_threshold: float = 12000.0):
        self.high_value_electronics_threshold = high_value_electronics_threshold

    def evaluate(self, event: ReturnEvent) -> Dict[str, Any]:
        order = event.order_details
        ret = event.return_request
        profile = event.customer_profile
        
        reason_code = ret.return_reason_code
        condition = ret.item_condition_tag or "TAGS_ATTACHED"
        refund_dest = ret.refund_destination
        payment_method = order.payment_method
        returned_items = ret.returned_items
        
        risk_score = 0.0
        reasons = []
        indicators = []
        is_claim_anomaly = False
        
        # 1. False Damage on High-Resale Electronics
        for item in returned_items:
            cat = item.category.upper() if item.category else ""
            is_electronics = (cat in [ItemCategory.ELECTRONICS.value, "ELECTRONICS", "GADGETS"]) or item.is_high_resale
            
            if is_electronics and item.unit_price >= self.high_value_electronics_threshold:
                if reason_code in ["DEFECTIVE_DAMAGED", "ITEM_NOT_AS_DESCRIBED"]:
                    # Claiming brand new flagship electronics was defective out of the box
                    if profile.historical_return_rate >= 0.30 or profile.account_age_days <= 30:
                        risk_score += 65.0
                        is_claim_anomaly = True
                        indicators.append("HIGH_VALUE_ELECTRONICS_DAMAGE_CLAIM")
                        reasons.append(f"High-risk damage claim on sealed electronics ({item.title}, ₹{item.unit_price:,.2f}) by high-return/new profile. Requires serial-number photo verification.")
                    else:
                        risk_score += 35.0
                        is_claim_anomaly = True
                        indicators.append("ELECTRONICS_DAMAGE_REVIEW_REQUIRED")
                        reasons.append(f"Damage claim on flagship electronics ({item.title}, ₹{item.unit_price:,.2f}). Routed for merchant hardware inspection.")

        # 2. Missing Parts / Component Stripping
        if condition in ["MISSING_PARTS", "HEAVILY_WORN"]:
            risk_score += 60.0
            is_claim_anomaly = True
            indicators.append("COMPONENT_OR_PARTS_MISSING")
            reasons.append(f"Return payload tagged with condition '{condition}' — high risk of component stripping/swap fraud.")

        # 3. Cash / COD Refund Extraction
        if payment_method == "COD" and refund_dest in ["INSTANT_CASH", "INSTANT_BANK_TRANSFER"] and ret.requested_refund_amount >= 5000:
            risk_score += 30.0
            indicators.append("COD_INSTANT_CASH_CONVERSION")
            reasons.append("COD purchase requesting instant cash refund conversion prior to physical item return.")

        # Decision synthesis
        if risk_score >= 60.0:
            action = DecisionAction.BLOCK
        elif risk_score >= 30.0:
            action = DecisionAction.FLAG
        else:
            action = DecisionAction.ALLOW
            reasons.append("Claim consistency verified. Standard return procedure authorized.")

        passed = (action == DecisionAction.ALLOW)
        
        return {
            "passed": passed,
            "action": action,
            "confidence": 0.93 if action != DecisionAction.FLAG else 0.86,
            "risk_score": min(100.0, risk_score),
            "is_claim_anomaly": is_claim_anomaly,
            "condition": condition,
            "refund_destination": refund_dest,
            "indicators": indicators,
            "reason": " ".join(reasons)
        }
