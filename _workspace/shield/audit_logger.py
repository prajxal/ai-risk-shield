"""
Structured Audit Logger for Return-Risk Shield (AI Risk Manager).
Stores every evaluation decision in _workspace/audit_logs/{timestamp}_{event_id}_{audit_id}.json.
Conforms strictly to AuditEntry schema from _workspace/requirements/contracts.py.
"""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../requirements")))
from contracts import AuditEntry, DecisionAction, ShieldDecision


class AuditLogger:
    def __init__(self, log_dir: Optional[str] = None, max_live_logs: int = 200):
        if log_dir is None:
            self.log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../audit_logs"))
        else:
            self.log_dir = os.path.abspath(log_dir)
        self.max_live_logs = max_live_logs
        os.makedirs(self.log_dir, exist_ok=True)

    def _prune_live_logs(self):
        """
        Maintains a rolling buffer for live traffic audit logs only.
        NEVER touches failure cases (ret_synth_fail_001 / tx_synth_fail_001), demo logs, or eval logs.
        """
        try:
            files = [
                f for f in os.listdir(self.log_dir)
                if f.endswith(".json") and ("_ret_live_" in f or "_tx_live_" in f) and "fail" not in f
            ]
            if len(files) > self.max_live_logs:
                # Sort ascending (oldest first)
                files.sort()
                excess_count = len(files) - self.max_live_logs
                for old_f in files[:excess_count]:
                    try:
                        os.remove(os.path.join(self.log_dir, old_f))
                    except OSError:
                        pass
        except Exception:
            pass

    def log(
        self,
        event_id: str,
        customer_id: str,
        order_id: str,
        return_id: str,
        decision: DecisionAction,
        reason: str,
        triggered_checks: List[str],
        check_details: Dict[str, Any],
        timestamp: Optional[str] = None,
        write_to_disk: bool = True
    ) -> AuditEntry:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
        short_id = uuid.uuid4().hex[:8]
        audit_id = f"audit_{short_id}"
        
        entry = AuditEntry(
            audit_id=audit_id,
            timestamp=timestamp,
            event_id=event_id,
            customer_id=customer_id,
            order_id=order_id,
            return_id=return_id,
            decision=decision,
            reason=reason,
            triggered_checks=triggered_checks,
            check_details=check_details
        )
        
        if write_to_disk:
            # Format safe filename: YYYYMMDD_HHMMSS_{event_id}_{audit_id}.json
            safe_time = timestamp.replace(":", "-").replace(".", "-")
            filename = f"{safe_time}_{event_id}_{audit_id}.json"
            filepath = os.path.join(self.log_dir, filename)
            
            with open(filepath, "w") as f:
                json.dump(entry.model_dump(), f, indent=2)

            # Apply rolling cap if this is a live synthetic transaction
            if "_ret_live_" in filename or "_tx_live_" in filename:
                self._prune_live_logs()
            
        return entry
