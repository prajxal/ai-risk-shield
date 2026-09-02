"""
Structured Audit Logger for Agentic Commerce AI Risk Shield.
Stores every evaluation decision in _workspace/audit_logs/{timestamp}_{tx_id}.json.
Conforms strictly to AuditEntry schema from _workspace/requirements/contracts.py.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../requirements")))
from contracts import AuditEntry, DecisionAction, ShieldDecision


class AuditLogger:
    def __init__(self, log_dir: Optional[str] = None):
        if log_dir is None:
            self.log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../audit_logs"))
        else:
            self.log_dir = os.path.abspath(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)

    def log(
        self,
        transaction_id: str,
        agent_id: str,
        session_id: str,
        decision: DecisionAction,
        reason: str,
        triggered_checks: List[str],
        check_details: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> AuditEntry:
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"
            
        short_id = uuid.uuid4().hex[:8]
        audit_id = f"audit_{short_id}"
        
        entry = AuditEntry(
            audit_id=audit_id,
            timestamp=timestamp,
            transaction_id=transaction_id,
            agent_id=agent_id,
            session_id=session_id,
            decision=decision,
            reason=reason,
            triggered_checks=triggered_checks,
            check_details=check_details
        )
        
        # Format safe filename: YYYYMMDD_HHMMSS_{tx_id}_{audit_id}.json
        safe_time = timestamp.replace(":", "-").replace(".", "-")
        filename = f"{safe_time}_{transaction_id}_{audit_id}.json"
        filepath = os.path.join(self.log_dir, filename)
        
        with open(filepath, "w") as f:
            json.dump(entry.model_dump(), f, indent=2)
            
        return entry
