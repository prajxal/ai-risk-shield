"""
Intent-Consistency Defensive Check for Agentic Commerce AI Risk Shield.
Priority Check: Compares buyer agent stated intent with final checkout cart payload.
Evaluates Budget Drift, Quantity Inflation, and Semantic SKU/Category Consistency.
"""
import re
from typing import Dict, Any, List, Set
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../requirements")))
from contracts import Transaction, DecisionAction


class IntentConsistencyCheck:
    def __init__(self):
        # Common stopwords to filter for keyword extraction
        self.stopwords = {
            "a", "an", "the", "in", "on", "for", "with", "and", "or", "of", "to",
            "at", "by", "from", "under", "below", "pack", "set", "box", "only",
            "standard", "basic", "good", "quality", "piece", "pieces", "unit", "units",
            "per", "total", "each", "all"
        }

    def _tokenize(self, text: str) -> Set[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        tokens = set(cleaned.split()) - self.stopwords
        return {t for t in tokens if len(t) > 1}

    def _compute_semantic_similarity(self, requested: str, cart_titles: List[str], cart_descs: List[str]) -> float:
        """
        Computes token overlap similarity between stated request and cart items.
        Returns a score between 0.0 and 1.0.
        """
        req_tokens = self._tokenize(requested)
        if not req_tokens:
            return 1.0
            
        cart_tokens = set()
        for t in cart_titles:
            cart_tokens.update(self._tokenize(t))
        for d in cart_descs:
            cart_tokens.update(self._tokenize(d))
            
        if not cart_tokens:
            return 0.0
            
        matched_tokens = set()
        
        # 1. Direct token intersection
        for r in req_tokens:
            if r in cart_tokens:
                matched_tokens.add(r)
                
        # 2. Substring & Dimension normalization
        dimension_equivalences = {
            "xxl": {"extended", "large", "xl", "xxl", "wide"},
            "90x40cm": {"900x400mm", "90x40", "900x400"},
            "60x45cm": {"600x450mm", "60x45", "600x450"},
            "1080p": {"fhd", "1080", "hd"},
            "4k": {"uhd", "2160p", "4k"},
            "1tb": {"1000gb", "1024gb", "1tb"},
            "500gb": {"512gb", "500gb"},
            "1l": {"1000ml", "1l", "liter", "litre"},
            "65w": {"65w", "gan", "fast"}
        }
        
        # 3. Domain synonym mappings for commerce items
        synonyms = {
            "mouse": {"mouse", "mice", "optical", "trackball", "pointer", "vertical"},
            "keyboard": {"keyboard", "keypad", "switches", "tkl", "mech", "mechanical"},
            "headphone": {"headphone", "headphones", "earbuds", "earphones", "headset", "anc", "tws", "iem", "iems", "monitors", "ear"},
            "headphones": {"headphone", "headphones", "earbuds", "earphones", "headset", "anc", "tws", "iem", "iems", "monitors", "ear"},
            "earbuds": {"earbuds", "earphones", "tws", "headphones", "in-ear", "iem", "iems", "monitors"},
            "earphones": {"earbuds", "earphones", "tws", "headphones", "in-ear", "iem", "iems", "monitors"},
            "monitors": {"monitors", "monitor", "display", "screen", "iem", "earphones", "headphones"},
            "mic": {"mic", "microphone", "condenser", "cardioid", "podcast"},
            "microphone": {"mic", "microphone", "condenser", "cardioid", "podcast"},
            "mug": {"mug", "mugs", "cup", "cups", "flask", "tea", "coffee"},
            "mugs": {"mug", "mugs", "cup", "cups", "flask", "tea", "coffee"},
            "notebook": {"notebook", "journal", "diary", "pad", "notepad", "cubes"},
            "pens": {"pen", "pens", "ballpoint", "ink"},
            "cable": {"cable", "cord", "wire", "lead"},
            "stand": {"stand", "riser", "mount", "arm", "holder", "tray"},
            "cooler": {"cooling", "cooler", "fan", "pad"},
            "mat": {"mat", "pad"},
            "charger": {"charger", "adapter", "gan", "plug", "power", "hub"},
            "clicker": {"clicker", "presenter", "remote", "laser"},
            "filter": {"filter", "screen", "shield", "privacy"},
            "whiteboard": {"whiteboard", "board", "magnetic"},
            "footwear": {"boots", "shoes", "sneakers", "sandals", "slippers"},
            "drone": {"drone", "quadcopter", "uav", "fpv"},
            "watch": {"watch", "smartwatch", "fitness", "tracker"}
        }
        
        for r in req_tokens:
            if r in matched_tokens:
                continue
            if r in dimension_equivalences and dimension_equivalences[r].intersection(cart_tokens):
                matched_tokens.add(r)
                continue
            if r in synonyms and synonyms[r].intersection(cart_tokens):
                matched_tokens.add(r)
                continue
            if any(r in c or c in r for c in cart_tokens):
                matched_tokens.add(r)
                    
        final_similarity = len(matched_tokens) / len(req_tokens)
        return min(1.0, final_similarity)

    def evaluate(self, transaction: Transaction) -> Dict[str, Any]:
        intent = transaction.user_stated_intent
        payload = transaction.checkout_payload
        meta = transaction.agent_metadata
        
        # 1. Budget Drift Calculation
        budget = intent.max_budget
        actual_total = payload.total_amount
        budget_drift_ratio = (actual_total - budget) / budget if budget > 0 else 0.0
        budget_drift_pct = round(budget_drift_ratio * 100, 2)
        
        # 2. Quantity Analysis
        requested_qty = intent.quantity if intent.quantity > 0 else 1
        actual_total_qty = sum(item.quantity for item in payload.cart_items)
        quantity_drift = actual_total_qty - requested_qty
        
        # 3. Item & Category Semantic Consistency
        cart_titles = [item.title for item in payload.cart_items]
        cart_descs = [item.item_description for item in payload.cart_items]
        similarity = self._compute_semantic_similarity(intent.requested_items, cart_titles, cart_descs)
        
        action = DecisionAction.ALLOW
        reasons = []
        confidence = 0.96
        risk_score = 0.0
        
        is_retry = (meta.retry_count > 0)
        
        # Severe Semantic Mismatch (similarity < 0.25) -> BLOCK
        if similarity < 0.25:
            action = DecisionAction.BLOCK
            reasons.append(f"Item category mismatch: Requested '{intent.requested_items}' but cart contains '{', '.join(cart_titles)}' (semantic similarity: {similarity:.2f}).")
            risk_score = 90.0
            
        # Severe Budget Overrun (>50%) on standard initial attempt -> BLOCK
        elif budget_drift_pct > 50.0:
            if is_retry:
                action = DecisionAction.FLAG if meta.retry_count < 3 else DecisionAction.BLOCK
                reasons.append(f"Session retry overrun: Cart total (₹{actual_total:,.2f}) is +{budget_drift_pct:.1f}% above budget on retry #{meta.retry_count}.")
                risk_score = 65.0 if meta.retry_count < 3 else 90.0
            else:
                action = DecisionAction.BLOCK
                reasons.append(f"Severe budget overrun: Cart total (₹{actual_total:,.2f}) exceeds stated max budget (₹{budget:,.2f}) by {budget_drift_pct:.1f}%.")
                risk_score = 85.0
            
        # Quantity Inflation with Price Overrun -> BLOCK
        elif quantity_drift >= 2 and budget_drift_pct > 25.0:
            action = DecisionAction.BLOCK
            reasons.append(f"Quantity inflation: Cart has {actual_total_qty} units (expected {requested_qty}) inflating total to ₹{actual_total:,.2f} (+{budget_drift_pct:.1f}% over budget).")
            risk_score = 80.0

        # Moderate Budget Drift (10% to 50%) -> FLAG
        elif budget_drift_pct > 10.0:
            action = DecisionAction.FLAG
            reasons.append(f"Budget drift detected: Cart total (₹{actual_total:,.2f}) exceeds user budget (₹{budget:,.2f}) by {budget_drift_pct:.1f}%. Requires confirmation.")
            risk_score = min(75.0, 45.0 + (budget_drift_pct - 10.0))
            
        # Moderate Semantic Drift / Partial Match (0.25 <= similarity < 0.40) -> FLAG
        elif similarity < 0.40:
            action = DecisionAction.FLAG
            reasons.append(f"Potential intent divergence: Stated item '{intent.requested_items}' partially matches cart '{', '.join(cart_titles)}' (match score: {similarity:.2f}).")
            risk_score = 45.0
            
        # Minor Quantity Drift -> FLAG
        elif quantity_drift > 0 and budget_drift_pct > 0:
            action = DecisionAction.FLAG
            reasons.append(f"Minor quantity drift: Cart contains {actual_total_qty} units vs {requested_qty} requested.")
            risk_score = 40.0
            
        else:
            action = DecisionAction.ALLOW
            reasons.append(f"Cart items match user intent '{intent.requested_items}' within budget limits (drift: {budget_drift_pct:+.1f}%, match: {similarity:.2f}).")
            risk_score = 5.0

        passed = (action == DecisionAction.ALLOW)
        
        return {
            "passed": passed,
            "action": action,
            "confidence": confidence,
            "risk_score": risk_score,
            "budget_drift_pct": budget_drift_pct,
            "item_similarity": round(similarity, 3),
            "quantity_drift": quantity_drift,
            "actual_total": actual_total,
            "stated_budget": budget,
            "reason": " ".join(reasons)
        }
