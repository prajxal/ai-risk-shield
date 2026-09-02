"""
Prompt Injection Defensive Check for Agentic Commerce AI Risk Shield.
Scans product descriptions, titles, shipping addresses, and agent metadata for prompt injection signatures.
"""
import re
from typing import Dict, Any, List, Tuple
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../requirements")))
from contracts import Transaction, DecisionAction


class InjectionCheck:
    # High-confidence deterministic injection patterns
    PATTERNS = [
        # System instruction overrides
        (r"(?i)ignore\s+(previous|all|prior)\s+(instructions|constraints|budget|rules)", "INSTRUCTION_OVERRIDE"),
        (r"(?i)disregard\s+(buyer|budget|user|previous|all)\s+(constraints|limit|instructions|checks)", "INSTRUCTION_OVERRIDE"),
        (r"(?i)system\s*prompt\s*override", "SYSTEM_PROMPT_OVERRIDE"),
        (r"(?i)developer\s*mode\s*(enabled|:)?", "DEVELOPER_MODE_MARKER"),
        (r"(?i)assistant\s*rule\s*update", "RULE_OVERRIDE"),
        (r"(?i)important\s*update\s*:\s*system\s*instructions", "SYSTEM_REFRESH_SPOOF"),
        
        # Tag & Delimiter Spoofing
        (r"<!--\s*(SYSTEM|ADMIN|OVERRIDE).*?-->", "HTML_COMMENT_INJECTION"),
        (r"<\s*(INSTRUCTION|ADMIN_COMMAND|SYSTEM)\s*>.*?</\s*(INSTRUCTION|ADMIN_COMMAND|SYSTEM)\s*>", "XML_TAG_INJECTION"),
        (r"```\s*system", "MARKDOWN_SYSTEM_BLOCK"),
        (r"\[\s*(SYSTEM|DEVELOPER\s*MODE|ADMIN).*?\]", "BRACKETED_DIRECTIVE"),
        (r"===\s*HUMAN\s*INTERVENTION\s*REQUIRED.*?===", "DELIMITER_SPOOFING"),
        
        # Malicious Action Hijacking
        (r"(?i)redirect\s+shipping\s+address\s+to", "DROP_POINT_REDIRECTION"),
        (r"(?i)delivery\s+to\s+(rogue|attacker|drop_site|fraud_drop)", "DROP_POINT_REDIRECTION"),
        (r"(?i)override\s+(total_amount|quantity|shipping)", "FIELD_OVERRIDE"),
        (r"(?i)transfer\s+payment\s+token\s+to", "TOKEN_EXFILTRATION"),
        (r"(?i)bypass\s+(safety\s+checks|verification\s+checks)", "SAFETY_BYPASS"),
        (r"(?i)grant\s+(100%|full)\s+discount\s+(code|bypass)", "DISCOUNT_EXPLOIT"),
    ]

    def evaluate(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Evaluates transaction payload for prompt injection attacks.
        Returns check summary with decision, confidence, matched indicators, and reason.
        """
        matched_indicators = []
        snippets = []
        
        # Collect all inspectable text surfaces
        texts_to_scan: List[Tuple[str, str]] = []
        
        for idx, item in enumerate(transaction.checkout_payload.cart_items):
            if item.title:
                texts_to_scan.append((f"cart_items[{idx}].title", item.title))
            if item.item_description:
                texts_to_scan.append((f"cart_items[{idx}].item_description", item.item_description))
                
        if transaction.checkout_payload.shipping_address:
            texts_to_scan.append(("checkout_payload.shipping_address", transaction.checkout_payload.shipping_address))
            
        # Scan patterns
        for surface, text in texts_to_scan:
            for pattern, indicator_name in self.PATTERNS:
                matches = re.findall(pattern, text, re.DOTALL)
                if matches:
                    matched_indicators.append(indicator_name)
                    # Extract small snippet for explainability
                    snippet = text.strip()
                    if len(snippet) > 80:
                        snippet = snippet[:77] + "..."
                    snippets.append(f"{surface}: '{snippet}'")
                    
        # Remove duplicate indicators and snippets
        unique_indicators = list(dict.fromkeys(matched_indicators))
        unique_snippets = list(dict.fromkeys(snippets))
        
        if unique_indicators:
            return {
                "passed": False,
                "action": DecisionAction.BLOCK,
                "confidence": 0.98,
                "risk_score": 95.0,
                "indicators": unique_indicators,
                "matched_surfaces": unique_snippets,
                "reason": f"Prompt injection detected ({', '.join(unique_indicators)}) in product metadata: {'; '.join(unique_snippets)}"
            }
            
        return {
            "passed": True,
            "action": DecisionAction.ALLOW,
            "confidence": 0.99,
            "risk_score": 0.0,
            "indicators": [],
            "matched_surfaces": [],
            "reason": "No prompt injection patterns detected in payload."
        }
