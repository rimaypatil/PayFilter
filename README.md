# PayFilter — AI Agent Transaction Risk Engine & Auth Platform

PayFilter is an intelligent, real-time risk mitigation, anomaly detection, cryptographic audit logging, and human-in-the-loop confirmation platform designed for autonomous AI-agent-initiated payments before Razorpay order creation.

---

## Directory Structure

```text
payfilter/
├── ml/                              # Phase 1: ML Foundation & Data Generation
│   ├── generate_synthetic_data.py   # Synthetic transaction generator (5 anomaly vectors)
│   ├── features.py                  # Leakage-safe rolling feature extractor
│   ├── baseline_rules.py            # Deterministic heuristic baseline
│   ├── threshold_manager.py         # Adaptive threshold with poisoning defense
│   ├── train_model.py               # Time-split training with SHA-256 tamper checks
│   ├── evaluate.ipynb               # Evaluation & friction cost analysis
│   ├── data/
│   │   └── synthetic_transactions.csv
│   ├── models/
│   │   ├── isolation_forest.pkl     # Trained Isolation Forest model
│   │   └── model_metadata.json      # Cryptographic SHA-256 model hashes & metadata
│   └── tests/                       # Phase 1 unit and integrity test suite
│
├── backend/                         # Phases 2, 3, & 5: Backend Engine, Auth & Integrations
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint, lifespan integrity checks, CORS
│   │   ├── config.py                # Environment configuration, live-key safety check
│   │   ├── dependencies.py          # FastAPI dependencies (get_current_user, require_role, require_api_key)
│   │   ├── schemas.py               # Pydantic request/response validation schemas
│   │   │
│   │   ├── integrations/            # Phase 5: External Service Integrations
│   │   │   ├── razorpay_client.py   # Test-mode Orders API wrapper + HMAC webhook verification
│   │   │   └── claude_client.py     # Anthropic Claude API wrapper for zero-PII plain-English explanations
│   │   │
│   │   ├── auth/                    # Phase 3: Auth & Security Layer
│   │   │   ├── jwt_verify.py        # Supabase JWT signature, claims, and expiry verification
│   │   │   ├── api_key_auth.py      # Merchant API key verification (SHA-256 hashed lookup)
│   │   │   ├── permissions.py       # RBAC role checks (admin vs analyst)
│   │   │   └── step_up.py           # Short-lived server-side OTP flow for critical operations
│   │   │
│   │   ├── routes/
│   │   │   ├── health.py            # GET /health
│   │   │   ├── merchants.py         # POST /merchants/signup, POST /merchants/api-key/rotate
│   │   │   ├── transactions.py      # POST /transactions/check, GET /transactions
│   │   │   ├── confirmations.py     # POST /transactions/{id}/confirm
│   │   │   ├── kill_switch.py       # POST /kill-switch/request, POST /kill-switch/confirm
│   │   │   ├── rules.py             # GET /rules, PUT /rules (Admin JWT)
│   │   │   ├── audit.py             # GET /audit-log (Analyst/Admin JWT)
│   │   │   └── webhooks.py          # POST /webhooks/razorpay (HMAC verified)
│   │   │
│   │   ├── risk_engine/
│   │   │   ├── rules.py             # Hard caps, category limits, & velocity checks
│   │   │   ├── model.py             # Verified ML inference with SHA-256 validation
│   │   │   ├── scorer.py            # Decision tier synthesizer (approve/hold/block)
│   │   │   ├── idempotency.py       # Replay cache preventing duplicate processing
│   │   │   └── timeout_handler.py   # Scheduled auto-resolution for stale held transactions
│   │   │
│   │   └── db/
│   │       ├── client.py            # Supabase Python client & test simulator
│   │       ├── models.py            # Pydantic models (Merchant, UserRole, RulesConfig, etc.)
│   │       ├── audit_chain.py       # SHA-256 hash chaining & verify_chain()
│   │       ├── repository/          # Repository layer (merchants, transactions, rules, audit)
│   │       └── migrations/          # PostgreSQL migrations (0001 to 0009)
│   │
│   └── tests/                       # Complete backend unit, auth, integration & E2E test suites
│
├── frontend/                        # Phase 4: Frontend Applications
│   ├── landing/                     # Public Landing Page & Developer Docs (Vite + React)
│   └── dashboard/                   # Authenticated Merchant Console (Vite + React + Supabase Auth)
│
├── README.md                        # Setup guide & walkthrough
└── ARCHITECTURE.md                  # Comprehensive system & flow architecture
```

