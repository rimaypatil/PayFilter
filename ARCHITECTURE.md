# PayFilter — System & Security Architecture

PayFilter is a real-time risk assessment, anomaly detection, cryptographic audit logging, and payment authorization firewall designed for autonomous AI agent transactions prior to order execution on Razorpay.

---

## 1. Complete Decision & Integration Pipeline (Phases 1–5)

```text
       [ Autonomous AI Agent / Checkout Request ]
                           │
                           ▼ (X-API-Key Header)
            ┌─────────────────────────────┐
            │   1. API Key Auth & RLS     │ ──► SHA-256 Hashed Lookup
            └──────────────┬──────────────┘
                           │
                           ▼
            ┌─────────────────────────────┐
            │   2. Emergency Kill Switch  │ ──► [Active?] ──► BLOCKED + Claude NL Reason
            └──────────────┬──────────────┘
                           │ (Inactive)
                           ▼
            ┌─────────────────────────────┐
            │   3. Idempotency Check      │ ──► [Duplicate?] ──► Return Cached Decision
            └──────────────┬──────────────┘
                           │
                           ▼
            ┌─────────────────────────────┐
            │  4. Leakage-Safe Features   │ ──► Rolling customer baseline (strictly < t_curr)
            └──────────────┬──────────────┘
                           │
                           ▼
            ┌─────────────────────────────┐
            │  5. Deterministic Rules     │ ──► Velocity caps, max order cap, category limits
            └──────────────┬──────────────┘
                           │
                           ▼
            ┌─────────────────────────────┐
            │  6. Scikit-Learn ML Model   │ ──► IsolationForest (SHA-256 integrity verified)
            └──────────────┬──────────────┘
                           │
                           ▼
            ┌─────────────────────────────┐
            │  7. Decision Synthesizer    │
            └──────────────┬──────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     [ APPROVED ]      [ HELD ]        [ BLOCKED ]
          │                │                │
          ▼                ▼                ▼
   Create Razorpay    Analyst Queue     Claude NL Reason
   Test-Mode Order    (Safe Timeout)    (Zero-PII)
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
            ┌─────────────────────────────┐
            │  8. Chained Cryptography    │ ──► SHA-256 Row Hash: H(prev_hash || row)
            │      Audit Trail Log        │
            └─────────────────────────────┘
```

---

## 2. Decision Tiers & Integrations

| Decision Tier | Anomaly Score Range / Condition | Phase 5 Integration Action | Next Step / Safe Resolution |
|---|---|---|---|
| **Approved** | Score &lt; 0.45 & passes rules | Calls `razorpay_client.create_order()` | Attaches `razorpay_order_id`, proceeds to payment gateway |
| **Held** | 0.45 &le; Score &lt; 0.70 or soft rule | Calls `claude_client.explain_decision()` | Flagged queue for human confirmation or safe auto-timeout |
| **Blocked** | Score &ge; 0.70 or hard limit breach | Calls `claude_client.explain_decision()` | Aborts checkout, records zero-PII plain-English explanation |

---

## 3. Core Security Principles

1. **Zero-PII Data Minimization**:
   - Claude API calls receive strictly numerical and categorical telemetry (amount, ratios, velocity, rule name, risk score).
   - Customer names, card details, addresses, and personal identifiers are never included in prompts.
2. **Failure-Tolerant Resilience**:
   - Neither external Razorpay API errors nor Claude API timeouts can fail or roll back a PayFilter risk decision.
   - Fallback explanations and audit logging ensure continuous 100% service uptime.
3. **Test-Mode Safety Enforcement**:
   - Configuration checks refuse Razorpay live-mode keys (`rzp_live_...`) to prevent accidental charges in staging/test environments.
4. **Pre-Parse Webhook Signature Verification**:
   - `POST /webhooks/razorpay` verifies constant-time HMAC SHA-256 signatures against raw request bytes before JSON decoding.
5. **Cryptographic Tamper-Evident Audit Chain**:
   - Every transaction score, human confirmation, timeout resolution, and webhook event is linked in an immutable SHA-256 hash chain ($H_n = \text{SHA256}(H_{n-1} \parallel \text{data})$).
