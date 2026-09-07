"""
ML Providers Bridge Module
GyanSetu - Phase 4.1b + 4.5b

Connects trained psychometric and cognitive ML models to FastAPI backend services:
- RetentionProvider (models/retention_model.pkl) -> monitoring_agent (stale evidence detection)
- LearningStateProvider (models/learning_state_model.pkl) -> signal_collector (learning state classification)
- MisconceptionClassifierProvider (ml_pipeline/misconception_classifier.py) -> misconception_tracker
- IRTProvider (models/irt_item_params.json) -> 2PL IRT item lookup and probability
- InterventionProvider (models/intervention_effectiveness.json) -> targeted intervention recommendations
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    import models.retention_model as _rm
    sys.modules.setdefault("retention_model", _rm)
except ImportError:
    pass

try:
    import models.learning_state_classifier as _lsc
    sys.modules.setdefault("learning_state_classifier", _lsc)
except ImportError:
    pass

MODELS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "models")
)


class RetentionProvider:
    """Provides retention factor inference from models/retention_model.pkl."""

    REQUIRED_FEATURES = [
        "days_since_learning",
        "mastery_before_decay",
        "decay_amount",
        "intervention_count",
        "intervention_boost",
        "mastery",
    ]

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.path.join(MODELS_DIR, "retention_model.pkl")
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Retention model artifact not found at {self.model_path}")
            try:
                from models.retention_model import RetentionModel
                self._model = RetentionModel.load(self.model_path)
            except Exception:
                import joblib
                self._model = joblib.load(self.model_path)

    def predict_retention(self, features: Dict[str, float]) -> float:
        """
        Predicts retention factor in [0.0, 1.0].
        Fills defaults for missing features safely.
        """
        self._ensure_model()
        payload = {
            "days_since_learning": float(features.get("days_since_learning", 30.0)),
            "mastery_before_decay": float(features.get("mastery_before_decay", 0.75)),
            "decay_amount": float(features.get("decay_amount", 0.05)),
            "intervention_count": float(features.get("intervention_count", 0.0)),
            "intervention_boost": float(features.get("intervention_boost", 0.0)),
            "mastery": float(features.get("mastery", 0.70)),
        }
        if hasattr(self._model, "predict_one"):
            return float(self._model.predict_one(payload))
        import pandas as pd
        df = pd.DataFrame([payload])
        return float(self._model.predict(df)[0])

    def evaluate_stale_evidence(
        self,
        observed_at: datetime,
        current_mastery: float = 0.7,
        reassessment_threshold: float = 0.65,
    ) -> Tuple[float, bool]:
        """
        Calculates predicted retention and determines if reassessment is recommended.
        Returns: (predicted_retention, reassessment_needed)
        """
        now = datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        days = max(0.0, (now - observed_at).total_seconds() / 86400.0)
        retention = self.predict_retention({
            "days_since_learning": days,
            "mastery_before_decay": current_mastery,
            "decay_amount": 0.05,
            "intervention_count": 0.0,
            "intervention_boost": 0.0,
            "mastery": current_mastery,
        })
        return retention, retention < reassessment_threshold


class LearningStateProvider:
    """Provides learning state classification from models/learning_state_model.pkl."""

    REQUIRED_FEATURES = [
        "accuracy",
        "average_response_time_seconds",
        "hints_used",
        "completion_rate",
        "engagement_score",
        "mastery_change",
        "session_quality_score",
    ]

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.path.join(MODELS_DIR, "learning_state_model.pkl")
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Learning state model artifact not found at {self.model_path}")
            try:
                from models.learning_state_classifier import LearningStateClassifier
                self._model = LearningStateClassifier.load(self.model_path)
            except Exception:
                import joblib
                self._model = joblib.load(self.model_path)

    def classify_state(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies learner session into one of: 'mastered', 'improving', 'needs_practice', 'struggling'.
        """
        self._ensure_model()
        payload = {
            "accuracy": float(signals.get("accuracy", 0.7)),
            "average_response_time_seconds": float(signals.get("average_response_time_seconds", signals.get("response_time", 25.0))),
            "hints_used": float(signals.get("hints_used", signals.get("hints_requested", 0.0))),
            "completion_rate": float(signals.get("completion_rate", 1.0)),
            "engagement_score": float(signals.get("engagement_score", 0.75)),
            "mastery_change": float(signals.get("mastery_change", 0.05)),
            "session_quality_score": float(signals.get("session_quality_score", 0.8)),
        }
        if hasattr(self._model, "predict_one"):
            return self._model.predict_one(payload)
        import pandas as pd
        df = pd.DataFrame([payload])
        pred = self._model.predict(df)[0]
        return {"predicted_state": str(pred), "confidence": 0.8, "data_source": "[SANDBOX DATA]"}


class MisconceptionClassifierProvider:
    """Wraps ml_pipeline/misconception_classifier.py for backend service injection."""

    def __init__(self):
        from ml_pipeline.misconception_classifier import LLMMisconceptionClassifier
        self._classifier = LLMMisconceptionClassifier()

    def classify(self, response: Any) -> Any:
        return self._classifier.classify(response)


class IRTProvider:
    """Loads 2PL IRT calibrated parameters from models/irt_item_params.json."""

    def __init__(self, params_path: Optional[str] = None):
        self.params_path = params_path or os.path.join(MODELS_DIR, "irt_item_params.json")
        self._items_by_id: Optional[Dict[str, Dict[str, Any]]] = None

    def _ensure_loaded(self):
        if self._items_by_id is None:
            if not os.path.exists(self.params_path):
                raise FileNotFoundError(f"IRT params not found at {self.params_path}")
            with open(self.params_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._items_by_id = {
                item["item_id"]: item for item in data.get("items", [])
            }

    def get_item_params(self, item_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        return self._items_by_id.get(item_id)

    def predict_probability(self, theta: float, item_id: str) -> float:
        """Computes 2PL IRT response probability P(theta) = 1 / (1 + exp(-1.702 * a * (theta - b)))."""
        params = self.get_item_params(item_id)
        if not params:
            return 1.0 / (1.0 + math.exp(-theta))
        a = float(params.get("calibrated_discrimination_a", 1.0))
        b = float(params.get("calibrated_difficulty_b", 0.0))
        exponent = -1.702 * a * (theta - b)
        exponent = max(-30.0, min(30.0, exponent))
        return 1.0 / (1.0 + math.exp(exponent))


class InterventionProvider:
    """Loads intervention effectiveness matrix from models/intervention_effectiveness.json."""

    def __init__(self, matrix_path: Optional[str] = None):
        self.matrix_path = matrix_path or os.path.join(MODELS_DIR, "intervention_effectiveness.json")
        self._matrix: Optional[List[Dict[str, Any]]] = None

    def _ensure_loaded(self):
        if self._matrix is None:
            if not os.path.exists(self.matrix_path):
                raise FileNotFoundError(f"Intervention effectiveness matrix not found at {self.matrix_path}")
            with open(self.matrix_path, "r", encoding="utf-8") as f:
                self._matrix = json.load(f)

    def recommend_interventions(self, mastery_band: str = "medium", top_k: int = 3) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        band = mastery_band.lower()
        candidates = [row for row in self._matrix if row.get("mastery_band", "").lower() == band]
        if not candidates:
            candidates = self._matrix
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("score", x.get("improvement", 0.0)),
            reverse=True,
        )
        return sorted_candidates[:top_k]
