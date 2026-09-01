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
├── backend/                         # Phase 2 & Phase 3: Backend Risk Engine & Auth
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint, lifespan integrity checks, CORS
│   │   ├── config.py                # Environment configuration & settings
│   │   ├── dependencies.py          # FastAPI dependencies (get_current_user, require_role, require_api_key)
│   │   ├── schemas.py               # Pydantic request/response validation schemas
│   │   │
│   │   ├── auth/                    # Phase 3 Auth & Security Layer
│   │   │   ├── jwt_verify.py        # Supabase JWT signature, claims, and expiry verification
│   │   │   ├── api_key_auth.py      # Merchant API key verification (SHA-256 hashed lookup)
│   │   │   ├── permissions.py       # RBAC role checks (admin vs analyst)
│   │   │   └── step_up.py           # Short-lived server-side OTP flow for critical operations
│   │   │
│   │   ├── routes/
│   │   │   ├── health.py            # GET /health
│   │   │   ├── merchants.py         # POST /merchants/signup, POST /merchants/api-key/rotate
│   │   │   ├── transactions.py      # POST /transactions/check (Requires X-API-Key)
│   │   │   ├── confirmations.py     # POST /transactions/{id}/confirm (Analyst/Admin JWT)
│   │   │   ├── kill_switch.py       # POST /kill-switch/request, POST /kill-switch/confirm
│   │   │   ├── rules.py             # GET /rules, PUT /rules (Admin JWT)
│   │   │   └── audit.py             # GET /audit-log (Analyst/Admin JWT)
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
│   │       ├── repository/
│   │       │   ├── merchants_repo.py    # Merchant accounts, key rotation & user roles
│   │       │   ├── transactions_repo.py # Transaction CRUD & timeout query
│   │       │   ├── rules_repo.py        # Merchant limits & rule management
│   │       │   └── audit_repo.py        # Append-only cryptographic audit trail
│   │       └── migrations/
│   │           ├── 0001_create_merchants.sql
│   │           ├── 0002_create_transactions.sql
│   │           ├── 0003_create_audit_log.sql
│   │           ├── 0004_create_rules_config.sql
│   │           ├── 0005_create_user_roles.sql    # Phase 3 RBAC schema
│   │           ├── 0006_enable_rls.sql
│   │           ├── 0007_rls_policies.sql
│   │           ├── 0008_update_rls_for_auth.sql  # Phase 3 auth.uid()-based RLS policies
│   │           └── seed_demo_data.sql
│   │
│   ├── tests/
│   │   ├── test_auth.py             # JWT signature, expiry & API key verification tests
│   │   ├── test_permissions.py      # RBAC role authorization tests (admin vs analyst)
│   │   ├── test_confirmations.py    # Human approval/denial & threshold adaptation tests
│   │   ├── test_kill_switch.py      # Step-up OTP & emergency kill switch tests
│   │   ├── test_timeout_handler.py  # Stale hold safe auto-resolution tests
│   │   ├── test_rls_with_auth.py    # Multi-tenant isolation with real JWT user sessions
│   │   ├── test_rules.py            # Deterministic rule evaluation tests
│   │   ├── test_scorer.py           # 3-tier scoring synthesis tests
│   │   ├── test_idempotency.py      # Duplicate request replay protection tests
│   │   ├── test_audit_chain.py      # Cryptographic tamper detection tests
│   │   └── test_api.py              # FastAPI end-to-end integration tests
│   │
│   ├── requirements.txt             # Backend dependencies
│   └── .env.example                 # Environment variables template
│
├── demo_phase3_workflow.py          # Complete Phase 3 end-to-end demonstration script
├── requirements.txt                 # Project-wide pinned dependencies
├── README.md                        # Documentation & setup guide
└── ARCHITECTURE.md                  # Comprehensive system & flow architecture
```

---

## 1. Authentication & Authorization (Phase 3)

### Supabase JWT Verification (`jwt_verify.py`)
- Every human-facing route (`/confirmations`, `/rules`, `/kill-switch`, `/audit-log`) requires an `Authorization: Bearer <token>` header.
- Validates the token's cryptographic signature, expiry (`exp`), audience (`authenticated`), and user identity claims.
- Rejects expired or forged tokens with HTTP 401 Unauthorized.

### Merchant Backend API Keys (`api_key_auth.py`)
- Used by merchant backend services when calling `POST /transactions/check`.
- API keys follow the prefix format `pf_live_<32-byte-secure-token>`.
- Plaintext keys are **never stored or logged** — only their SHA-256 digests are stored in Postgres.
- Evaluates the caller's key hash and automatically scopes the evaluation context to the verified `merchant_id`.

### Role-Based Access Control (RBAC) (`permissions.py`)
| Role | Privileges |
| :--- | :--- |
| **`analyst`** | View transactions, view audit log, review and confirm held transactions (`approve`/`deny`). |
| **`admin`** | All analyst capabilities + edit rules configuration (`PUT /rules`), rotate API keys (`POST /merchants/api-key/rotate`), and execute emergency kill switch (`POST /kill-switch/confirm`). |

---

## 2. Human Confirmation & Timeout Workflow

```text
                ┌──────────────────────────────────────┐
                │   Transaction Scored: Status 'held'  │
                └──────────────────┬───────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
       [Human Review]                            [Timeout Reached]
              │                                         │
              ▼                                         ▼
   Analyst/Admin Decision                  TimeoutHandler Evaluation
 (POST /transactions/{id}/confirm)             (Default: 120s)
              │                                         │
     ┌────────┴────────┐                       ┌────────┴────────┐
     ▼                 ▼                       ▼                 ▼
 'approve'          'deny'              Amount > 25,000    Amount <= 25,000
     │                 │                       │                 │
     ▼                 ▼                       ▼                 ▼
