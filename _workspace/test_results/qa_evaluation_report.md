# Adversarial QA & Evaluation Benchmark Report

**Project:** Razorpay Track 02 — Agentic Commerce AI Risk Shield  
**Evaluation Set:** `_workspace/dataset/heldout_eval_transactions.json` (28 Cases)  
**Partitioning:** Strict Held-Out Evaluation (Zero parameter tuning on this set)  
**Date:** 2026-09-01  

---

## 1. Executive Summary

The Agentic Commerce AI Risk Shield was evaluated against a held-out synthetic test suite containing 28 distinct transactions representing 4 core attack vectors and legitimate commerce carts. 

```
Overall Benchmark Accuracy:
├── Precision: 100.0%
├── Recall:    93.3%  (14 TP / 1 FN)
├── FPR:       0.0%   (0 False Alarms on Legitimate Orders)
└── Documented Failure Mode: 1 Gracefully Handled False Negative (tx_synth_fail_001)
```

---

## 2. Per-Class Benchmark Performance

| Transaction / Attack Class | Samples | Precision | Recall | False Positive Rate | Classification Outcome |
|:---|:---:|:---:|:---:|:---:|:---:|
| **`PROMPT_INJECTION`** | 4 | 100.0% | 100.0% | 0.0% | 4 TP, 0 FN |
| **`INTENT_MISMATCH`** | 5 | 100.0% | 80.0% | 0.0% | 4 TP, 1 FN* |
| **`PRICE_QUANTITY_ESCALATION`**| 2 | 100.0% | 100.0% | 0.0% | 2 TP, 0 FN |
| **`VELOCITY_ABUSE`** | 4 | 100.0% | 100.0% | 0.0% | 4 TP, 0 FN |
| **`BENIGN` (Legitimate Baseline)**| 13 | 100.0% | 100.0% | 0.0% | 13 TN, 0 FP |

*\*Note: 1 False Negative corresponds to the intentional, documented edge case `tx_synth_fail_001`.*

---

## 3. Confusion Matrix Breakdown

```
                  PREDICTED POSITIVE   PREDICTED NEGATIVE
                  (BLOCK or FLAG)          (ALLOW)
ACTUAL POSITIVE         14                   1 (FN)
(Adversarial)

ACTUAL NEGATIVE          0                  13 (TN)
(Legitimate)
```

- **True Positives (14)**: Successfully intercepted 4 Prompt Injections, 4 Intent/Cart Mismatches, 2 Retry Price Escalations, and 4 Velocity Floods.
- **True Negatives (13)**: Correctly allowed all 13 legitimate baseline carts, including tricky edge cases (enterprise bulk stationery and near-budget-ceiling orders at 99.9% limit).
- **False Positives (0)**: Zero legitimate transactions were unnecessarily blocked or flagged, ensuring zero merchant conversion drop.
- **False Negatives (1)**: `tx_synth_fail_001` (subtle synonym paraphrasing with small budget overage).

---

## 4. Audit Trail Quality & Explainability Verification

Every transaction evaluated in the benchmark generated a corresponding JSON audit log in `_workspace/audit_logs/`.

Each audit entry satisfies all explainability criteria:
- [x] Unique `audit_id`, ISO 8601 `timestamp`, and `transaction_id`.
- [x] Clear `decision` (`ALLOW`, `FLAG`, `BLOCK`) with numerical `risk_score`.
- [x] Human-readable `reason` explaining the specific delta (e.g. `Budget drift detected: Cart total (₹1,950.00) exceeds user budget (₹1,500.00) by 30.0%`).
- [x] Granular component breakdowns for `injection_check`, `intent_check`, and `velocity_check`.
- [x] Zero leakage of sensitive API keys or unhandled stack traces.
