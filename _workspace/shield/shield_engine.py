"""
Shield Defensive Engine for Return-Risk Shield (AI Risk Manager - Track 02).
Orchestrates sequential execution of:
1. CustomerHistoryCheck (Serial-Returner & Velocity Abuse)
2. WardrobingBracketingCheck (Occasionwear Wardrobing & Size/Color Bracketing)
3. ClaimAnomalyCheck (False Damage Claims & Cash Arbitrage)
Emits structured AuditEntry for every return evaluation decision.
"""
from typing import Dict, Any, Tuple, Union, Optional
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../requirements")))
from contracts import ReturnEvent, ShieldDecision, AuditEntry, DecisionAction, AbuseClass

from checks.customer_history_check import CustomerHistoryCheck
from checks.wardrobing_bracketing_check import WardrobingBracketingCheck
from checks.claim_anomaly_check import ClaimAnomalyCheck
from audit_logger import AuditLogger


class ShieldEngine:
    def __init__(self, log_dir: Optional[str] = None):
        self.customer_history_check = CustomerHistoryCheck()
        self.wardrobing_bracketing_check = WardrobingBracketingCheck()
        self.claim_anomaly_check = ClaimAnomalyCheck()
        self.audit_logger = AuditLogger(log_dir=log_dir)

    def reset_state(self):
        """Resets stateful checks if any."""
        pass

    def evaluate(self, event_input: Union[ReturnEvent, Dict[str, Any]], write_to_disk: bool = True) -> Tuple[ShieldDecision, AuditEntry]:
        """
        Main defensive return-risk evaluation pipeline.
        Executes: CustomerHistoryCheck -> WardrobingBracketingCheck -> ClaimAnomalyCheck.
        Returns: (ShieldDecision, AuditEntry)
        """
        if isinstance(event_input, dict):
            event = ReturnEvent(**event_input)
        else:
            event = event_input

        check_details: Dict[str, Any] = {}
        triggered_checks: list[str] = []
        overall_reasons: list[str] = []
        max_risk_score = 0.0
        final_action = DecisionAction.ALLOW
        min_confidence = 1.0

        # -------------------------------------------------------------
        # Step 1: Customer Return History & Serial Returner Check
        # -------------------------------------------------------------
        cust_res = self.customer_history_check.evaluate(event)
        check_details["customer_history_check"] = cust_res

        if cust_res["action"] == DecisionAction.BLOCK:
            final_action = DecisionAction.BLOCK
            triggered_checks.append("SERIAL_RETURNER_FRAUD")
            overall_reasons.append(cust_res["reason"])
            max_risk_score = max(max_risk_score, cust_res["risk_score"])
            min_confidence = min(min_confidence, cust_res["confidence"])
        elif cust_res["action"] == DecisionAction.FLAG:
            if final_action != DecisionAction.BLOCK:
                final_action = DecisionAction.FLAG
            triggered_checks.append("SERIAL_RETURNER_FRAUD")
            overall_reasons.append(cust_res["reason"])
            max_risk_score = max(max_risk_score, cust_res["risk_score"])
            min_confidence = min(min_confidence, cust_res["confidence"])

        # -------------------------------------------------------------
        # Step 2: Wardrobing & Bracketing Pattern Check
        # -------------------------------------------------------------
        wardrobe_res = self.wardrobing_bracketing_check.evaluate(event)
        check_details["wardrobing_bracketing_check"] = wardrobe_res

        if wardrobe_res["action"] == DecisionAction.BLOCK:
            final_action = DecisionAction.BLOCK
            if wardrobe_res.get("is_wardrobing"):
                triggered_checks.append("WARDROBING")
            if wardrobe_res.get("is_bracketing"):
                triggered_checks.append("BRACKETING_ABUSE")
            overall_reasons.append(wardrobe_res["reason"])
            max_risk_score = max(max_risk_score, wardrobe_res["risk_score"])
            min_confidence = min(min_confidence, wardrobe_res["confidence"])
        elif wardrobe_res["action"] == DecisionAction.FLAG:
            if final_action != DecisionAction.BLOCK:
                final_action = DecisionAction.FLAG
            if wardrobe_res.get("is_wardrobing"):
                triggered_checks.append("WARDROBING")
            if wardrobe_res.get("is_bracketing"):
                triggered_checks.append("BRACKETING_ABUSE")
            overall_reasons.append(wardrobe_res["reason"])
            max_risk_score = max(max_risk_score, wardrobe_res["risk_score"])
            min_confidence = min(min_confidence, wardrobe_res["confidence"])

        # -------------------------------------------------------------
        # Step 3: Claim Anomaly & False Damage / Cash Arbitrage Check
        # -------------------------------------------------------------
        claim_res = self.claim_anomaly_check.evaluate(event)
        check_details["claim_anomaly_check"] = claim_res

        if claim_res["action"] == DecisionAction.BLOCK:
            final_action = DecisionAction.BLOCK
            triggered_checks.append("FALSE_DAMAGE_CLAIM")
            overall_reasons.append(claim_res["reason"])
            max_risk_score = max(max_risk_score, claim_res["risk_score"])
            min_confidence = min(min_confidence, claim_res["confidence"])
        elif claim_res["action"] == DecisionAction.FLAG:
            if final_action != DecisionAction.BLOCK:
                final_action = DecisionAction.FLAG
            triggered_checks.append("FALSE_DAMAGE_CLAIM")
            overall_reasons.append(claim_res["reason"])
            max_risk_score = max(max_risk_score, claim_res["risk_score"])
            min_confidence = min(min_confidence, claim_res["confidence"])

        # Default ALLOW summary if all checks passed
        if final_action == DecisionAction.ALLOW:
            overall_reasons = ["Legitimate return request: Customer profile healthy, standard timeline, no wardrobing or damage claim anomalies."]
            max_risk_score = 5.0
            min_confidence = 0.98

        decision = ShieldDecision(
            action=final_action,
            reason=" | ".join(overall_reasons),
            triggered_checks=triggered_checks,
            confidence=min_confidence,
            risk_score=max_risk_score
        )

        audit_entry = self.audit_logger.log(
            event_id=event.event_id,
            customer_id=event.customer_profile.customer_id,
            order_id=event.order_details.order_id,
            return_id=event.return_request.return_id,
            decision=final_action,
            reason=decision.reason,
            triggered_checks=triggered_checks,
            check_details=check_details,
            timestamp=event.timestamp,
            write_to_disk=write_to_disk
        )

        return decision, audit_entry
