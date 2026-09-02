# PRD: Agentic Adversarial Shield & Semantic Intent Verifier

**Track:** 02 — AI Risk Manager
**Event:** Razorpay AI Buildathon
**Author:** Prajwal
**Status:** Draft — build scoped for a 2-day weekend build

---

## 1. Problem Statement

Razorpay has, within the last several months, shipped **RAY Agentic Dashboard**,
conversational/agentic checkout flows, and a public **WebMCP tool**
(`get_product_details`) that lets external AI agents query merchant catalogs
and initiate transactions. This is a deliberate move to make Razorpay
merchants transactable by AI buyers — but it also creates a new attack
surface that did not exist when checkout required a human clicking buttons.

Razorpay's existing risk stack (Magic Checkout's risk engine, native gateway
fraud scoring, Thirdwatch-style device/behavioral signals) is built to catch
**human-originated fraud**: stolen cards, COD abuse, RTO risk, synthetic
buyer identities. None of it is built to catch fraud that originates **inside
an AI agent's own reasoning or tool-call payload** — for example:

- An agent whose instructions get hijacked via prompt injection embedded in
  a product description or a tool response
- An agent whose final checkout cart silently drifts from what it told the
  user it was buying (wrong item, wrong quantity, wrong price)
- An agent (or a coordinated swarm of agent sessions) probing checkout with
  escalating prices/quantities or high transaction velocity

No public product from Razorpay, Stripe (Radar), or fraud vendors
(Signifyd/Riskified) currently addresses this specific class of risk. This is
a genuinely open gap, not a duplicate of an existing feature.

## 2. Goal

Build a **defensive proxy** that sits between an AI buyer agent and a
checkout API, evaluates each transaction attempt for agent-specific attack
patterns, and returns an auditable **ALLOW / FLAG / BLOCK** decision with a
stated reason — before the transaction reaches payment.

This is strictly **defense-only**: the project detects and blocks; it does
not demonstrate, generate, or optimize any attack technique beyond what's
needed to test the shield.

## 3. Non-Goals (explicitly out of scope for this build)

- Not a general-purpose card/COD fraud model (Razorpay already has this)
- Not a production Razorpay integration — test-mode or fully mocked checkout
  API is acceptable and will be stated plainly
- Not a trained ML classifier — pattern-based rules + a single LLM-judge
  call are sufficient and more honestly justifiable in a 2-day build
- Not a polished frontend — a clean CLI/simple dashboard is sufficient; the
  audit trail and metrics carry the demo, not the UI
- No claim of "real-world" data — the eval set is synthetic and will be
  disclosed as such

## 4. Users & Use Case

**Primary user (in this simulation):** a merchant/platform (Razorpay-like)
that has exposed a checkout API to third-party AI buyer agents.

**Use case:** Every incoming agent checkout request is routed through the
Shield before it reaches the actual checkout/payment endpoint. The Shield
either lets it through, flags it for human/merchant review, or blocks it
outright — always with a logged reason.

## 5. System Architecture

Three components, kept deliberately small:

### 5.1 Mock Checkout API (the thing being protected)
- Minimal FastAPI service, 2 endpoints: `create_order`, `checkout`
- In-memory store; no real payment execution
- Represents "Razorpay test-mode API" — explicitly labeled as such

### 5.2 The Shield (the actual deliverable)
Middleware exposing one function:

```
evaluate(transaction) -> {
  decision: "ALLOW" | "FLAG" | "BLOCK",
  reason: string,
  checks_triggered: [ ... ],
  audit_entry: { ... }
}
```

Three checks, run in sequence:

1. **Injection Check** — scans the agent's tool-call payload / reasoning
   trace for injected instructions (e.g. text in a product field attempting
   to override quantity/price/constraints). Pattern-matching first, one
   LLM-judge call for ambiguous cases.
2. **Intent-Consistency Check (core differentiator)** — compares the agent's
   *stated* intent (e.g. "2 chairs, ≤ ₹8,000 each") against the *actual*
   cart about to be charged (items, quantities, prices). An NLI-style
   consistency judgment flags mismatches. This is the direct extension of
   the faithfulness-evaluation approach already scoped for the personal
   RAG/NLI learning plan.
3. **Velocity / Identity Check** — rule-based counters: same
   session/device firing repeated orders in a short window, or
   price/quantity escalating across retries (classic tampering pattern).

### 5.3 Attacker Harness (for evaluation only)
- Script that replays a labeled synthetic dataset through the Shield
- Produces the precision/recall table required by the track's bar

## 6. Synthetic Evaluation Dataset

60–80 labeled synthetic agent-checkout attempts, explicitly disclosed as
synthetic in the pitch and README.

**Legitimate (30–40):**
- Normal carts matching stated intent, varied products/prices/quantities
- Deliberate "looks suspicious but isn't" edge cases (bulk orders, prices
  right at a threshold) — needed to measure false-positive rate honestly

**Adversarial (30–40), across 4 attack classes:**
- Prompt injection embedded in product data / tool responses
- Cart-intent mismatch (stated constraint vs. actual cart)
- Price/quantity tampering across retries within one session
- Velocity/identity abuse (many orders, same fingerprint, short window)

Each record carries ground-truth labels (attack class + correct decision)
so the harness can compute honest metrics.

## 7. Success Metrics

- Precision / recall on the synthetic set, broken out **per attack class**
  (not just an aggregate number)
- False-positive rate on the legitimate set, including the deliberately
  tricky "looks suspicious" cases
- At least one known failure case kept in the demo (not hidden), with the
  audit log showing why it was missed or wrongly flagged — this directly
  satisfies the track's "show one failure handled gracefully" requirement
- Every decision must produce a human-readable audit entry (what was
  checked, what triggered, why)

## 8. Deliverables (per Buildathon requirements)

1. Public repo (Shield + mock checkout API + attacker harness + dataset)
2. 5-minute pitch video
3. Architecture writeup (this PRD + a diagram)

## 9. Pitch Structure (5 minutes)

1. **0:00–0:30** — The gap: Razorpay's own WebMCP + agentic checkout means
   AI agents can now transact; nothing polices what those agents actually do
2. **0:30–2:00** — Live demo: a legitimate agent passing through, an
   injection attempt getting blocked with a stated reason, a cart-mismatch
   getting flagged
3. **2:00–3:00** — The numbers: precision/recall table per attack class,
   including the honest unresolved false positive
4. **3:00–4:00** — Why this matters long-term: every new agentic-commerce
   protocol (ACP, AP2, NPCI's UAP) increases this exact attack surface —
   this is infrastructure that gets more necessary over time, not a
   one-off feature

## 10. Build Plan (2-day weekend scope)

| When | Work |
|---|---|
| Sat AM | Build synthetic dataset (60–80 labeled cases); stand up mock checkout API |
| Sat PM | Build Shield: intent-consistency check first, then injection check, then velocity rules |
| Sat eve | Build attacker harness; get first precision/recall numbers |
| Sun AM | Fix false positives/negatives found; build structured audit-log output |
| Sun PM | Build simple metrics dashboard/CLI output; record pitch video |
| Sun eve | Clean up repo, finalize README + architecture doc, submit |

## 11. Risks / Open Questions

- LLM-judge calls for injection/intent checks introduce their own latency
  and cost — acceptable for a demo, flagged as a known production
  consideration rather than solved here
- Dataset is hand-built/LLM-assisted, not adversarially red-teamed at
  scale — disclosed honestly as a limitation, not oversold
- No claim is made that this generalizes beyond the synthetic attack
  classes tested; the README will state this explicitly