'approved'         'blocked'               'blocked'         'approved'
     │                 │                (Safe Default)    (Low-Risk Default)
     └────────┬────────┘                       │                 │
              │                                └────────┬────────┘
              ▼                                         ▼
   Audit Trail Appended                      Audit Trail Appended
 (action="confirmed_by_human")             (action="auto_resolved_timeout")
              │                                         │
              ▼                                         ▼
   Adaptive Threshold Updated               Database Status Persisted
```

### 1. Human Confirmation Route (`POST /transactions/{id}/confirm`)
- Analyst submits `{"decision": "approve" | "deny"}`.
- Enforces that the transaction belongs to the caller's merchant and is currently in `held` status.
- Updates database status to `approved` or `blocked`.
- Appends cryptographic audit entry with `action="confirmed_by_human"`.
- Adjusts the customer's risk baseline via Phase 1 `AdaptiveThresholdManager` (strictly adhering to the 10% drift cap).

### 2. Background Timeout Handler (`timeout_handler.py`)
- Scans for unreviewed held transactions older than `HELD_TIMEOUT_SECONDS` (default: 120s).
- **High-value holds ($> 25,000$)**: Resolves safely to `blocked` (preventing silent high-value exposure).
- **Standard holds ($\le 25,000$)**: Resolves safely to `approved` (preventing low-risk orders from stalling).
- Appends cryptographic audit log with `action="auto_resolved_timeout"`, `actor="system_timeout"`.

---

## 3. Step-Up Authenticated Emergency Kill Switch

To protect merchants against compromised API keys or runaway agents, PayFilter includes an emergency kill switch requiring two-factor step-up verification:

1. **Step-Up Request (`POST /kill-switch/request`)**:
   - Requires authenticated `admin` JWT session.
   - Generates a short-lived (5-minute) 6-digit numeric OTP stored server-side.
2. **Step-Up Execution (`POST /kill-switch/confirm`)**:
   - Requires both active `admin` session AND valid one-time OTP code.
   - Sets merchant kill switch state to `active`.
   - Appends audit entry `kill_switch_activated`.
3. **Instant Risk Engine Enforcement**:
   - While kill switch is active, all incoming `POST /transactions/check` requests for that merchant are instantly blocked with risk score `1.0` and primary driver `kill_switch_activated`.

---

## 4. API Endpoints Reference

### Public & Management Endpoints
* `GET /health`: Service health check.
* `POST /merchants/signup`: Register merchant organization, hashes API key, links initial admin user.

### Merchant Backend Route (Pre-Order)
* `POST /transactions/check` *(Requires `X-API-Key`)*: Real-time risk evaluation and anomaly scoring.

### Dashboard & Human-in-the-Loop Routes *(Requires `Authorization: Bearer <JWT>`)*
* `POST /transactions/{id}/confirm`: Approve or deny a held transaction.
* `POST /kill-switch/request`: Request step-up OTP for kill switch.
* `POST /kill-switch/confirm`: Confirm kill switch activation/deactivation with OTP.
* `GET /kill-switch/status`: Query merchant kill switch state.
* `GET /rules`: Retrieve merchant risk caps and category limits.
* `PUT /rules` *(Admin only)*: Update merchant risk caps.
* `POST /merchants/api-key/rotate` *(Admin only)*: Rotate API key and invalidate old hash.
* `GET /audit-log`: Paginated, merchant-isolated cryptographic audit trail.

---

## 5. Setup & Running Instructions

### Installation

```bash
# Clone repository
cd PayFilter

# Install dependencies
pip install -r backend/requirements.txt
```

### Environment Variables (`.env`)

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
HELD_TIMEOUT_SECONDS=120
LARGE_AMOUNT_THRESHOLD=25000.0
```

### Run Live Phase 3 Demonstration

Run the automated demonstration script to see all Phase 3 flows in action:

```bash
python demo_phase3_workflow.py
```

### Run Full Test Suite

```bash
pytest backend/tests ml/tests
```
