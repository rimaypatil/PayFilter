# PayFilter — AI Agent Transaction Risk Engine

PayFilter is an intelligent, real-time risk mitigation, anomaly detection, and cryptographic audit logging platform built for autonomous AI-agent-initiated transactions prior to Razorpay order creation.

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
├── backend/                         # Phase 2: Backend Risk Engine & Database
│   ├── app/
│   │   ├── main.py                  # FastAPI application entrypoint, CORS, lifespan
│   │   ├── config.py                # Environment configuration & settings
│   │   ├── schemas.py               # Pydantic request/response validation schemas
│   │   │
│   │   ├── routes/
│   │   │   ├── transactions.py      # POST /transactions/check
│   │   │   ├── audit.py             # GET /audit-log (paginated)
│   │   │   └── health.py            # GET /health
│   │   │
│   │   ├── risk_engine/
│   │   │   ├── rules.py             # Hard caps, category limits, & velocity checks
│   │   │   ├── model.py             # Verified ML inference with SHA-256 validation
│   │   │   ├── scorer.py            # Decision tier synthesizer (approve/hold/block)
│   │   │   └── idempotency.py       # Replay cache preventing duplicate processing
│   │   │
│   │   └── db/
│   │       ├── client.py            # Supabase Python client & test simulator
│   │       ├── models.py            # Pydantic models mirroring Postgres tables
│   │       ├── audit_chain.py       # SHA-256 hash chaining & verify_chain()
│   │       ├── repository/
│   │       │   ├── transactions_repo.py
│   │       │   ├── audit_repo.py    # Append-only audit repository
│   │       │   ├── merchants_repo.py
│   │       │   └── rules_repo.py
│   │       └── migrations/
│   │           ├── 0001_create_merchants.sql
│   │           ├── 0002_create_transactions.sql
│   │           ├── 0003_create_audit_log.sql
│   │           ├── 0004_create_rules_config.sql
│   │           ├── 0006_enable_rls.sql
│   │           ├── 0007_rls_policies.sql
│   │           └── seed_demo_data.sql
│   │
│   ├── tests/
│   │   ├── test_rules.py            # Deterministic rule evaluation tests
│   │   ├── test_scorer.py           # 3-tier scoring synthesis tests
│   │   ├── test_idempotency.py      # Duplicate request replay protection tests
│   │   ├── test_audit_chain.py      # Cryptographic tamper detection tests
│   │   ├── test_rls_isolation.py    # Multi-tenant DB isolation security tests
│   │   └── test_api.py              # FastAPI end-to-end integration tests
│   │
│   ├── requirements.txt             # Backend dependencies
│   └── .env.example                 # Environment variables template
│
├── features.py                      # Root proxy for ml.features
├── threshold_manager.py             # Root proxy for ml.threshold_manager
├── train_model.py                   # Root proxy for ml.train_model
├── demo_phase2_decisions.py         # End-to-end demo script for all 3 decision tiers
├── requirements.txt                 # Project-wide pinned dependencies
├── README.md                        # Documentation & setup guide
└── ARCHITECTURE.md                  # Comprehensive system & flow architecture
```

---

## 1. Backend Risk Engine Architecture (Phase 2)

The PayFilter backend combines deterministic business rules with machine learning anomaly detection to produce instant, machine-readable risk decisions on every AI-agent checkout attempt.

```text
Incoming Transaction (POST /transactions/check)
                     │
                     ▼
       ┌───────────────────────────┐
       │   1. Idempotency Check    │ ── (Duplicate Found) ──► Return Cached Decision
       └─────────────┬─────────────┘
                     │ (New Transaction)
                     ▼
       ┌───────────────────────────┐
       │ 2. Feature Extraction     │ ◄── Historical transactions (t_hist < t_curr)
       │    (Leakage-Safe)         │
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ 3. Deterministic Rules    │ ── (Hard Cap / Velocity Exceeded) ──► Block Decision
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ 4. IsolationForest Model  │ ──► Normalized Anomaly Score [0.0 - 1.0]
       │    (Verified SHA-256)     │
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ 5. Risk Scorer Decision   │ ──► Approve / Hold / Block Decision
       └─────────────┬─────────────┘
                     │
                     ├──────────────────────────┐
                     ▼                          ▼
       ┌───────────────────────────┐ ┌───────────────────────────────────┐
       │ 6. Write to DB            │ │ 7. Append to Cryptographic Audit │
       │    (transactions table)   │ │    (audit_log with SHA-256 chain) │
       └───────────────────────────┘ └───────────────────────────────────┘
                     │
                     ▼
        HTTP 200 JSON Response (status, risk_score, reason, audit_log_id)
