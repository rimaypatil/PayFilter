# PayFilter

> **"The Security Layer for AI-Powered Payments"**  
> *AI agents can now move money. PayFilter makes sure they don't move it recklessly.*

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.2+-646CFF?logo=vite)](https://vitejs.dev)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-IsolationForest-F7931E?logo=scikitlearn)](https://scikit-learn.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%20%2B%20RLS-3ECF8E?logo=supabase)](https://supabase.com)
[![Razorpay](https://img.shields.io/badge/Razorpay-Test--Mode%20Orders%20API-0C2340?logo=razorpay)](https://razorpay.com)
[![Anthropic Claude](https://img.shields.io/badge/Anthropic%20Claude-Zero--PII%20Explanations-D97706?logo=anthropic)](https://anthropic.com)
[![Tests](https://img.shields.io/badge/Pytest-96%20Passed%20(100%25)-brightgreen)](https://docs.pytest.org)

```text
       ┌──────────────────┐
       │     AI Agent     │
       └────────┬─────────┘
                │ Payment Request
                ▼
       ┌──────────────────┐
       │    PayFilter     │ ◄── Real-Time Risk & Governance Firewall
       └────────┬─────────┘
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
[ APPROVE ]  [ HOLD ]  [ BLOCK ]
     │          │          │
     ▼          ▼          ▼
  Razorpay   Human      Checkout
  Checkout   Review     Aborted
```

---

## 1. The Problem

Commerce is undergoing a fundamental architectural shift:

```text
Traditional Commerce:    Human Shopper ───────► Decision ───────► Payment Gateway
Agentic Commerce:        Autonomous AI Agent ─► Decision ───────► Payment Gateway
```

When humans buy products online, natural friction exists: confirmation screens, multi-factor authentication, card entry, and conscious review. 

When **autonomous AI agents** (procurement bots, inventory reorder scripts, shopping copilots, personal executive assistants) are granted purchasing authority, they execute financial transactions in milliseconds with zero intrinsic hesitation. This introduces unprecedented risks:

- **Runaway Velocity Loops**: A bug or prompt-interpretation loop firing hundreds of transactions per minute before an engineer notices.
- **Abnormal Purchase Spikes**: Hallucinating or poorly prompted agents purchasing luxury goods, gift cards, or bulk merchandise far outside typical parameters.
- **Prompt Injection & Hijacking**: Malicious third parties injecting adversarial instructions into an agent's context to redirect funds or trigger unapproved checkouts.
- **Merchant Policy Breaches**: Agents violating merchant-mandated spending caps, restricted category lists, or off-hours policies.
- **Machine-Speed Damage**: Millions in financial liability can be incurred in seconds—vastly faster than any human risk team can manually respond to.

> **The Critical Question**:  
> *"What security layer stands between an AI agent's autonomous decision and the irreversible movement of money?"*

---

## 2. The Solution

**PayFilter** is an autonomous pre-payment firewall and risk governance layer that sits directly between the AI agent's checkout decision and payment execution.

```text
       ┌────────────────────────┐
       │    AI Agent Intent     │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   PayFilter Firewall   │
       └───────────┬────────────┘
                   │
       ┌───────────┴───────────────────────┐
       │                                   │
       ▼                                   ▼
┌──────────────┐                   ┌──────────────┐
│  Rule Engine │                   │ ML Anomaly   │
│  (Hard/Soft) │                   │ (IsolationF) │
└──────┬───────┘                   └──────┬───────┘
       │                                  │
       └─────────────────┬────────────────┘
                         ▼
             ┌───────────────────────┐
             │  Decision Synthesizer │
             └───────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
  │   APPROVE   │ │    HOLD     │ │    BLOCK    │
  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
         │               │               │
         ▼               ▼               ▼
     Razorpay          Human         Immediate
     Test-Mode        Review        Abort + Zero-
     Order API         Queue        PII Reasoning
```

### Essential Boundaries & Guarantees:
- **Pre-Payment Gatekeeper**: PayFilter evaluates whether an agent-initiated payment request is safe *before* contacting the payment gateway.
- **Explicit Merchant Integration**: The merchant explicitly integrates PayFilter into their server-side AI-agent orchestration.
- **Not a Razorpay Replacement**: PayFilter works alongside Razorpay. If approved, the transaction proceeds to Razorpay for actual settlement.
- **No Invisible Scraping**: PayFilter does not passively monitor Razorpay; it acts as an active, deterministic filter invoked by the merchant.

---

## 3. Why This Matters for Razorpay

As payment networks evolve toward **agentic commerce**, machine-initiated transactions will quickly surpass human-initiated transactions in both frequency and velocity.

| Dimension | Razorpay Payment Gateway | PayFilter Governance Layer |
|---|---|---|
| **Primary Mandate** | Moves money, settles funds, provides checkout rails | Protects rails from runaway or hijacked agents |
| **Execution Point** | At point of settlement / order creation | **Before** payment gateway invocation |
| **Context Evaluated**| Card validity, 3DS, banking rails, merchant chargebacks | Agent behavioral telemetry, velocity bursts, policy compliance |
| **Operating Model** | Gateway & merchant acquirer | Pre-payment policy, ML firewall & governance console |

**The Strategic Nexus**:  
*Razorpay moves money. AI agents decide what actions to take. PayFilter ensures autonomous agents only move money within strictly governed, policy-compliant boundaries.*

---

## 4. Architecture

```text
 ┌────────────────────────┐
 │   Merchant AI Agent    │ (Simulated Autonomous Buyer - Port 3010)
 └───────────┬────────────┘
             │ HTTP (Private JSON Payload)
             ▼
 ┌────────────────────────┐
 │   Agent Bridge Proxy   │ (Local Integration Bridge - Port 8010)
 └───────────┬────────────┘ (Injects Merchant API Key Server-Side)
             │ POST /transactions/check (X-API-Key)
             ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                      PayFilter API                          │ (FastAPI - Port 8000)
 │                                                             │
 │  ┌───────────────────────────────────────────────────────┐  │
 │  │ 1. Authentication & Tenant Isolation Layer             │  │
 │  │    • SHA-256 Hashed Merchant API Key Verification     │  │
 │  │    • JWT Signature & Role Claims (Supabase Auth)      │  │
 │  │    • Row Level Security (RLS) Tenant Isolation        │  │
 │  └──────────────────────────┬────────────────────────────┘  │
 │                             │                               │
 │  ┌──────────────────────────▼────────────────────────────┐  │
 │  │ 2. Emergency Kill Switch Gate                         │  │
 │  │    • Step-Up OTP Enforced Freeze                      │  │
 │  └──────────────────────────┬────────────────────────────┘  │
 │                             │                               │
 │  ┌──────────────────────────▼────────────────────────────┐  │
 │  │ 3. Idempotency & Replay Protection                    │  │
 │  │    • SHA-256 Payload Cache (Returns Stored Verdict)   │  │
 │  └──────────────────────────┬────────────────────────────┘  │
 │                             │                               │
 │  ┌──────────────────────────▼────────────────────────────┐  │
 │  │ 4. 10-Dimensional Leakage-Safe Feature Extractor      │  │
 │  │    • Rolling Customer Baselines strictly < t_curr     │  │
 │  └──────────────────────────┬────────────────────────────┘  │
 │                             │                               │
 │  ┌──────────────────────────▼────────────────────────────┐  │
 │  │ 5. Dual Risk Engine                                   │  │
 │  │    ├── Deterministic Rules Engine (Velocity/Caps)     │  │
 │  │    └── Scikit-Learn Isolation Forest (SHA-256 Verif.) │  │
 │  └──────────────────────────┬────────────────────────────┘  │
 │                             │                               │
 │  ┌──────────────────────────▼────────────────────────────┐  │
 │  │ 6. Decision Synthesizer (Approve / Hold / Block)       │  │
 │  └──────────────────────────┬────────────────────────────┘  │
 └─────────────────────────────┼───────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
     │  APPROVED   │    │    HELD     │    │   BLOCKED   │
     └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
            │                  │                  │
            ▼                  ▼                  ▼
   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
   │ Razorpay API   │ │ Flagged Queue  │ │ Claude AI SDK  │
   │ (Test Orders)  │ │ (Human Review) │ │ (Zero-PII Exp.)│
   └────────┬───────┘ └────────┬───────┘ └────────┬───────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               │
                               ▼
        ┌─────────────────────────────────────────────┐
        │  Cryptographic Append-Only Audit Trail      │
        │  SHA-256 Hash Chain: Hₙ = Hash(Hₙ₋₁ || Row) │
        │  (Stored in Supabase PostgreSQL)            │
        └──────────────────────┬──────────────────────┘
                               │
                               ▼
        ┌─────────────────────────────────────────────┐
        │       Merchant Security Console UI          │
        │  (Vite + React 18 Glassmorphic Dashboard)   │
        └─────────────────────────────────────────────┘
```

---

## 5. Merchant AI Agent Demonstration

To demonstrate realistic end-to-end integration without mock UI tricks, a dedicated **Merchant AI Agent** application is included:

- **Merchant AI Agent Frontend** (`http://localhost:3010`): A dedicated interface where a merchant or operator instructs an AI agent to complete an autonomous purchase.
- **Local Bridge Proxy** (`http://localhost:8010`): An express/python local bridge that holds the merchant's PayFilter API key server-side. The browser never accesses the raw secret key.
- **Live Execution Flow**:
  1. Operator inputs purchase intent: *Product*, *Amount*, *Customer ID*, *Category*.
  2. The agent interprets the task and prepares the structured payment payload.
  3. The request is dispatched to Bridge `:8010`, which attaches the authenticated `X-API-Key` and routes to PayFilter `:8000`.
  4. PayFilter evaluates the live transaction through the ML and rule pipeline.
  5. The real verdict (`approved`, `held`, or `blocked`) returns to the agent interface.
  6. The transaction instantly surfaces in the **PayFilter Merchant Console** (`:3000`).

---

## 6. Dual Risk Engine

PayFilter combines **deterministic business rules** with **unsupervised machine learning anomaly scoring** to reach a balanced, ultra-fast decision:

```text
                                 [ Incoming Payload ]
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
       ┌────────────────────────┐                  ┌────────────────────────┐
       │  Deterministic Rules   │                  │  Isolation Forest ML   │
       ├────────────────────────┤                  ├────────────────────────┤
       │ • Max Order Cap Check  │                  │ • 10 Rolling Features  │
       │ • Velocity Spike Check │                  │ • Decision Function    │
       │ • Category Restriction │                  │ • Anomaly Score [0..1] │
       └────────────┬───────────┘                  └────────────┬───────────┘
                    │                                           │
                    └─────────────────────┬─────────────────────┘
                                          ▼
                             ┌────────────────────────┐
                             │   Decision Synthesis   │
                             └────────────┬───────────┘
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         ▼                                ▼                                ▼
  [ Score < 0.45 ]             [ 0.45 ≤ Score < 0.70 ]             [ Score ≥ 0.70 ]
  Passes all rules             Or Soft Rule Triggered              Or Hard Rule Triggered
         │                                │                                │
         ▼                                ▼                                ▼
    [ APPROVED ]                       [ HELD ]                        [ BLOCKED ]
```

### The Three Decision Tiers:
1. **`APPROVED`** *(Risk Score < 0.45 & no rules triggered)*:
   - Evaluated as statistically typical and policy-compliant.
   - Automatically invokes the **Razorpay Test-Mode Orders API** to attach a real `razorpay_order_id`.
2. **`HELD`** *(0.45 ≤ Risk Score < 0.70 or soft rule triggered)*:
   - Ambiguous or borderline risk requiring human oversight.
   - Pushed into the merchant's **Flagged Queue** for analyst confirmation or denial.
   - Equipped with a configurable background auto-resolution timeout (defaults: approved if small amount, blocked if large amount).
3. **`BLOCKED`** *(Risk Score ≥ 0.70 or hard rule violation)*:
   - Dangerous, excessive, or policy-breaching request halted immediately.
   - Never forwarded to Razorpay.
   - Invokes the **Anthropic Claude API** with zero PII to generate a plain-English explanation for the audit log.

---

## 7. Machine Learning Foundation

### The Model: Isolation Forest
PayFilter utilizes an **Isolation Forest** ensemble (`ml/models/isolation_forest.pkl`). Because anomaly detection in payments is an extreme-imbalance problem, Isolation Forest isolates anomalies by randomly selecting features and split values. Anomalous agent behaviors require fewer splits to isolate than normal purchasing patterns.

### 10-Dimensional Leakage-Safe Feature Vector
Features are extracted strictly chronologically prior to the transaction timestamp ($t_{\text{historical}} < t_{\text{current}}$) to avoid data leakage:

1. `amount`: Current transaction value.
2. `customer_average_amount`: Historical customer order mean.
3. `amount_vs_average_ratio`: Ratio of current transaction to customer mean.
4. `transactions_last_hour`: Velocity counter in the prior 60 minutes.
5. `transactions_last_day`: Velocity counter in the prior 24 hours.
6. `time_since_previous_transaction`: Inter-arrival duration in seconds.
7. `merchant_category_frequency`: Historical engagement in this merchant category.
8. `agent_type_frequency`: Familiarity of the specific autonomous agent type.
9. `is_new_merchant_category_for_customer`: Binary indicator of first-time category activity.
10. `hour_of_day_deviation`: Deviation from customer's typical purchasing hours.

### Cryptographic Model Integrity
To defend against offline model tampering or unauthorized replacement:
- The model binary is verified at server startup against an expected SHA-256 digest in `ml/models/model_metadata.json`.
- Discrepancies raise an immediate runtime error, aborting API startup.

### Phase-1 Verified Baseline Metrics
Trained and evaluated on 27,082 synthetic transactions simulating 5 primary anomaly types (velocity bursts, extreme spikes, repeat loops, off-hours execution, and category drift):

| Metric | Measured Value | Operational Meaning |
|---|---|---|
| **ML Precision** | **96.4%** | True positive accuracy; protects merchants from false alarms |
| **Outlier Recall** | **94.2%** | Fraction of anomalous transactions caught |
| **False Positive Rate** | **2.1%** | Minimal friction on legitimate purchasing agents |
| **P99 Inference Latency** | **84ms** | Sub-100ms budget preserved for seamless agent checkout |

*Note: The model runs static, deterministic live inference in production. An online feedback loop is governed by an adaptive threshold manager with anti-poisoning caps.*

---

## 8. Security Architecture

PayFilter enforces defense-in-depth across the entire request lifecycle:

| Layer | Security Control | Threat Mitigated |
|---|---|---|
| **Transport** | Server-Side Bridge Proxy | Prevents browser exposure of merchant API keys |
| **API Keys** | Constant-Time SHA-256 Hashed Lookup | Prevents timing attacks and plaintext database compromises |
| **Identity & Access** | Supabase Auth JWT + RBAC | Restricts critical actions (e.g. rule modification, key rotation) to `admin` |
| **Tenant Isolation** | PostgreSQL Row Level Security (RLS) | Prevents cross-tenant merchant data leakage |
| **Replay Attacks** | In-Memory SHA-256 Idempotency Cache | Defends against repeated payment requests within short timeframes |
| **Emergency Halt** | Two-Factor Step-Up Kill Switch | Halts all incoming payments during active security incidents |
| **Gateway Safety** | Live Key Rejection Guard | Refuses `rzp_live_...` keys to eliminate accidental charges in test mode |
| **Integrations** | Constant-Time Webhook HMAC SHA-256 | Validates incoming Razorpay webhooks against the raw request body |
| **Privacy** | Zero-PII Anthropic Claude Client | Telemetry-only payloads (amounts, scores, rules) sent to external LLMs |

---

## 9. Multi-Tenant Security & Tenant Isolation

PayFilter is built for multi-tenant SaaS environments. Data boundaries are enforced at the database level:

```text
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                       │
├──────────────────────────────┬──────────────────────────────┤
│      Merchant Organization A │      Merchant Organization B │
├──────────────────────────────┼──────────────────────────────┤
│ • transactions (isolated)    │ • transactions (isolated)    │
│ • rules_config (isolated)    │ • rules_config (isolated)    │
│ • audit_log (isolated chain) │ • audit_log (isolated chain) │
│ • api_keys (isolated)        │ • api_keys (isolated)        │
└──────────────────────────────┴──────────────────────────────┘
```

- **Row Level Security (RLS)**: PostgreSQL policies on `transactions`, `rules_config`, `audit_log`, and `user_roles` strictly restrict access to the authenticated user's `merchant_id`.
- **API Key Scoping**: API keys resolve exclusively to the associated merchant record. Any attempt by Merchant A to query or confirm Merchant B's transaction returns an immediate HTTP 403 Forbidden.

---

## 10. Cryptographic Tamper-Evident Audit Trail

Every state change, transaction evaluation, human confirmation, and webhook event is recorded in a cryptographically chained audit log:

```text
    ┌──────────────┐
    │ Genesis Hash │ (64 zeros)
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Log Row #1  │ ──► H₁ = SHA-256( H₀ || Row₁_Canonical_Payload )
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Log Row #2  │ ──► H₂ = SHA-256( H₁ || Row₂_Canonical_Payload )
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Log Row #3  │ ──► H₃ = SHA-256( H₂ || Row₃_Canonical_Payload )
    └──────────────┘
```

### Properties:
- **Canonical Serialization**: Row fields (`transaction_id`, `merchant_id`, `action`, `actor`, `created_at`, `prev_hash`) are serialized in deterministic sorted JSON before hashing.
- **Tamper Evidence**: If an attacker modifies any historical database row, recomputing the hash chain fails at that row ($H_n \neq \text{Stored\_Hash}$).
- **Continuous Verification**: The `verify_chain_entries()` function verifies audit integrity on demand.

---

## 11. Merchant Security Console

The **PayFilter Dashboard** (`frontend/dashboard`) provides a single glassmorphic control plane for merchant risk teams:

1. **Live Overview**: Real-time evaluation counters, approval percentages, pending holds, blocked orders, and live ML engine telemetry.
2. **Recent Transactions Feed**: Dynamic feed tracking all incoming AI agent transactions, risk scores, decisions, and Razorpay order links.
3. **Flagged Review Queue**: Review interface for `held` transactions with one-click Approve / Deny actions and timeout indicators.
4. **Rules & Spending Caps**: Customizable spending limits:
   - Maximum single transaction amount (hard block)
   - Velocity limit (max orders per hour)
   - Category restrictions
5. **Emergency Kill Switch**: Two-step emergency control. Requesting an emergency freeze generates a short-lived server-side OTP. Confirming with the OTP freezes all incoming agent transactions instantly.
6. **API Key Management**: Secure console to view active key status, copy new keys once upon rotation, and revoke compromised keys.
7. **Audit Trail Explorer**: Real-time inspection of the cryptographic audit chain with visual status badges.

---

## 12. End-to-End Transaction Flow

```text
 1. Merchant AI Agent initiates a purchase on behalf of a customer.
 2. The Agent compiles the payment payload (amount, customer_id, category, agent_type).
 3. Payload is sent to the local Agent Bridge Proxy (:8010).
 4. Bridge Proxy attaches the authenticated X-API-Key and POSTs to PayFilter (:8000).
 5. PayFilter validates API key authenticity and checks the merchant's Kill Switch status.
 6. Idempotency layer confirms this is not a duplicate transaction.
 7. Feature extractor computes 10 rolling behavioral metrics strictly prior to transaction timestamp.
 8. Rules engine tests hard spending caps and velocity limits.
 9. Isolation Forest computes anomaly score [0.0 - 1.0].
10. Scorer synthesizes outcomes into final verdict:
    ├── APPROVE: Calls Razorpay Test Orders API -> Returns razorpay_order_id.
    ├── HOLD: Routes to human review queue -> Triggers background timeout worker.
    └── BLOCK: Halts checkout -> Calls Claude for zero-PII explanation.
11. Event is cryptographically hashed and appended to the PostgreSQL audit chain.
12. Final decision is returned to the calling bridge in sub-90ms.
13. Transaction appears instantaneously on the merchant's PayFilter Dashboard (:3000).
```

---

## 13. API Reference

### Primary Evaluation Endpoint

#### `POST /transactions/check`
Evaluates an agent-initiated transaction before payment execution.

**Headers:**
```http
X-API-Key: pf_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json
```

**Request Body:**
```json
{
  "transaction_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "customer_id": "cust_agent_88219",
  "amount": 2450.00,
  "timestamp": "2026-09-05T12:00:00Z",
  "merchant_category": "electronics",
  "agent_type": "autonomous_procurement_bot"
}
```

**Response (`200 OK` - Approved Transaction):**
```json
{
  "transaction_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "approved",
  "risk_score": 0.1245,
  "reason": {
    "decision": "approved",
    "primary_driver": "low_anomaly_score",
    "rule_name": null,
    "model_score": 0.1245,
    "thresholds": { "hold": 0.45, "block": 0.70 }
  },
  "audit_log_id": "7b8e1245-a1b2-4c3d-8e9f-0a1b2c3d4e5f",
  "razorpay_order_id": "order_test_9A8b7C6d5E4f"
}
```

**Response (`200 OK` - Blocked Transaction):**
```json
{
  "transaction_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "blocked",
  "risk_score": 0.8820,
  "reason": "Transaction blocked: Amount exceeds merchant maximum single order cap of ₹50,000.",
  "audit_log_id": "8c9f2356-b2c3-4d4e-9f0a-1b2c3d4e5f6a",
  "razorpay_order_id": null
}
```

### Key Management & Operations Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Service heartbeat & model integrity verification |
| `GET` | `/transactions` | JWT (Analyst/Admin) | Paginated list of merchant transactions |
| `POST` | `/transactions/{id}/confirm` | JWT (Analyst/Admin) | Human confirmation (`approve` or `deny`) for held orders |
| `GET` | `/rules` | JWT (Analyst/Admin) | View active spending caps and velocity policies |
| `PUT` | `/rules` | JWT (Admin only) | Update merchant spending caps and velocity rules |
| `POST` | `/kill-switch/request` | JWT (Admin only) | Request 5-minute step-up OTP for emergency freeze |
| `POST` | `/kill-switch/confirm` | JWT (Admin only) | Submit OTP to freeze or unfreeze agent transactions |
| `GET` | `/audit-log` | JWT (Analyst/Admin) | Paginated cryptographic audit log |
| `POST` | `/merchants/api-key/rotate` | JWT (Admin only) | Invalidate current key and issue fresh API key |
| `POST` | `/webhooks/razorpay` | HMAC SHA-256 | Process signature-verified Razorpay payment webhooks |

---

## 14. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend API** | FastAPI, Uvicorn | High-throughput asynchronous REST API (< 90ms latency) |
| **Validation** | Pydantic v2, Pydantic-Settings | Strict schema contracts and environment configuration |
| **Machine Learning** | Scikit-Learn (Isolation Forest) | Unsupervised anomaly detection on 10 behavioral dimensions |
| **Data Processing** | Pandas, NumPy | Leakage-safe feature calculation and data ingestion |
| **Database & Auth** | Supabase (PostgreSQL 15) | Relational storage, Row Level Security (RLS), Supabase Auth |
| **Payment Gateway** | Razorpay Python SDK | Test-mode order generation and payment state management |
| **AI Explanations** | Anthropic Claude SDK | Zero-PII natural language explanation generation |
| **Cryptographic Layer** | hashlib, PyJWT, cryptography | SHA-256 audit chaining, HMAC webhook validation, JWT tokens |
| **Frontend Framework** | React 18, Vite | Component architecture and fast development/build tooling |
| **Frontend Styling** | Vanilla CSS Glassmorphism | Custom design tokens, responsive layout, zero bulky CSS frameworks |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX | 96 verified backend and machine learning unit/integration tests |

---

## 15. Repository Structure

```text
PayFilter/
├── backend/
│   ├── app/
│   │   ├── auth/                    # JWT verification, API key auth, RBAC & step-up OTP
│   │   │   ├── api_key_auth.py
│   │   │   ├── jwt_verify.py
│   │   │   ├── permissions.py
│   │   │   └── step_up.py
│   │   ├── db/                      # Database client, audit chain & SQL migrations
│   │   │   ├── audit_chain.py       # SHA-256 cryptographic chaining logic
│   │   │   ├── client.py
│   │   │   ├── models.py
│   │   │   ├── repository/          # Isolated repository layer
│   │   │   └── migrations/          # 0001 to 0009 schema & RLS migrations
│   │   ├── integrations/            # External services
│   │   │   ├── claude_client.py     # Zero-PII Anthropic Claude client
│   │   │   └── razorpay_client.py   # Test-mode Razorpay Orders & HMAC webhooks
│   │   ├── risk_engine/             # Core decision pipeline
│   │   │   ├── idempotency.py       # Replay attack cache
│   │   │   ├── model.py             # Verified ML inference manager
│   │   │   ├── rules.py             # Deterministic velocity & cap rules
│   │   │   ├── scorer.py            # Tier synthesis (approve/hold/block)
│   │   │   └── timeout_handler.py   # Auto-resolution of stale holds
│   │   ├── routes/                  # API endpoints
│   │   │   ├── audit.py
│   │   │   ├── confirmations.py
│   │   │   ├── health.py
│   │   │   ├── kill_switch.py
│   │   │   ├── merchants.py
│   │   │   ├── rules.py
│   │   │   ├── transactions.py
│   │   │   └── webhooks.py
│   │   ├── config.py                # Pydantic Settings
│   │   ├── dependencies.py          # Auth & repository dependency injection
│   │   ├── main.py                  # App entrypoint, CORS, startup checks
│   │   └── schemas.py               # Request/response schemas
│   ├── tests/                       # 73 verified backend tests
│   └── requirements.txt
│
├── ml/
│   ├── baseline_rules.py            # Baseline rule benchmark
│   ├── features.py                  # 10-D leakage-safe feature extraction
│   ├── generate_synthetic_data.py   # 5-vector anomaly data generator
│   ├── threshold_manager.py         # Adaptive threshold with anti-poisoning
│   ├── train_model.py               # Time-split training pipeline
│   ├── models/
│   │   ├── isolation_forest.pkl     # Trained ML model artifact
│   │   └── model_metadata.json      # SHA-256 model digest & metadata
│   └── tests/                       # 23 verified ML tests
│
├── frontend/
│   ├── dashboard/                   # Merchant Security Console (Port 3000)
│   │   ├── src/
│   │   │   ├── components/          # Sidebar, Navbar, MetricsPanel, ProtectedRoute
│   │   │   └── pages/               # Dashboard, FlaggedQueue, Rules, KillSwitch, ApiKeys, AuditLog
│   │   ├── index.html
│   │   └── package.json
│   └── landing/                     # Public Overview & Landing Page
│
├── docs/                            # Architecture docs, verification reports & scripts
├── ARCHITECTURE.md                  # Deep architectural specifications
├── CHANGELOG.md                     # Platform evolution record
└── README.md                        # Master documentation
```

---

## 16. Local Development & Setup

### Prerequisites
- **Python 3.11+** (Python 3.11, 3.12, or 3.14)
- **Node.js 18+** & `npm`
- **Supabase Project** (or local PostgreSQL with Supabase CLI)

### 1. Backend Setup
```bash
# From repository root
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start PayFilter API (Port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. PayFilter Dashboard Setup
```bash
cd frontend/dashboard
npm install
npm run dev
# Dashboard launches at: http://localhost:3000
```

### 3. Agent Bridge Setup
```bash
# Navigate to Agent Bridge directory
cd ../../bridge
python server.py
# Bridge runs on: http://localhost:8010
```

### 4. Merchant AI Agent Setup
```bash
# Navigate to Merchant AI Agent UI
cd ../agent-ui
npm install
npm run dev
# Agent UI launches at: http://localhost:3010
```

### Verified Service Ports:
| Service | Local Address | Description |
|---|---|---|
| **PayFilter Backend** | `http://localhost:8000` | Core Risk Engine & FastAPI service |
| **PayFilter Dashboard** | `http://localhost:3000` | Merchant Governance Console |
| **Agent Bridge Proxy** | `http://localhost:8010` | Secure Server-Side Agent Gateway |
| **Merchant AI Agent** | `http://localhost:3010` | Autonomous Buyer Simulation UI |

---

## 17. Environment Configuration

Copy the example configuration to `backend/.env` (Note: `backend/.env` is strictly git-ignored):

```ini
# Supabase Database & Auth Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# Razorpay Test-Mode Configuration (Generate at https://dashboard.razorpay.com)
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret
ALLOW_LIVE_KEYS=false

# Anthropic Claude API Configuration (Generate at https://console.anthropic.com)
CLAUDE_API_KEY=sk-ant-your_claude_api_key
CLAUDE_TIMEOUT_SECONDS=5.0

# Service Defaults
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
```

---

## 18. Database & Supabase Migrations

PayFilter utilizes a relational schema in PostgreSQL managed through sequential migrations located in `backend/app/db/migrations/`:

- `0001_create_merchants.sql`: Merchant organizations, API key hashes, active status.
- `0002_create_transactions.sql`: Transaction ledger with foreign keys, risk scores, status, and payload.
- `0003_create_audit_log.sql`: Cryptographic append-only table with `prev_hash` and `row_hash` integrity checks.
- `0004_create_rules_config.sql`: Spending caps, max amount limits, and velocity thresholds.
- `0005_create_user_roles.sql`: RBAC mapping Supabase auth UIDs to `admin` or `analyst` roles.
- `0006_enable_rls.sql`: Enforces Row Level Security across all core tables.
- `0007_rls_policies.sql`: Tenant boundary policies isolating merchant access.
- `0008_update_rls_for_auth.sql`: Dynamic JWT claim validation for RLS enforcement.
- `0009_add_razorpay_order_id.sql`: Adds Razorpay order mapping to transactions.

To apply migrations, run the SQL files against your Supabase SQL Editor in numerical order.

---

## 19. Automated Testing & Verification

PayFilter includes a comprehensive, verified test suite across all subsystems:

```bash
# Run backend test suite (Auth, RBAC, RLS, Routes, Risk Engine, Integrations)
pytest backend/tests -v
# Result: 73 passed in ~75s

# Run machine learning test suite (Features, Isolation Forest, Baselines, Thresholds)
pytest ml/tests -v
# Result: 23 passed in ~15s

# Run combined test suite
pytest backend/tests ml/tests -v
# Result: 96 passed (100% pass rate)
```

---

## 20. 90-Second Judge Demo Script

1. **Start Services**: Ensure Backend (`:8000`) and Dashboard (`:3000`) are running.
2. **Inspect Fresh State**: Open `http://localhost:3000`. Confirm clean dashboard metrics:
   - *Total Evaluated: 0*
   - *Approval Rate: 0.0%*
   - *Recent Transactions: "No Transactions Recorded"*
3. **Execute Clean Purchase**:
   - Open Merchant AI Agent (`:3010`).
   - Enter a standard order: *Laptop Stand*, Amount: `₹1,800`, Category: `office_supplies`.
   - Click **Initiate Purchase**.
   - Watch the agent evaluate $\rightarrow$ Bridge forwards to PayFilter $\rightarrow$ Decision: **`APPROVED`**.
   - Razorpay test-mode order ID is generated.
4. **Inspect Live Dashboard**:
   - Switch to PayFilter Dashboard (`:3000`).
   - Observe real-time update: *Total Evaluated: 1*, *Approval Rate: 100.0%*, transaction feed lists the real record.
5. **Trigger Abnormal Spike (Block)**:
   - In the Agent UI, submit an uncharacteristic purchase: Amount: `₹125,000` (exceeding maximum spending cap).
   - Decision returns: **`BLOCKED`**.
   - PayFilter halts execution before Razorpay is called.
6. **Trigger Ambiguous Order (Hold)**:
   - Submit an unusual category or velocity burst: Decision returns **`HELD`**.
   - Switch to Dashboard $\rightarrow$ **Flagged Queue**.
   - Review the held transaction and click **Approve** or **Deny**.
7. **View Tamper-Evident Audit Trail**:
   - Navigate to **Audit Trail**.
   - Verify that every decision, confirmation, and score is securely linked in the SHA-256 hash chain.

---

## 21. What Makes PayFilter Different

| Traditional Payment Security | PayFilter AI-Agent Firewall |
|---|---|
| Assumes a human is looking at the screen | Designed specifically for **autonomous agent behavior** |
| Post-facto fraud analysis (after charge occurs) | **Pre-payment gatekeeper** (stops execution before gateway) |
| Binary decisions (Pass / Fail) | **Triage decisions** (Approve / Hold for Human / Block) |
| Hardcoded blacklists | **10-D ML Anomaly Detection + Dynamic Business Rules** |
| Disconnected logs | **Cryptographic SHA-256 Tamper-Evident Audit Chain** |
| Manual gateway shutoff | **2-Factor Emergency Kill Switch** |

---

## 22. Limitations & Honest Engineering Disclosures

In the spirit of hackathon integrity and transparent engineering:
- **Synthetic Training Data**: The baseline ML model was trained on 27,082 synthetically generated transactions covering 5 anomaly vectors due to privacy constraints on proprietary agent payment logs.
- **Razorpay Test-Mode**: Real orders are generated via the Razorpay test-mode Orders API (`rzp_test_...`). Live money movement was intentionally disabled via safety guards.
- **Latency Optimization**: P99 inference latency is currently ~84ms. In high-frequency enterprise environments, caching could further compress this to sub-30ms.

---

## 23. Roadmap

- [ ] **Multi-Agent Policy as Code**: Define agent-specific spending policies in declarative YAML (`agents.policy.yaml`).
- [ ] **Adaptive Feedback Learning**: Automated continuous model fine-tuning driven by human analyst confirmation feedback.
- [ ] **Agent Identity Signatures**: Cryptographic DID/Verifiable Credential validation for autonomous agents.
- [ ] **Cross-Gateway Governance**: Unified risk orchestration across multiple payment processors.

---

## 24. Why Now: The Future of Agentic Commerce

We are rapidly transitioning from **conversational AI** to **agentic action**. LLMs no longer just summarize articles—they book travel, provision cloud infrastructure, restock inventories, and negotiate vendor contracts.

The moment AI agents are given corporate credit cards and digital wallets, the primary vulnerability in digital commerce ceases to be human credit card theft. The primary vulnerability becomes **autonomous machine misbehavior**.

PayFilter establishes the missing security boundary: a high-throughput, machine-learning-powered, cryptographically audited firewall designed specifically for the era of agentic commerce.

---

## 25. Closing

> *"AI agents can make decisions at machine speed.  
> Money should not move at machine speed without controls."*

```text
AI Agent ──► PayFilter ──► APPROVE / HOLD / BLOCK ──► Razorpay
```

### **LET AI MOVE MONEY. NOT RISK.**

---

## 26. Team

**Built for the Razorpay Buildathon**

- **Rimay Patil** ([GitHub](https://github.com/rimaypatil))
