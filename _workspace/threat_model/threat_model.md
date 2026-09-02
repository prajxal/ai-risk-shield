# Return-Risk Threat Model & Abuse Taxonomy (Track 02: AI Risk Manager)

## 1. Domain & Scope
The **Return-Risk Shield** protects merchants from loss originating from post-purchase return abuse and reverse-logistics fraud:
1. **Wardrobing**: Using luxury/festive occasionwear once and returning it after the event.
2. **Bracketing Abuse**: Ordering multi-size/color variants in bulk, keeping one, and returning the rest at merchant shipping expense.
3. **Serial-Returner Fraud**: Chronic refund abuse (>65% return rate, prior chargebacks).
4. **False Damage Claims & Arbitrage**: Claiming sealed electronics arrived defective, missing parts/component swaps, and COD cash conversion exploitation.

## 2. Attack Vectors & Policy Actions

| Threat ID | Threat Name | Key Signals | Policy Action |
| :--- | :--- | :--- | :--- |
| `THR-01` | **Wardrobing** | `days_since_purchase >= 18`, `TAGS_REMOVED`/`USED_ONCE`, event notes | `BLOCK` (score ≥ 60) |
| `THR-02` | **Bracketing Abuse** | Multiple size/color SKUs in same order, returning ≥ 1 variant | `FLAG` (score ≥ 30) |
| `THR-03` | **Serial-Returner Fraud** | `historical_return_rate >= 0.65`, `dispute_chargeback_count >= 1` | `BLOCK` (score ≥ 80) |
| `THR-04` | **False Damage Claims** | `DEFECTIVE_DAMAGED` on electronics >₹12k, `MISSING_PARTS`, COD instant cash | `BLOCK` / `FLAG` |
