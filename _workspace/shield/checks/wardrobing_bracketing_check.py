"""
Wardrobing & Bracketing Abuse Defensive Check for Return-Risk Shield.
Detects:
1. Wardrobing: Occasionwear/luxury apparel used for events and returned near return deadline with tags altered or removed.
2. Bracketing Abuse: Ordering multiple sizes/colors of identical items with systemic return of the bracket.
"""
from typing import Dict, Any, List
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../requirements")))
from contracts import ReturnEvent, DecisionAction, ItemCategory


class WardrobingBracketingCheck:
    def __init__(self, wardrobing_days_threshold: int = 18, high_value_apparel_price: float = 6000.0):
        self.wardrobing_days_threshold = wardrobing_days_threshold
        self.high_value_apparel_price = high_value_apparel_price

    def evaluate(self, event: ReturnEvent) -> Dict[str, Any]:
        order = event.order_details
        ret = event.return_request
        
        days_held = order.days_since_purchase
        condition = ret.item_condition_tag or "TAGS_ATTACHED"
        reason_code = ret.return_reason_code
        notes = (ret.return_reason_notes or "").lower()
        returned_items = ret.returned_items
        order_items = order.items
        
        risk_score = 0.0
        reasons = []
        indicators = []
        is_bracketing = False
        is_wardrobing = False
        
        # -------------------------------------------------------------
        # 1. Wardrobing Detection
        # -------------------------------------------------------------
        for item in returned_items:
            cat = item.category.upper() if item.category else ""
            is_apparel_or_luxury = cat in [
                ItemCategory.APPAREL_LUXURY.value,
                ItemCategory.FAST_FASHION.value,
                ItemCategory.ACCESSORIES.value,
                "APPAREL",
                "LUXURY",
                "FASHION"
            ]
            
            if is_apparel_or_luxury and item.unit_price >= self.high_value_apparel_price:
                # Late return near expiration + tags altered/used
                if days_held >= self.wardrobing_days_threshold:
                    if condition in ["TAGS_REMOVED", "USED_ONCE", "HEAVILY_WORN"]:
                        risk_score += 70.0
                        is_wardrobing = True
                        indicators.append("WARDROBING_TAGS_REMOVED_LATE")
                        reasons.append(f"High-confidence Wardrobing: High-value fashion item ({item.title}, ₹{item.unit_price:,.2f}) returned at {days_held} days with condition '{condition}'.")
                    elif any(kw in notes for kw in ["wedding", "party", "shoot", "event", "occasion", "ceremony", "function"]):
                        risk_score += 55.0
                        is_wardrobing = True
                        indicators.append("WARDROBING_EVENT_KEYWORD_LATE")
                        reasons.append(f"Wardrobing event keyword match: '{item.title}' returned after {days_held} days following single-use event.")
                    elif days_held >= 25:
                        risk_score += 35.0
                        is_wardrobing = True
                        indicators.append("BORDERLINE_LATE_FASHION_RETURN")
                        reasons.append(f"Elevated wardrobing risk: High-ticket garment returned on day {days_held} right at return policy ceiling.")

        # -------------------------------------------------------------
        # 2. Bracketing Abuse Detection (Multi-size / Multi-color Clustering)
        # -------------------------------------------------------------
        if len(order_items) >= 2:
            # Group order items by base title or root SKU
            base_groups: Dict[str, List[Any]] = {}
            for oi in order_items:
                # Normalize title without size/color (e.g., "Slim Fit Linen Shirt - Size M" -> "slim fit linen shirt")
                norm_title = oi.title.lower().split(" - ")[0].strip()
                base_groups.setdefault(norm_title, []).append(oi)
                
            for base_title, items_group in base_groups.items():
                if len(items_group) >= 2:
                    sizes = {i.size_variant for i in items_group if i.size_variant}
                    colors = {i.color_variant for i in items_group if i.color_variant}
                    
                    if len(sizes) >= 2 or len(colors) >= 2:
                        # Customer bracketed multiple variants in the same order
                        # Check how many of these are being returned
                        group_skus = {i.sku for i in items_group}
                        ret_group_items = [ri for ri in returned_items if ri.sku in group_skus]
                        
                        if len(ret_group_items) >= 1:
                            is_bracketing = True
                            bracket_risk = 35.0 if len(ret_group_items) == 1 else 50.0
                            risk_score += bracket_risk
                            indicators.append("BRACKETING_PATTERN_DETECTED")
                            reasons.append(f"Size/Color bracketing pattern detected on '{base_title}' (ordered {len(items_group)} variants, returning {len(ret_group_items)}).")

        # Decision synthesis
        if risk_score >= 60.0:
            action = DecisionAction.BLOCK
        elif risk_score >= 30.0:
            action = DecisionAction.FLAG
        else:
            action = DecisionAction.ALLOW
            reasons.append(f"No wardrobing or bracketing patterns detected ({days_held}d holding time, condition: {condition}).")

        passed = (action == DecisionAction.ALLOW)
        
        return {
            "passed": passed,
            "action": action,
            "confidence": 0.94 if action != DecisionAction.FLAG else 0.88,
            "risk_score": min(100.0, risk_score),
            "is_wardrobing": is_wardrobing,
            "is_bracketing": is_bracketing,
            "days_held": days_held,
            "days_since_purchase": days_held,
            "condition": condition,
            "indicators": indicators,
            "reason": " ".join(reasons)
        }