---

## 1. Quickstart & Local Setup

### Step 1: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 2: Environment Configuration (`.env`)
Create a `.env` file in the project root:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# Razorpay Test-Mode Configuration
# (Generate test keys at https://dashboard.razorpay.com/app/keys)
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_here
ALLOW_LIVE_KEYS=false

# Anthropic Claude API Configuration
# (Generate API key at https://console.anthropic.com/)
CLAUDE_API_KEY=sk-ant-your_claude_api_key
CLAUDE_TIMEOUT_SECONDS=5.0
```

### Step 3: Start the Backend Server
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 2. Phase 5 Integrations & Verification

### A. Razorpay Test-Mode Orders
- When a transaction is evaluated as `approved` by the risk engine (or approved by a human analyst in the confirmation workflow), PayFilter automatically invokes Razorpay's Orders API in **test mode**.
- The created `razorpay_order_id` (e.g. `order_test_abc123`) is stored in the database and returned in `TransactionCheckResponse`.

### B. Claude Plain-English Explanations
- When a transaction is flagged as `held` or `blocked`, PayFilter queries Claude to translate complex mathematical anomaly drivers and rule breaches into 1-2 plain-English sentences for risk analysts.
- **Data Minimization Guarantee**: No customer names, card numbers, street addresses, or personal identifiers are sent to Claude.

### C. Signature-Verified Webhooks (`POST /webhooks/razorpay`)
- Webhooks from Razorpay (such as `payment.captured` or `payment.failed`) are cryptographically verified using constant-time HMAC SHA-256 against the raw request body before JSON decoding.
- Processed webhook events are permanently recorded in the append-only cryptographic audit trail.

---

## 3. How to Reproduce the "Graceful Failure" Demo

A core design principle of PayFilter is **Failure Tolerance**: external API failures or network latency must never compromise or roll back a PayFilter risk decision.

1. **Simulate Claude API Outage**:
   - Set `CLAUDE_API_KEY=""` or an invalid token in `.env`.
   - Submit a blocked transaction (e.g. amount ₹100,000 exceeding order caps).
   - **Result**: The transaction is still successfully scored as `blocked` and recorded in the audit trail, and PayFilter automatically provides a clean deterministic fallback explanation (`Flagged by risk rules: ...`).
2. **Simulate Razorpay API Outage**:
   - Set an invalid `RAZORPAY_KEY_ID`.
   - Submit an approved transaction.
   - **Result**: The transaction's `approved` verdict is preserved, the order status remains pending, and an audit event (`action = "razorpay_order_creation_failed"`) is transparently appended to the audit log.

---

## 4. Running Full-Pipeline & Unit Tests

Run the complete, verified test suite across all 6 phases:

```bash
# Run the continuous 7-scenario full pipeline integration test
pytest backend/tests/test_full_pipeline.py -v

# Run the complete test suite (unit, auth, integration & E2E)
pytest backend/tests ml/tests -v
```

---

## 5. Documentation & Submission Index

- [**System & Security Architecture**](file:///c:/Users/rimay/Desktop/PayFilter/ARCHITECTURE.md): Comprehensive end-to-end pipeline diagrams, data flows, and security model.
- [**Security Verification & Audit Report**](file:///c:/Users/rimay/Desktop/PayFilter/docs/SECURITY_VERIFICATION.md): Line-by-line verification evidence for all security requirements & dependency audits.
- [**Video Demo Script**](file:///c:/Users/rimay/Desktop/PayFilter/docs/demo-script.md): Step-by-step reproducible script for video demonstration and judging.
- [**Judge One-Pager Summary**](file:///c:/Users/rimay/Desktop/PayFilter/docs/one-pager.md): Single-page executive summary covering problem, architecture, metrics, and value proposition.
- [**Changelog**](file:///c:/Users/rimay/Desktop/PayFilter/CHANGELOG.md): Complete phase-by-phase platform evolution history.

