import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ml.features import FEATURE_COLUMNS, extract_features
from ml.baseline_rules import evaluate_baseline_rules
from ml.train_model import (
    load_secure_model,
    time_based_train_test_split,
    verify_model_integrity,
)

def run_evaluation():
    print("=" * 80)
    print("1. RUNNING REAL EVALUATION (ml/evaluate.ipynb pipeline)")
    print("=" * 80)

    data_path = Path("ml/data/synthetic_transactions.csv")
    if not data_path.exists():
        data_path = Path("data/synthetic_transactions.csv")

    print(f"Loading dataset: {data_path}")
    df = pd.read_csv(data_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    total_txns = len(df)
    overall_anomaly_rate = df["label"].mean()
    print(f"Total transactions: {total_txns:,}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Overall Anomaly rate: {overall_anomaly_rate:.4%}")

    print("\nExtracting features (leakage-safe, rolling strictly prior to timestamp)...")
    features_df = extract_features(df)
    print(f"Feature matrix shape: {features_df.shape}")

    # Strict Time-Based Partitioning
    X_train, X_test, y_train, y_test, df_train, df_test = time_based_train_test_split(
        df, features_df, train_ratio=0.80
    )

    print(f"\nTraining set: {len(X_train):,} samples (from {df_train['timestamp'].min()} to {df_train['timestamp'].max()})")
    print(f"Train anomaly rate: {y_train.mean():.4%}")
    print(f"Testing set:  {len(X_test):,} samples (from {df_test['timestamp'].min()} to {df_test['timestamp'].max()})")
    print(f"Test anomaly rate:  {y_test.mean():.4%}")

    # 1. Rules-Only Baseline
    rules_preds = evaluate_baseline_rules(X_test)

    # 2. Isolation Forest Model (Loaded with cryptographic SHA-256 integrity check)
    model_path = Path("ml/models/isolation_forest.pkl")
    meta_path = Path("ml/models/model_metadata.json")
    iso_model, metadata = load_secure_model(model_path, meta_path)
    iso_raw_preds = iso_model.predict(X_test[FEATURE_COLUMNS])
    iso_preds = np.where(iso_raw_preds == -1, 1, 0)

    # Optional XGBoost
    try:
        import xgboost as xgb
        xgb_clf = xgb.XGBClassifier(n_estimators=100, max_depth=4, random_state=42, eval_metric="logloss")
        xgb_clf.fit(X_train[FEATURE_COLUMNS], y_train)
        xgb_preds = xgb_clf.predict(X_test[FEATURE_COLUMNS])
        xgb_avail = True
    except Exception as e:
        xgb_avail = False
        xgb_preds = None

    # Friction Cost Calculation
    ASSUMED_DROP_OFF_RATE = 0.05  # 5% assumed customer drop-off on friction
    avg_txn_value = float(df_test["amount"].mean())
    num_legit = int((y_test == 0).sum())

    def get_metrics_dict(name: str, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()

        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fp_percentage = (fp / num_legit) * 100.0 if num_legit > 0 else 0.0
        friction_cost = fp * avg_txn_value * ASSUMED_DROP_OFF_RATE

        return {
            "Model": name,
            "Precision": round(precision, 4),
            "Recall": round(recall, 4),
            "F1 Score": round(f1, 4),
            "False Positive Rate": f"{fpr:.2%}",
            "Legit Flagged (FP)": int(fp),
            "Legit Flagged (%)": f"{fp_percentage:.2f}%",
            "Est. Friction Cost (INR)": f"₹{friction_cost:,.2f}",
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "TP": int(tp),
        }

    metrics_rules = get_metrics_dict("Rules-Only Baseline", y_test.values, rules_preds)
    metrics_iso = get_metrics_dict("Isolation Forest (Unsupervised)", y_test.values, iso_preds)

    metrics_list = [metrics_rules, metrics_iso]
    if xgb_avail and xgb_preds is not None:
        metrics_list.append(get_metrics_dict("XGBoost (Supervised Benchmark)", y_test.values, xgb_preds))

    print("\n" + "=" * 80)
    print("CLASSIFICATION REPORTS & CONFUSION MATRICES")
    print("=" * 80)

    for name, preds in [("Rules Baseline", rules_preds), ("Isolation Forest", iso_preds)]:
        print(f"\n--- {name} Classification Report ---")
        print(classification_report(y_test, preds, target_names=["Normal (0)", "Anomalous (1)"], digits=4))
        print(f"{name} Confusion Matrix (TN, FP / FN, TP):")
        cm = confusion_matrix(y_test, preds)
        print(f"[[TN={cm[0,0]:>5}, FP={cm[0,1]:>5}]\n [FN={cm[1,0]:>5}, TP={cm[1,1]:>5}]]")

    print("\n" + "=" * 80)
    print("COMPARISON & FRICTION COST SUMMARY TABLE")
    print("=" * 80)
    summary_df = pd.DataFrame(metrics_list)
    print(summary_df[["Model", "Precision", "Recall", "F1 Score", "False Positive Rate", "Legit Flagged (FP)", "Legit Flagged (%)", "Est. Friction Cost (INR)"]].to_markdown(index=False))

    print(f"\nFriction Cost Formula: FP * Average Order Value (₹{avg_txn_value:.2f}) * Drop-off Rate ({ASSUMED_DROP_OFF_RATE:.0%})")
    print("Assumed Drop-off Rate: 5% industry benchmark for customer abandonment upon challenge.")

if __name__ == "__main__":
    run_evaluation()
