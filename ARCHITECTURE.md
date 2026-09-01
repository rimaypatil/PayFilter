# PayFilter Architecture Specification (Phase 1 & Phase 2)

## 1. System Overview

PayFilter is a high-throughput, low-latency transaction risk evaluation layer positioned between AI agent checkout requests and the Razorpay Order Creation API.

```text
+---------------------+      +-----------------------------------------+      +-----------------------+
|  AI Agent / Client  | ---> |          PayFilter Backend              | ---> |  Razorpay Order API   |
| (Autonomous Action) |      | (FastAPI + Rules + ML + Audit Chain)    |      | (Phase 3 Integration) |
+---------------------+      +-----------------------------------------+      +-----------------------+
                                                  |
                                                  v
                                     +-------------------------+
                                     |   Supabase PostgreSQL   |
                                     | (RLS + Append-Only Log) |
                                     +-------------------------+
```

---

## 2. End-to-End Backend Request Lifecycle (Phase 2)

```text
                    POST /transactions/check
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │       schemas.py Input Validation    │
            │   (Positive amount, forbid extra)    │
            └──────────────────┬───────────────────┘
                               │ Valid
                               ▼
            ┌──────────────────────────────────────┐
            │        idempotency.py Check          │
            └──────────────────┬───────────────────┘
                               │
                ┌──────────────┴──────────────┐
       [Found Duplicate]              [New Transaction]
                │                             │
                ▼                             ▼
     Return Cached Decision       ┌────────────────────────┐
                                  │   transactions_repo    │
                                  │ (Fetch past customer   │
                                  │  history t_hist < t)   │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │      features.py       │
                                  │ (Leakage-safe 10-D     │
                                  │  feature vector)       │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │        rules.py        │
                                  │ (Hard caps, velocity,  │
                                  │  category limits)      │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │        model.py        │
                                  │ (IsolationForest score │
                                  │  with verified SHA256) │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │       scorer.py        │
                                  │ (Synthesize rules +    │
                                  │  adaptive thresholds)  │
                                  └───────────┬────────────┘
                                              │
                        ┌─────────────────────┴─────────────────────┐
                        ▼                                           ▼
            ┌────────────────────────┐                  ┌────────────────────────┐
            │   transactions_repo    │                  │       audit_repo       │
            │  (INSERT transaction)  │                  │  (INSERT append-only   │
            │                        │                  │   SHA-256 hash chain)  │
            └───────────┬────────────┘                  └───────────┬────────────┘
                        │                                           │
                        └─────────────────────┬─────────────────────┘
                                              ▼
                                    HTTP 200 Response
```

---

## 3. Database Architecture & Multi-Tenant Isolation

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
                           │
       ┌───────────────────┼───────────────────┐
       │ 1:N               │ 1:N               │ 1:1
       ▼                   ▼                   ▼
+-----------------+ +-----------------+ +---------------------+
|  transactions   | |    audit_log    | |    rules_config     |
+-----------------+ +-----------------+ +---------------------+
| id (PK)         | | id (PK)         | | merchant_id (PK, FK)|
| merchant_id (FK)| | transaction_id  | | max_amount_per_order|
| customer_id     | | merchant_id (FK)| | max_txns_per_minute |
| amount          | | action          | | category_limits     |
| agent_type      | | actor ('system')| | created_at          |
| status          | | prev_hash       | | updated_at          |
| risk_score      | | row_hash        | +---------------------+
| reason (JSONB)  | | created_at      |
| model_version   | +-----------------+
| created_at      |
+-----------------+
```

### 3.2 Row-Level Security (RLS)
Every table enforces RLS with PostgreSQL policies scoping read and write access to `merchant_id = current_merchant_id()`. Multi-tenant leakage between merchants is strictly prevented at the database kernel level.

### 3.3 Append-Only Audit Trail Guarantees
* **Database Role Permissions**: `REVOKE UPDATE, DELETE, TRUNCATE ON TABLE audit_log FROM authenticated, anon, public;`
* **Defensive Trigger**: `trg_prevent_audit_log_mutation` raises an exception if any update/delete query is attempted.
* **Cryptographic Chaining**: Each audit row calculates $\text{row\_hash}_n = \text{SHA256}(\text{data}_n \,\|\, \text{prev\_hash}_n)$, ensuring any retroactive modification renders `verify_chain()` false.

---

## 4. Risk Scorer Decision Matrix

| Condition | Decision | Risk Score | Machine-Readable Reason Driver |
| :--- | :--- | :--- | :--- |
| Hard Rule Triggered (Max amount / velocity / category cap) | `blocked` | `1.0` | `rule_violation` (`rule_name`, `rule_reason`) |
| Soft Rule Triggered | `held` | `0.65` | `soft_rule_violation` |
| $\text{Model Score} \ge \theta_{\text{block}}$ | `blocked` | Model Score ($\ge 0.70$) | `high_anomaly_score` (`feature_drivers`) |
| $\theta_{\text{hold}} \le \text{Model Score} < \theta_{\text{block}}$ | `held` | Model Score ($[0.45, 0.70)$) | `medium_anomaly_score` (`feature_drivers`) |
| $\text{Model Score} < \theta_{\text{hold}}$ | `approved` | Model Score ($< 0.45$) | `normal_baseline` |

---

## 5. Security & Model Integrity Architecture

1. **SHA-256 Model Digest**: Pre-computed during training and stored in `model_metadata.json`.
2. **Startup Verification**: FastAPI `lifespan` event calls `verify_model_integrity()`. If the file hash mismatches, startup aborts immediately with a `SecurityError`.
3. **Threshold Poisoning Defense**: `AdaptiveThresholdManager` limits threshold drift to $\le 10\%$ per update with strict bounds $[0.15, 0.85]$.

---

## 6. Phase 3 Integration Interfaces

* **Authentication Middleware**: In Phase 3, incoming requests will validate Supabase JWTs and merchant API keys, populating `current_merchant_id()` dynamically.
* **Claude Explanation Service**: Consumes machine-readable `reason` objects from `POST /transactions/check` to generate merchant-facing natural language audit summaries.
* **Human Confirmation Queue & Razorpay Client**: Webhook listener receiving manual analyst approvals and triggering Razorpay Order API creation.
