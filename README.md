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
├── backend/                         # Phase 2 & 3: Backend Risk Engine & Auth
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
│   │   │   ├── transactions.py      # POST /transactions/check, GET /transactions
│   │   │   ├── confirmations.py     # POST /transactions/{id}/confirm
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
│   │       ├── repository/          # Repository layer (merchants, transactions, rules, audit)
│   │       └── migrations/          # PostgreSQL migrations (0001 to 0008)
│   │
│   └── tests/                       # Complete backend unit and integration test suite
│
├── frontend/                        # Phase 4: Frontend Applications
│   ├── landing/                     # Public Landing Page & Developer Docs (Vite + React)
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   │   ├── Home.jsx         # Value proposition, architecture flow diagram & stats
│   │   │   │   ├── HowItWorks.jsx   # Plain-language 3-tier decision & anomaly vector guide
│   │   │   │   ├── Docs.jsx         # Developer API integration guide (cURL & Python SDK)
│   │   │   │   └── SignUp.jsx       # Merchant onboarding & single-reveal API key display
│   │   │   ├── components/          # Navbar, Footer
│   │   │   └── App.jsx
│   │   └── package.json
│   │
│   └── dashboard/                   # Authenticated Merchant Console (Vite + React + Supabase Auth)
│       ├── src/
│       │   ├── pages/
│       │   │   ├── Login.jsx        # Supabase Auth email/password login
│       │   │   ├── Dashboard.jsx    # Real-time transaction feed + MetricsPanel telemetry
│       │   │   ├── FlaggedQueue.jsx # Held transactions queue with live Approve/Deny buttons
│       │   │   ├── AuditLog.jsx     # Read-only paginated cryptographic audit trail explorer
│       │   │   ├── RulesSettings.jsx# Admin-only rules editor (max order caps & category limits)
│       │   │   └── KillSwitch.jsx   # Admin-only 2-factor step-up emergency kill switch
│       │   ├── components/          # ProtectedRoute, RoleGate, RiskBadge, TransactionCard, MetricsPanel
│       │   ├── lib/                 # supabaseClient.js, api.js, useAuth.jsx
│       │   └── App.jsx
│       └── package.json
│
├── demo_phase3_workflow.py          # End-to-end backend workflow validation script
├── README.md                        # Documentation & setup guide
└── ARCHITECTURE.md                  # Comprehensive system & flow architecture
```

---

## 1. Quickstart & Local Setup

### Step 1: Backend Setup
```bash
# Clone and enter project directory
cd PayFilter

# Install Python dependencies
pip install -r backend/requirements.txt

# Start FastAPI backend server (Runs on port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Public Landing Page Setup (`frontend/landing`)
```bash
cd frontend/landing
npm install
npm run dev # Starts on http://localhost:3000
```

### Step 3: Merchant Dashboard Setup (`frontend/dashboard`)
```bash
cd frontend/dashboard
npm install
npm run dev # Starts on http://localhost:3001
```

---

## 2. Environment Variables

### Backend `.env`
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
HELD_TIMEOUT_SECONDS=120
LARGE_AMOUNT_THRESHOLD=25000.0
```

### Dashboard `.env` (`frontend/dashboard/.env`)
```env
VITE_BACKEND_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

---

## 3. Manual End-to-End Walkthrough Checklist

1. **Merchant Onboarding**:
   - Open Landing Page at `http://localhost:3000/signup`.
   - Enter organization name (e.g., "Acme Procurement").
   - Click **Generate API Key & Register**.
   - Copy the one-time revealed API key (`pf_live_...`).
2. **Dashboard Login**:
   - Navigate to Dashboard at `http://localhost:3001/login`.
   - Sign in using your Supabase Auth user credentials (or 1-click demo button).
   - Verify that unauthenticated visits to `/` or `/queue` redirect to `/login`.
3. **Live Transaction Feed**:
   - View recent transactions and real-time ML performance telemetry on `Dashboard.jsx`.
4. **Human Review Queue**:
   - Open `Flagged Queue` at `http://localhost:3001/queue`.
   - Locate a `held` transaction card.
   - Click **Approve** or **Deny**.
   - Observe the card update/leave the queue immediately without requiring a page refresh.
5. **Cryptographic Audit Explorer**:
   - Open `Audit Trail` at `http://localhost:3001/audit`.
   - Verify the confirmed action is recorded with a verified SHA-256 row hash.
6. **Rules Configuration (Admin Only)**:
   - Switch role to `Admin` and navigate to `http://localhost:3001/rules`.
   - Update the Max Amount per Order cap and click **Save Rules Configuration**.
   - Switch role to `Analyst` and verify the edit controls are gated.
7. **Emergency Kill Switch Flow**:
   - Navigate to `http://localhost:3001/kill-switch` as an Admin.
   - Click **Freeze All Agent Payments** -> receive short-lived 6-digit OTP.
   - Enter the OTP code and confirm freeze.
   - Observe status flip to **ACTIVE (ALL PAYMENTS FROZEN)**.
   - Any subsequent `POST /transactions/check` request is now immediately blocked by the risk engine.

---

## 4. Testing

Run all backend unit and integration test suites:
```bash
pytest backend/tests ml/tests
```
