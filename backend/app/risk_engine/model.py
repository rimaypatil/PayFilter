"""ML Anomaly Model inference and startup integrity enforcement."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# Canonical package imports from ml/
from ml.features import FEATURE_COLUMNS
from ml.train_model import SecurityError, load_secure_model, verify_model_integrity

logger = logging.getLogger("payfilter.risk_engine.model")


class MLModelManager:
    """Manages loaded IsolationForest model with tamper-evident cryptographic validation."""

    def __init__(
        self,
        model_path: Optional[Path | str] = None,
        metadata_path: Optional[Path | str] = None,
    ):
        self.model_path = Path(model_path) if model_path else None
        self.metadata_path = Path(metadata_path) if metadata_path else None
        self._model: Optional[IsolationForest] = None
        self._metadata: Optional[Dict[str, Any]] = None

    def initialize(self) -> None:
        """Loads and cryptographically validates the ML model on startup.

        Raises:
            SecurityError: If model integrity verification fails.
            FileNotFoundError: If model or metadata files do not exist.
        """
        if self._model is not None:
            return
        logger.info("Verifying model integrity and loading IsolationForest...")
        model, metadata = load_secure_model(
            model_path=self.model_path,
            metadata_path=self.metadata_path,
        )
        self._model = model
        self._metadata = metadata
        logger.info(
            f"Successfully loaded verified model v{metadata.get('model_version')} "
            f"(SHA-256: {metadata.get('model_hash', '')[:16]}...)"
        )

    @property
    def model_version(self) -> str:
        """Returns loaded model version string."""
        if self._metadata:
            return self._metadata.get("model_version", "1.0.0")
        return "1.0.0"

    @property
    def is_loaded(self) -> bool:
        """Returns True if model is loaded and verified."""
        return self._model is not None

    def score_features(self, features: Dict[str, float]) -> float:
        """Calculates normalized anomaly score in [0.0, 1.0].

        Higher score denotes higher anomaly probability / higher risk.

        Args:
            features: Dictionary containing FEATURE_COLUMNS.

        Returns:
            float: Anomaly score between 0.0 (completely normal) and 1.0 (highly anomalous).
        """
        if self._model is None:
            self.initialize()

        # Build feature vector in exact canonical column order
        ordered_vals = [float(features.get(col, 0.0)) for col in FEATURE_COLUMNS]
        X = np.array([ordered_vals], dtype=float)

        # In IsolationForest, decision_function returns negative values for outliers
        # decision_function ranges roughly between -0.35 (outlier) and +0.25 (inlier)
        # Shift and scale to [0.0, 1.0] where 1.0 is maximum anomaly
        raw_decision = float(self._model.decision_function(X)[0])
        # Logistic transformation centered around threshold
        scaled_score = 1.0 / (1.0 + np.exp(raw_decision * 8.0))
        return round(float(np.clip(scaled_score, 0.0, 1.0)), 4)

    def identify_feature_drivers(self, features: Dict[str, float]) -> List[str]:
        """Identifies key anomaly features driving the risk score."""
        drivers = []
        amt_ratio = features.get("amount_vs_average_ratio", 1.0)
        if amt_ratio > 3.0:
            drivers.append(f"amount_vs_average_ratio ({amt_ratio:.1f}x normal)")
        
        txns_1h = features.get("transactions_last_hour", 0.0)
        if txns_1h >= 4.0:
            drivers.append(f"high_hourly_velocity ({int(txns_1h)} txns in 1h)")

        time_prev = features.get("time_since_previous_transaction", 86400.0)
        if time_prev < 30.0:
            drivers.append(f"rapid_repeat ({time_prev:.1f}s since last)")

        new_cat = features.get("is_new_merchant_category_for_customer", 0.0)
        if new_cat == 1.0:
            drivers.append("unseen_merchant_category")

        hour_dev = features.get("hour_of_day_deviation", 0.0)
        if hour_dev >= 0.75:
            drivers.append(f"unusual_hour_of_day (deviation: {hour_dev:.2f})")

        return drivers


# Global singleton instance
_model_manager: Optional[MLModelManager] = None


def get_model_manager(
    model_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
) -> MLModelManager:
    """Returns the singleton MLModelManager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = MLModelManager(model_path=model_path, metadata_path=metadata_path)
    return _model_manager
