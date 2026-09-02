"""
Velocity & Retry Escalation Defensive Check for Agentic Commerce AI Risk Shield.
Tracks session transaction frequency and price/quantity escalation across retries.
"""
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../requirements")))
from contracts import Transaction, DecisionAction


class VelocityCheck:
    def __init__(self, window_seconds: int = 60, burst_limit: int = 5, burst_warning: int = 3):
        self.window_seconds = window_seconds
        self.burst_limit = burst_limit
        self.burst_warning = burst_warning
        
        # In-memory sliding windows: session_id -> deque of timestamps
        self.session_windows = defaultdict(deque)
        # Session historical cart amounts: session_id -> list of total_amounts
        self.session_amounts = defaultdict(list)

    def _parse_timestamp(self, ts_str: str) -> datetime:
        try:
            clean = ts_str.replace("Z", "+00:00")
            return datetime.fromisoformat(clean)
        except Exception:
            return datetime.utcnow()

    def reset_state(self):
        """Clears in-memory session counters (for clean evaluation replays)."""
        self.session_windows.clear()
        self.session_amounts.clear()

    def evaluate(self, transaction: Transaction) -> Dict[str, Any]:
        meta = transaction.agent_metadata
        payload = transaction.checkout_payload
        intent = transaction.user_stated_intent
        
        current_time = self._parse_timestamp(transaction.timestamp)
        session_id = meta.session_id
        retry_count = meta.retry_count
        current_amount = payload.total_amount
        
        # 1. Sliding Window Velocity Tracking
        window = self.session_windows[session_id]
        
        # Prune timestamps older than window_seconds
        cutoff = current_time - timedelta(seconds=self.window_seconds)
        while window and window[0] < cutoff:
            window.popleft()
            
        # Append current request
        window.append(current_time)
        window_count = len(window)
        
        # 2. Retry Escalation Tracking
        history = self.session_amounts[session_id]
        escalation_pct = 0.0
        
        if history:
            prev_amount = history[-1]
            if prev_amount > 0:
                escalation_pct = round(((current_amount - prev_amount) / prev_amount) * 100, 2)
        elif retry_count > 0 and intent.max_budget > 0:
            escalation_pct = round(((current_amount - intent.max_budget) / intent.max_budget) * 100, 2)
            
        history.append(current_amount)
        
        # Decision Logic
        action = DecisionAction.ALLOW
        reasons = []
        confidence = 0.96
        risk_score = 0.0
        
        # Velocity Burst Over Limit (> 5 tx/60s) -> BLOCK
        if window_count > self.burst_limit:
            action = DecisionAction.BLOCK
            reasons.append(f"Velocity burst limit exceeded: {window_count} checkout requests in {self.window_seconds}s (limit: {self.burst_limit}).")
            risk_score = 95.0
            
        # Retry Escalation (> 50% increase on retry)
        elif retry_count >= 3 and escalation_pct > 50.0:
            action = DecisionAction.BLOCK
            reasons.append(f"Persistent retry price escalation: {escalation_pct:+.1f}% jump on retry #{retry_count} (current: ₹{current_amount:,.2f}).")
            risk_score = 90.0
            
        elif retry_count >= 1 and escalation_pct > 50.0:
            action = DecisionAction.FLAG
            reasons.append(f"Retry price escalation: Cart amount jumped by {escalation_pct:+.1f}% on retry attempt #{retry_count}.")
            risk_score = 65.0
            
        # Velocity Warning (3 to 5 tx/60s) -> FLAG
        elif window_count >= self.burst_warning and window_count <= self.burst_limit:
            action = DecisionAction.FLAG
            reasons.append(f"Elevated request frequency: {window_count} requests in {self.window_seconds}s.")
            risk_score = 45.0
            
        else:
            action = DecisionAction.ALLOW
            reasons.append(f"Velocity normal ({window_count} tx in window). No retry escalation.")
            risk_score = 0.0
            
        passed = (action == DecisionAction.ALLOW)
        
        return {
            "passed": passed,
            "action": action,
            "confidence": confidence,
            "risk_score": risk_score,
            "window_count": window_count,
            "retry_count": retry_count,
            "escalation_pct": escalation_pct,
            "reason": " ".join(reasons)
        }
