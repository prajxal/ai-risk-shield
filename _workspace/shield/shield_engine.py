"""
Shield Defensive Engine for Agentic Commerce Transactions.
Orchestrates sequential execution of InjectionCheck, IntentConsistencyCheck, and VelocityCheck.
Emits structured AuditEntry for every decision.
"""
from typing import Dict, Any, Tuple, Union, Optional
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../requirements")))
from contracts import Transaction, ShieldDecision, AuditEntry, DecisionAction, AttackClass

from checks.injection_check import InjectionCheck
from checks.intent_check import IntentConsistencyCheck
from checks.velocity_check import VelocityCheck
from audit_logger import AuditLogger


class ShieldEngine:
    def __init__(self, log_dir: Optional[str] = None):
        self.injection_check = InjectionCheck()
        self.intent_check = IntentConsistencyCheck()
        self.velocity_check = VelocityCheck()
        self.audit_logger = AuditLogger(log_dir=log_dir)

    def reset_state(self):
        """Resets stateful checks (e.g. velocity session counters)."""
        self.velocity_check.reset_state()

    def evaluate(self, transaction_input: Union[Transaction, Dict[str, Any]]) -> Tuple[ShieldDecision, AuditEntry]:
        """
        Main defensive proxy evaluation pipeline.
        Executes sequential checks: Injection -> Intent-Consistency -> Velocity/Escalation.
        Returns: (ShieldDecision, AuditEntry)
        """
        # Ensure transaction is a validated Transaction model
        if isinstance(transaction_input, dict):
            transaction = Transaction(**transaction_input)
        else:
            transaction = transaction_input

        check_details: Dict[str, Any] = {}
        triggered_checks: list[str] = []
        overall_reasons: list[str] = []
        max_risk_score = 0.0
        final_action = DecisionAction.ALLOW
        min_confidence = 1.0

        # -------------------------------------------------------------
        # -------------------------------------------------------------
        # Step 1: Prompt Injection Check
        # -------------------------------------------------------------
        inj_res = self.injection_check.evaluate(transaction)
        check_details["injection_check"] = inj_res
        
        if inj_res["action"] == DecisionAction.BLOCK:
            final_action = DecisionAction.BLOCK
            triggered_checks.append("PROMPT_INJECTION")
            overall_reasons.append(inj_res["reason"])
            max_risk_score = max(max_risk_score, inj_res["risk_score"])
            min_confidence = min(min_confidence, inj_res["confidence"])

        # -------------------------------------------------------------
        # Step 2: Intent-Consistency Check (Core Priority Differentiator)
        # -------------------------------------------------------------
        intent_res = self.intent_check.evaluate(transaction)
        check_details["intent_check"] = intent_res
        
        if intent_res["action"] == DecisionAction.BLOCK:
            final_action = DecisionAction.BLOCK
            triggered_checks.append("INTENT_MISMATCH")
            overall_reasons.append(intent_res["reason"])
            max_risk_score = max(max_risk_score, intent_res["risk_score"])
            min_confidence = min(min_confidence, intent_res["confidence"])
            
        elif intent_res["action"] == DecisionAction.FLAG:
            if final_action != DecisionAction.BLOCK:
                final_action = DecisionAction.FLAG
            triggered_checks.append("INTENT_MISMATCH")
            overall_reasons.append(intent_res["reason"])
            max_risk_score = max(max_risk_score, intent_res["risk_score"])
            min_confidence = min(min_confidence, intent_res["confidence"])

        # -------------------------------------------------------------
        # Step 3: Velocity & Retry Escalation Check
        # -------------------------------------------------------------
        vel_res = self.velocity_check.evaluate(transaction)
        check_details["velocity_check"] = vel_res
        
        if vel_res["action"] == DecisionAction.BLOCK:
            final_action = DecisionAction.BLOCK
            if vel_res.get("escalation_pct", 0) > 50:
                triggered_checks.append("PRICE_QUANTITY_ESCALATION")
            else:
                triggered_checks.append("VELOCITY_ABUSE")
            overall_reasons.append(vel_res["reason"])
            max_risk_score = max(max_risk_score, vel_res["risk_score"])
            min_confidence = min(min_confidence, vel_res["confidence"])
            
        elif vel_res["action"] == DecisionAction.FLAG:
            if final_action != DecisionAction.BLOCK:
                final_action = DecisionAction.FLAG
            if vel_res.get("escalation_pct", 0) > 50:
                triggered_checks.append("PRICE_QUANTITY_ESCALATION")
            else:
                triggered_checks.append("VELOCITY_ABUSE")
            overall_reasons.append(vel_res["reason"])
            max_risk_score = max(max_risk_score, vel_res["risk_score"])
            min_confidence = min(min_confidence, vel_res["confidence"])

        # Default ALLOW summary if no flags/blocks
        if final_action == DecisionAction.ALLOW:
            overall_reasons = ["All security checks passed. Cart strictly matches stated intent, zero injection patterns, normal velocity."]
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
            transaction_id=transaction.transaction_id,
            agent_id=transaction.agent_metadata.agent_id,
            session_id=transaction.agent_metadata.session_id,
            decision=final_action,
            reason=decision.reason,
            triggered_checks=triggered_checks,
            check_details=check_details,
            timestamp=transaction.timestamp
        )

        return decision, audit_entry
