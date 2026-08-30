# PayFilter — Phase 1 (Data & ML Foundation)

PayFilter is an intelligent, real-time risk mitigation and anomaly detection layer designed for AI-agent-initiated transactions before a merchant creates a Razorpay order.

This repository contains **Phase 1: Data & Machine Learning Foundation**, establishing a production-grade, tamper-evident ML pipeline and leakage-safe feature engineering engine.

---

## Architecture & Directory Structure

```text
payfilter/
├── ml/
│   ├── generate_synthetic_data.py   # Synthetic transaction generator (5 anomaly vectors)
│   ├── features.py                  # Leakage-safe rolling feature extractor
│   ├── baseline_rules.py            # Deterministic heuristic baseline for benchmarking
│   ├── threshold_manager.py         # Adaptive threshold with poisoning attack defense
│   ├── train_model.py               # Time-split training with SHA-256 tamper checks
│   ├── evaluate.ipynb               # End-to-end evaluation & friction cost analysis
│   ├── data/
│   │   └── synthetic_transactions.csv
│   ├── models/
│   │   ├── isolation_forest.pkl     # Serialized trained Isolation Forest model
│   │   └── model_metadata.json      # Model metadata, dataset & model SHA-256 digests
│   └── tests/
│       ├── test_data_generation.py  # Validation of data volume & 5 anomaly types
│       ├── test_features.py         # Leakage prevention & feature matrix validation
│       ├── test_baseline_rules.py   # Heuristic rule trigger & sanity checks
│       ├── test_model.py            # Model training & tamper-evident security tests
│       └── test_threshold_manager.py# Attack simulation & threshold cap tests
│
├── features.py                      # Root proxy for seamless backend imports
├── threshold_manager.py             # Root proxy for seamless backend imports
├── requirements.txt                 # Pinned dependencies
├── .gitignore                       # Git ignore configuration
├── README.md                        # Documentation & setup guide
└── ARCHITECTURE.md                  # Comprehensive system & ML architecture
```

---

## 1. Synthetic Data Generator

Generate programmatic, realistic AI-agent transaction streams with a fixed random seed for 100% reproducibility.

```bash
python ml/generate_synthetic_data.py --normal 10000 --anomalous 450 --days 60 --seed 42
```

### Dataset Schema
* `transaction_id`: Unique identifier (`txn_000001`)
* `customer_id`: Synthetic customer profile ID
* `merchant_id`: Fake merchant identifier
* `amount`: Transaction value in standard currency units (INR)
* `timestamp`: ISO 8601 chronological timestamp
* `merchant_category`: Category (`ecommerce`, `saas`, `travel`, `gaming`, `utilities`, `food_delivery`, `luxury`, `electronics`, `crypto`)
* `agent_type`: Initiating AI agent (`procurement_agent`, `customer_service_bot`, `personal_assistant`, `automated_scheduler`, `code_assistant`, `browser_subagent`)
* `label`: Ground truth indicator (`0 = normal`, `1 = anomalous`)
* `anomaly_type`: Subtype metadata

### Synthesized Anomaly Vectors
1. **Velocity Spike**: High volume of rapid, varied purchases across different merchants in $< 15$ minutes.
2. **Repeat Loop**: Near-identical transactions (same amount, same merchant) repeated rapidly in seconds, simulating a stuck/looping autonomous agent.
3. **Amount Spike**: Single transaction amounts $10\times - 25\times$ higher than customer's historical average.
4. **Merchant Shift**: Customer suddenly transacting with above-average amounts in a completely unprecedented merchant category (e.g., luxury or crypto).
5. **Odd-Hour Burst**: Purchases executed at hours outside of that specific customer's normal diurnal activity pattern.

### Anomaly Rate Rationale & Contamination Setting
> **Deliberate Design Decision:**
> Real-world transaction fraud rates are typically $< 1\%$. In our synthetic training dataset, we maintain a rate of **~4.5%** (~450 anomalies out of 10,450 transactions). This compromise ensures sufficient statistical sample size to evaluate all five anomaly subtypes and prevents severe class starvation during testing.
>
> However, when configuring `IsolationForest(contamination=0.015)`, we deliberately parameterize the model with the **assumed real-world rate (1.5%)**, NOT the synthetic dataset's inflated rate. This distinction is tracked explicitly in `model_metadata.json`.

---

## 2. Feature Engineering & Strict Leakage Prevention

`ml/features.py` converts raw transactions into numerical representations:
* `amount`
* `customer_average_amount` (prior mean)
* `amount_vs_average_ratio`
* `transactions_last_hour` (count in $[t-1\text{h}, t)$)
* `transactions_last_day` (count in $[t-24\text{h}, t)$)
* `time_since_previous_transaction` (seconds)
* `merchant_category_frequency`
* `agent_type_frequency`
* `is_new_merchant_category_for_customer`
* `hour_of_day_deviation` (circular hour distance relative to customer history)

### Zero Data Leakage Guarantee
All rolling and historical aggregations are computed strictly over transactions where $t_{\text{historical}} < t_{\text{current}}$. Future transactions relative to the scoring point never enter the calculation. Unit tests (`test_features.py`) verify that injecting future rows produces zero change in earlier feature vectors.

---

## 3. Tamper-Evident Model Integrity Layer

To protect against adversarial model corruption or supply-chain tampering:
1. **SHA-256 Model Digest**: During training, a cryptographic SHA-256 hash is computed over `isolation_forest.pkl` and saved in `model_metadata.json`.
2. **Integrity Verification**: `load_secure_model()` recalculates the binary hash before loading.
3. **Tamper Rejection**: Any discrepancy raises a `SecurityError`, halting execution immediately.

---

## 4. Adaptive Threshold Poisoning Protection

`ml/threshold_manager.py` manages risk score decision thresholds:
* Updates dynamically based on confirmed human analyst feedback (approvals/denials on held orders).
* **Maximum Delta Cap**: Bounded to a strict change rate (e.g. $\le 10\%$ per update cycle).
* **Adversarial Defense**: Prevents rapid approval floods from dragging down the risk threshold to allow fraudulent orders through.

---

## 5. Evaluation & Friction Cost Analysis

Run the evaluation notebook:

```bash
jupyter nbconvert --to notebook --execute ml/evaluate.ipynb --output ml/evaluate.ipynb
```

### Estimated Friction Cost Formula
When false positives occur on legitimate orders, customer verification friction introduces drop-off:

$$\text{Friction Cost} = \text{False Positives} \times \text{Average Transaction Value} \times \text{Assumed Drop-off Rate (5\%)}$$

---

## 6. Running Tests

Execute the complete automated test suite with pytest:

```bash
pytest -v ml/tests/
```

Test coverage includes:
* `test_data_generation.py`: Volume, columns, and presence of all 5 anomaly types.
* `test_features.py`: Zero NaNs, feature schema, and no lookahead leakage.
* `test_baseline_rules.py`: Heuristic trigger verification and false-positive immunity.
* `test_model.py`: Time-based split, metadata generation, SHA-256 checks, and 1-byte deliberate corruption rejection.
* `test_threshold_manager.py`: Drift cap enforcement and adversarial flood attack simulation.

---

## Phase 2 Backend Direct Reuse

The modules created in Phase 1 are designed for direct production consumption in Phase 2:
* `features.py` / `ml.features.extract_single_transaction_features`: Directly consumed by the FastAPI pre-order risk evaluation endpoint.
* `threshold_manager.py` / `ml.threshold_manager.AdaptiveThresholdManager`: Directly consumed by the webhook and manual review approval queue.
* `ml.train_model.load_secure_model`: Directly consumed during application startup for verified model inference.