```

### Risk Engine Components
* **Deterministic Rules (`rules.py`)**: Fast checks for merchant maximum order value, per-minute transaction velocity caps, and optional category limits.
* **Verified ML Model Inference (`model.py`)**: Evaluates the 10-dimensional feature vector using the Phase 1 Isolation Forest model. Verifies model binary hash integrity before inference.
* **Unified Risk Scorer (`scorer.py`)**: Synthesizes rule outputs and model anomaly scores against dynamic thresholds managed by `AdaptiveThresholdManager`.
  * `approved`: No rules triggered; anomaly score below hold threshold ($\text{score} < \theta_{\text{hold}}$).
  * `held`: Soft rule triggered OR anomaly score in medium-risk band ($\theta_{\text{hold}} \le \text{score} < \theta_{\text{block}}$).
  * `blocked`: Hard rule triggered OR anomaly score in high-risk band ($\text{score} \ge \theta_{\text{block}}$).
* **Idempotency Guard (`idempotency.py`)**: Identifies re-submitted `transaction_id` requests and returns the stored decision without duplicate scoring or writes.

---

## 2. Supabase Postgres Database Foundation

### Database Tables
1. **`merchants`**: Multi-tenant merchant identities (`id`, `name`, `api_key_hash`, `created_at`).
2. **`transactions`**: Scored transaction records with machine-readable reasons and risk scores (`id`, `merchant_id`, `customer_id`, `amount`, `agent_type`, `status`, `risk_score`, `reason`, `model_version`, `created_at`).
3. **`audit_log`**: Append-only cryptographic audit trail (`id`, `transaction_id`, `merchant_id`, `action`, `actor`, `prev_hash`, `row_hash`, `created_at`).
4. **`rules_config`**: Merchant-customizable risk rules (`merchant_id`, `max_amount_per_order`, `max_transactions_per_minute`, `category_limits`).

### Row-Level Security (RLS)
* Enabled and forced on all tenant tables (`transactions`, `audit_log`, `rules_config`, `merchants`).
* Scopes every query and mutation strictly to the caller's `merchant_id`.
* Proved and validated via `test_rls_isolation.py`.

### Append-Only Audit Log Enforcement
* `REVOKE UPDATE, DELETE, TRUNCATE` applied at the database role level.
* PostgreSQL trigger `trg_prevent_audit_log_mutation` raises an exception if any update or delete is attempted.

### Applying Migrations to Supabase

1. Open your [Supabase Dashboard](https://supabase.com/dashboard) and navigate to the **SQL Editor**.
2. Run the migration files in numerical order:
   * `backend/app/db/migrations/0001_create_merchants.sql`
   * `backend/app/db/migrations/0002_create_transactions.sql`
   * `backend/app/db/migrations/0003_create_audit_log.sql`
   * `backend/app/db/migrations/0004_create_rules_config.sql`
   * `backend/app/db/migrations/0006_enable_rls.sql`
   * `backend/app/db/migrations/0007_rls_policies.sql`
3. Optionally run `backend/app/db/migrations/seed_demo_data.sql` to populate demo merchants and rules.

---

## 3. Cryptographic Audit Chain

Each audit log write computes a SHA-256 digest over the record's payload concatenated with the previous record's `row_hash` for that merchant:

$$\text{row\_hash}_n = \text{SHA256}(\text{CanonicalJSON}(\text{payload}_n) \,\|\, \text{row\_hash}_{n-1})$$

The genesis record for a merchant links to `GENESIS_HASH = "0" * 64`.

The `verify_chain(merchant_id)` routine walks the complete historical audit log sequentially and re-computes every link. If any past record or hash is modified, verification immediately returns `False`.

---

## 4. API Endpoints

### 1. `POST /transactions/check`
Evaluates an incoming payment transaction and returns a risk verdict.

**Request Body:**
```json
{
  "transaction_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "merchant_id": "a0000000-0000-0000-0000-000000000001",
  "customer_id": "cust_12345",
  "amount": 250.00,
  "timestamp": "2026-08-30T12:00:00Z",
  "merchant_category": "electronics",
  "agent_type": "procurement_agent"
}
```

**Response (HTTP 200):**
```json
{
  "transaction_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "approved",
  "risk_score": 0.1245,
  "reason": {
    "decision": "approved",
    "primary_driver": "normal_baseline",
    "rule_name": null,
    "rule_type": null,
    "rule_reason": null,
    "model_score": 0.1245,
    "thresholds": {
      "hold": 0.45,
      "block": 0.70
    },
    "feature_drivers": []
  },
  "audit_log_id": "c1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c"
}
```

### 2. `GET /audit-log?merchant_id=<UUID>&page=1&page_size=50`
Retrieves paginated, immutable audit trail records for a merchant.

### 3. `GET /health`
Returns service health status and loaded model version.
```json
{
  "status": "ok",
  "model_version": "1.0.0",
  "model_loaded": true
}
```

---

## 5. Setup & Running Instructions

### Installation

```bash
# Clone and navigate to project root
cd PayFilter

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the project root (or `backend/.env`):

```bash
cp backend/.env.example .env
```

Populate `.env` with your Supabase credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_ANON_KEY=your-supabase-anon-key
```

*(If using default/mock settings, PayFilter automatically uses its built-in in-memory database simulator for local offline testing).*

### Running the FastAPI Server

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 6. Running Demonstration & Automated Tests

### Run Decision Tiers Demo Script
To demonstrate all three decision tiers (`approved`, `held`, `blocked`), idempotency replay, and audit chain verification:

```bash
python demo_phase2_decisions.py
```

### Run Complete Test Suite
Run the test suite across both Phase 2 backend and Phase 1 ML modules:

```bash
pytest backend/tests ml/tests
```

**Test Coverage Summary:**
* `backend/tests/test_rules.py`: Hard cap, category limit, and velocity rule triggers.
* `backend/tests/test_scorer.py`: Decision synthesis across all three tiers (approve, hold, block).
* `backend/tests/test_idempotency.py`: Replay protection and identical cached decision returns.
* `backend/tests/test_audit_chain.py`: Cryptographic hash chain creation and deliberate-tamper detection.
* `backend/tests/test_rls_isolation.py`: Cross-merchant multi-tenant database isolation.
* `backend/tests/test_api.py`: FastAPI end-to-end endpoint contracts and 422 input validation.
