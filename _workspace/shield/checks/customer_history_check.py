"""
Customer Return History & Velocity Defensive Check for Return-Risk Shield.
Evaluates account age, historical return rate, dispute/chargeback frequency, and serial return velocity.
"""
from typing import Dict, Any
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../requirements")))
from contracts import ReturnEvent, DecisionAction


class CustomerHistoryCheck:
    def __init__(self, high_return_rate_threshold: float = 0.65, warning_return_rate: float = 0.40):
        self.high_return_rate_threshold = high_return_rate_threshold
        self.warning_return_rate = warning_return_rate

    def evaluate(self, event: ReturnEvent) -> Dict[str, Any]:
        profile = event.customer_profile
        order = event.order_details
        
        return_rate = profile.historical_return_rate
        total_orders = profile.total_orders_count
        total_returns = profile.total_returns_count
        chargebacks = profile.dispute_chargeback_count
        account_age = profile.account_age_days
        order_amount = order.total_order_amount
        
        risk_score = 0.0
        reasons = []
        indicators = []
        
        # 1. Serial Returner Velocity
        if return_rate >= self.high_return_rate_threshold and total_orders >= 3:
            risk_score += 60.0
            indicators.append("HIGH_RETURN_RATE_BURDEN")
            reasons.append(f"Chronic serial returner profile: {return_rate*100:.1f}% return rate across {total_orders} orders ({total_returns} returns).")
        elif return_rate >= self.warning_return_rate and total_orders >= 3:
            risk_score += 30.0
            indicators.append("ELEVATED_RETURN_RATE")
            reasons.append(f"Elevated historical return rate: {return_rate*100:.1f}% ({total_returns}/{total_orders} orders returned).")

        # 2. Chargeback / Dispute History
        if chargebacks >= 2:
            risk_score += 40.0
            indicators.append("CHRONIC_CHARGEBACK_HISTORY")
            reasons.append(f"Critical risk: Customer has {chargebacks} prior payment dispute/chargeback records.")
        elif chargebacks == 1:
            risk_score += 20.0
            indicators.append("PRIOR_DISPUTE_FLAG")
            reasons.append("Prior payment dispute recorded on customer profile.")

        # 3. Fresh Account High-Value Order Velocity
        if account_age <= 7 and order_amount >= 15000:
            risk_score += 25.0
            indicators.append("NEW_ACCOUNT_HIGH_VALUE")
            reasons.append(f"New account ({account_age} days old) initiating high-value return (₹{order_amount:,.2f}).")

        # Decision
        if risk_score >= 60.0:
            action = DecisionAction.BLOCK
        elif risk_score >= 30.0:
            action = DecisionAction.FLAG
        else:
            action = DecisionAction.ALLOW
            reasons.append(f"Customer return profile healthy ({return_rate*100:.1f}% return rate, {account_age}d account age).")

        passed = (action == DecisionAction.ALLOW)
        
        return {
            "passed": passed,
            "action": action,
            "confidence": 0.95 if action != DecisionAction.FLAG else 0.85,
            "risk_score": min(100.0, risk_score),
            "historical_return_rate": round(return_rate, 3),
            "account_age_days": account_age,
            "total_orders": total_orders,
            "total_returns": total_returns,
            "chargeback_count": chargebacks,
            "indicators": indicators,
            "reason": " ".join(reasons)
        }
