# PayFilter Architecture Specification (Phase 1)

## 1. System Overview

PayFilter is a high-throughput, low-latency transaction risk evaluation layer positioned between AI agent checkout requests and the Razorpay Order Creation API.

```text
+---------------------+      +------------------------+      +-----------------------+
|  AI Agent / Client  | ---> |   PayFilter Risk Layer  | ---> |  Razorpay Order API   |
| (Autonomous Action) |      | (Features + ML + Rules)|      | (Authorized Only)     |
+---------------------+      +------------------------+      +-----------------------+
                                         |
                                         v
                             +------------------------+
                             | Adaptive Threshold Mgr |
                             | (Human Feedback Queue) |
                             +------------------------+
```

---

## 2. Temporal Feature Extraction Pipeline

To evaluate incoming transactions without lookahead bias, features are computed incrementally over strictly causal historical windows:

```text
Incoming Transaction: (customer_id, amount, merchant_category, agent_type, timestamp = t)
                                    |
                                    v
+-----------------------------------------------------------------------------------+
| Historical Customer State Query (Filtered where t_historical < t)                 |
+-----------------------------------------------------------------------------------+
| 1. Customer Average Amount:   E[Amount | t_hist < t]                              |
| 2. Amount-to-Average Ratio:   Amount / Prior_Avg                                  |
| 3. Hourly Velocity:           Count(Txns | t - 1h <= t_hist < t)                  |
| 4. Daily Velocity:            Count(Txns | t - 24h <= t_hist < t)                 |
| 5. Interval Delta:            t - max(t_hist)                                     |
| 6. Category Frequency:        Count(Category | t_hist < t) / Count(Txns)          |
| 7. Agent Frequency:           Count(Agent | t_hist < t) / Count(Txns)             |
| 8. New Category Indicator:    1 if Category not in past history else 0            |
| 9. Diurnal Hour Deviation:    min_dist_circular(hour(t), hours(t_hist)) / 12      |
+-----------------------------------------------------------------------------------+
                                    |
                                    v
                       Model-Ready 10-D Feature Vector
```

---

## 3. Anomaly Detection & Scoring Architecture

PayFilter employs an ensemble of unsupervised Isolation Forest trees combined with a safety-critical heuristic rule baseline.

### 3.1 Model Selection & Parameterization
* **Algorithm**: `sklearn.ensemble.IsolationForest`
* **Contamination**: `0.015` (1.5% assumed real-world anomaly baseline)
* **Ensemble Size**: 150 Isolation Trees
* **Feature Subsampling**: Automatic with subsampling factor

### 3.2 Decision Boundary
The model computes an anomaly path length score $s(x)$. Inverted risk scores $\in [0, 1]$ are passed to the `AdaptiveThresholdManager` to issue verdicts:
* $\text{Score} < \text{Threshold} \implies \text{APPROVE}$
* $\text{Score} \ge \text{Threshold} \implies \text{FLAG / CHALLENGE}$

---

## 4. Security & Cryptographic Integrity Layer

Model weights and configurations are protected against supply-chain injection and filesystem tampering.

```text
Training Phase:
Train Model ---> Serialize (isolation_forest.pkl) ---> SHA-256 Hash ---> Save (model_metadata.json)

Inference Startup (load_secure_model):
Read isolation_forest.pkl ---> Compute SHA-256 Digest
                                       |
                                       v
                             Match Metadata Hash?
                                   /       \
                               [YES]       [NO]
                                 /           \
                 Load Model into RAM      Raise SecurityError
```

---

## 5. Adaptive Threshold Poisoning Mitigation

Adversaries may attempt to flood the system with fraudulent transactions and submit false human approval signals to skew the model's threshold upward.

### Defense Mechanism
1. **Change Rate Cap**: Updates are strictly clamped to:
   $$\Delta \theta \le \theta_{\text{current}} \times \text{max\_change\_rate} \quad (\text{default } 10\%)$$
2. **Absolute Safety Floors**: Hard bounds $[\theta_{\min}, \theta_{\max}] = [0.15, 0.85]$ prevent extreme threshold drift under any circumstance.

---

## 6. Phase 2 Backend Consumption Contract

Phase 2 services import these exact modules:
* `from ml.features import extract_single_transaction_features`
* `from ml.threshold_manager import AdaptiveThresholdManager`
* `from ml.train_model import load_secure_model`
* `from ml.baseline_rules import evaluate_single_rule_record`
