# PayFilter — Changelog

All notable changes to the PayFilter platform are documented in this file.

---

## [Phase 6] — Hardening, End-to-End Verification & Demo Readiness (2026-09-02)

### Added
- **Full-Pipeline Integration Test Suite** (`backend/tests/test_full_pipeline.py`): Comprehensive 7-scenario suite verifying clean approval, hard blocking, human analyst confirmation, background timeout auto-resolution, graceful Claude failure fallback, active kill switch enforcement, and full-stack tenant isolation.
- **Security Verification Matrix** (`docs/SECURITY_VERIFICATION.md`): Line-by-line evidence mapping every security claim (Auth, RLS, SHA-256 Chaining, Kill Switch, Zero-PII, HMAC Webhooks) to passing automated test proofs and clean dependency audits (`pip-audit`, `npm audit`).
- **Demo Script** (`docs/demo-script.md`): Step-by-step reproducible script for live video demonstrations.
- **Judge One-Pager** (`docs/one-pager.md`): Single-page executive summary covering the core problem, 5 architectural pillars, and ML performance metrics.

### Changed
- **Seed Demo Data** (`backend/app/db/migrations/seed_demo_data.sql`): Primed named customer history rows (`cust_demo_normal`, `cust_demo_burst`, `cust_demo_borderline`) matching the demo script.
- **Documentation**: Finalized `README.md` and `ARCHITECTURE.md` as unified single sources of truth.

---

## [Phase 5] — Razorpay & Claude Integrations (2026-09-02)

### Added
- **Razorpay Orders Integration** (`backend/app/integrations/razorpay_client.py`): Test-mode Orders API integration generating real order references on approved transactions.
- **Claude Plain-English Explanations** (`backend/app/integrations/claude_client.py`): Zero-PII natural language explanations for held and blocked transactions with a 5-second timeout and deterministic fallback.
- **Signature-Verified Webhook Router** (`backend/app/routes/webhooks.py`): `POST /webhooks/razorpay` validating HMAC SHA-256 against raw request bytes before JSON decoding.
- **Live Key Safety Guard** (`backend/app/config.py`): Rejects `rzp_live_...` production keys unless explicit `ALLOW_LIVE_KEYS=true` is set.

---

## [Phase 4] — Frontend Applications (2026-09-02)

### Added
- **Public Landing Page** (`frontend/landing/`): Built with React 18 & Vite, featuring interactive architecture flows, 3-tier decision matrix guide, developer API documentation, and merchant onboarding with single-reveal API key display.
- **Authenticated Dashboard** (`frontend/dashboard/`): Real-time live transaction feed, ML telemetry panel, analyst flagged review queue with instant Approve/Deny buttons, cryptographic audit trail explorer, admin rules editor, and two-factor step-up emergency kill switch.

---

## [Phase 3] — Supabase Auth, Confirmation Workflow & Kill Switch (2026-09-01)

### Added
- **Supabase Auth & RBAC** (`backend/app/auth/`): JWT signature verification, merchant API key SHA-256 hashed lookup, and role boundaries (`admin` vs `analyst`).
- **Human Confirmation Workflow** (`backend/app/routes/confirmations.py`): `POST /transactions/{id}/confirm` allowing analysts to approve or deny held transactions.
- **Step-Up Two-Factor Kill Switch** (`backend/app/routes/kill_switch.py`): Short-lived OTP generation and verification for emergency payment freezes.
- **Background Timeout Resolver** (`backend/app/risk_engine/timeout_handler.py`): Safe default auto-resolution for unreviewed held transactions.

---

## [Phase 2] — Backend Risk Engine & Database Foundation (2026-09-01)

### Added
- **FastAPI Backend Service** (`backend/app/main.py`, `backend/app/routes/transactions.py`): Sub-100ms risk assessment endpoint `POST /transactions/check`.
- **Append-Only SHA-256 Audit Chaining** (`backend/app/db/audit_chain.py`): Immutable cryptographic hash-chaining in PostgreSQL.
- **Multi-Tenant PostgreSQL Schema** (`backend/app/db/migrations/`): RLS-protected tables for merchants, transactions, audit logs, and rules configs.
- **Idempotency Replay Cache** (`backend/app/risk_engine/idempotency.py`): Prevents duplicate transaction evaluations.

---

## [Phase 1] — Machine Learning Foundation (2026-09-01)

### Added
- **Synthetic Data Generator** (`ml/generate_synthetic_data.py`): Generated 10,000+ realistic transactions with 5 anomaly vectors (burst velocity, ticket spikes, novel categories, off-peak hours, drift).
- **Leakage-Safe Feature Extractor** (`ml/features.py`): Rolling feature computations strictly prior to transaction timestamp.
- **Isolation Forest Model** (`ml/train_model.py`): Trained unsupervised anomaly detection model with SHA-256 tamper-evident integrity checks.
- **Adaptive Threshold Manager** (`ml/threshold_manager.py`): Dynamic threshold adjustment with bounded 10% drift cap to prevent poisoning attacks.
