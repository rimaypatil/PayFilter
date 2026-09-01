# PayFilter Architecture Specification (Phase 1, Phase 2 & Phase 3)

## 1. System Overview

PayFilter sits as a real-time risk assessment, anomaly detection, and human-in-the-loop decision platform between autonomous AI agents and the Razorpay Order Creation API.

```text
+---------------------+      +-----------------------------------------+      +-----------------------+
|  AI Agent / Client  | ---> |          PayFilter Backend              | ---> |  Razorpay Order API   |
| (Autonomous Action) |      | (FastAPI + Rules + ML + Audit Chain)    |      | (Phase 5 Integration) |
+---------------------+      +-----------------------------------------+      +-----------------------+
                                   ▲                     ▲
                                   │ X-API-Key           │ JWT Auth & RBAC
                                   │ (Merchant Backend)  │ (Dashboard / Analysts)
                             +-------------------+  +-------------------+
                             | Merchant Platform |  | Analyst Dashboard |
                             |    (Autonomous)   |  | (Human-in-Loop)   |
                             +-------------------+  +-------------------+
                                                  │
                                                  ▼
                                     +-------------------------+
                                     |   Supabase PostgreSQL   |
                                     | (RLS + Append-Only Log) |
                                     +-------------------------+
```

---

## 2. End-to-End Decision, Confirmation & Kill Switch Lifecycle

```text
                               POST /transactions/check
                                (Requires X-API-Key)
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │   Verify Merchant API Key Hash  │
                         └────────────────┬────────────────┘
                                          │ Valid
                                          ▼
                         ┌─────────────────────────────────┐
                         │   Check Kill Switch Status      │ ── (Active) ──► Instant Block (1.0)
                         └────────────────┬────────────────┘
                                          │ Normal
                                          ▼
                         ┌─────────────────────────────────┐
                         │      Idempotency Check          │ ── (Duplicate) ──► Return Cached
                         └────────────────┬────────────────┘
                                          │ New
                                          ▼
                         ┌─────────────────────────────────┐
                         │   Feature Extraction (10-D)     │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │   Deterministic Rules & Limits  │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │   Verified ML Isolation Forest  │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │      Unified Risk Scorer        │
                         └────────────────┬────────────────┘
                                          │
               ┌──────────────────────────┼──────────────────────────┐
               ▼                          ▼                          ▼
          'approved'                   'held'                    'blocked'
               │                          │                          │
               │                          ▼                          │
               │             ┌─────────────────────────┐             │
               │             │  Human or Timeout Path  │             │
               │             └────────────┬────────────┘             │
               │                          │                          │
               │         ┌────────────────┴────────────────┐         │
               │         ▼                                 ▼         │
               │   Human Confirm                    Timeout Handler  │
               │   (Analyst JWT)                     (Older > 120s)  │
               │         │                                 │         │
               │    ┌────┴────┐                       ┌────┴────┐    │
               │    ▼         ▼                       ▼         ▼    │
               │ Approve     Deny                   > 25k    <= 25k  │
               │    │         │                       │         │    │
               │    ▼         ▼                       ▼         ▼    │
               │ 'approved' 'blocked'             'blocked' 'approved'
               │    │         │                       │         │    │
               └───┬┴─────────┴───────────────────────┴─────────┴────┘
                   │
                   ▼
        ┌────────────────────────────────────┐
        │  Append Cryptographic Audit Entry  │
        │    (SHA-256 Chained Hash Log)      │
        └──────────────────┬─────────────────┘
                           │
                           ▼
                 HTTP 200 Final Response
```

---

## 3. Database Schema & RLS Security

### 3.1 Relational Schema

```text
+-------------------------------------------------------+
|                       merchants                       |
+-------------------------------------------------------+
| id            : UUID (PK, gen_random_uuid())          |
| name          : TEXT                                  |
| api_key_hash  : TEXT                                  |
| created_at    : TIMESTAMPTZ                           |
+-------------------------------------------------------+
          │                        │                 │
          │ 1:N                    │ 1:N             │ 1:1
          ▼                        ▼                 ▼
+-------------------+    +-------------------+ +---------------------+
|    user_roles     |    |   transactions    | |    rules_config     |
+-------------------+    +-------------------+ +---------------------+
| user_id (PK, FK)  |    | id (PK)           | | merchant_id (PK, FK)|
| merchant_id (FK)  |    | merchant_id (FK)  | | max_amount_per_order|
| role ('admin'/    |    | customer_id       | | max_txns_per_minute |
|       'analyst')  |    | amount            | | category_limits     |
| created_at        |    | status ('approved'| | created_at          |
+-------------------+    |        /'held'/   | | updated_at          |
                         |        'blocked') | +---------------------+
                         | risk_score        |
                         | reason (JSONB)    |
                         | model_version     |
                         | created_at        |
                         +-------------------+
                                   │
                                   ▼ 1:N
                         +-------------------+
                         |     audit_log     |
                         +-------------------+
                         | id (PK)           |
                         | transaction_id    |
                         | merchant_id (FK)  |
                         | action            |
                         | actor (UUID/'sys')|
                         | prev_hash         |
                         | row_hash          |
                         | created_at        |
                         +-------------------+
```

### 3.2 Row-Level Security (RLS) with Supabase Auth
Postgres RLS policies enforce tenant isolation via `auth.uid()` mapped through `user_roles`:
```sql
CREATE POLICY auth_transactions_select ON transactions
    FOR SELECT TO authenticated
    USING (merchant_id = (SELECT merchant_id FROM user_roles WHERE user_id = auth.uid()));
```

---

## 4. Emergency Kill Switch Step-Up Architecture

```text
1. Admin Requests Step-Up OTP
   Admin ──► POST /kill-switch/request (Bearer JWT) ──► Backend generates 6-digit OTP (5m expiry)

2. Admin Confirms Kill Switch
   Admin ──► POST /kill-switch/confirm (Bearer JWT + OTP) ──► Backend validates OTP & activates kill switch

3. Automatic Risk Engine Enforcement
   Merchant ──► POST /transactions/check (X-API-Key) ──► Evaluator checks kill switch -> Returns status 'blocked'
```
