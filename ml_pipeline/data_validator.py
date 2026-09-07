"""
ml_pipeline/data_validator.py — Schema & Quality Validator for Real Learner Data.

Validates learner interaction logs, test responses, and temporal signals before
feeding into Bayesian Knowledge Tracing (BKT), Item Response Theory (IRT),
and Retention decay model retraining pipelines.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import pandas as pd


REQUIRED_INTERACTION_COLUMNS = {
    "learner_id",
    "item_id",
    "is_correct",
}

RECOMMENDED_COLUMNS = {
    "timestamp",
    "competency",
    "subskill",
    "response_time_seconds",
}


@dataclass
class DataValidationReport:
    """Detailed diagnostic report of learner data health and validity."""
    is_valid: bool
    total_records: int
    valid_records: int
    invalid_records: int
    unique_learners: int
    unique_items: int
    competencies_found: List[str]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)


class LearnerDataValidator:
    """
    Validates learner interaction records against psychometric pipeline requirements.
    """

    def __init__(
        self,
        min_records: int = 20,
        min_learners: int = 3,
        min_items: int = 2,
    ):
        self.min_records = min_records
        self.min_learners = min_learners
        self.min_items = min_items

    def validate_dataframe(self, df: pd.DataFrame) -> DataValidationReport:
        """
        Validates a pandas DataFrame of interaction records.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if df is None or df.empty:
            return DataValidationReport(
                is_valid=False,
                total_records=0,
                valid_records=0,
                invalid_records=0,
                unique_learners=0,
                unique_items=0,
                competencies_found=[],
                errors=["Input DataFrame is empty or None."],
            )

        total_records = len(df)
        df_clean = df.copy()

        # Check required columns
        missing_required = REQUIRED_INTERACTION_COLUMNS - set(df_clean.columns)
        if missing_required:
            errors.append(f"Missing mandatory columns: {sorted(list(missing_required))}")
            return DataValidationReport(
                is_valid=False,
                total_records=total_records,
                valid_records=0,
                invalid_records=total_records,
                unique_learners=0,
                unique_items=0,
                competencies_found=[],
                errors=errors,
            )

        # Check recommended columns
        missing_recommended = RECOMMENDED_COLUMNS - set(df_clean.columns)
        if missing_recommended:
            warnings.append(f"Missing recommended columns (defaults will be applied): {sorted(list(missing_recommended))}")

        # Normalize is_correct column
        try:
            # Map booleans, strings 'true'/'false', 0/1 to integer 0/1
            df_clean["is_correct_norm"] = df_clean["is_correct"].apply(
                lambda v: 1 if v in (1, "1", True, "true", "True") else (0 if v in (0, "0", False, "false", "False") else None)
            )
        except Exception as exc:
            errors.append(f"Failed to normalize 'is_correct' values: {exc}")
            df_clean["is_correct_norm"] = None

        invalid_correctness = df_clean["is_correct_norm"].isna().sum()
        if invalid_correctness > 0:
            errors.append(f"Found {invalid_correctness} rows with non-binary 'is_correct' values.")

        # Check for null learner_ids or item_ids
        null_learners = df_clean["learner_id"].isna().sum()
        null_items = df_clean["item_id"].isna().sum()
        if null_learners > 0:
            errors.append(f"Found {null_learners} rows with missing 'learner_id'.")
        if null_items > 0:
            errors.append(f"Found {null_items} rows with missing 'item_id'.")

        valid_df = df_clean.dropna(subset=["learner_id", "item_id", "is_correct_norm"])
        valid_count = len(valid_df)
        invalid_count = total_records - valid_count

        unique_learners = int(valid_df["learner_id"].nunique()) if not valid_df.empty else 0
        unique_items = int(valid_df["item_id"].nunique()) if not valid_df.empty else 0

        # Minimum data guards
        if valid_count < self.min_records:
            errors.append(
                f"Dataset has {valid_count} valid records, which is below the minimum threshold of {self.min_records}."
            )
        if unique_learners < self.min_learners:
            errors.append(
                f"Dataset contains {unique_learners} unique learners, which is below the minimum threshold of {self.min_learners}."
            )
        if unique_items < self.min_items:
            errors.append(
                f"Dataset contains {unique_items} unique items, which is below the minimum threshold of {self.min_items}."
            )

        # Sample size warning for production statistical power
        if valid_count < 200:
            warnings.append(
                f"Dataset size ({valid_count} records) is adequate for calibration tests but recommend >200 records for optimal IRT/BKT convergence."
            )

        # Competency discovery
        competencies = []
        if "competency" in valid_df.columns:
            competencies = [str(c) for c in valid_df["competency"].dropna().unique() if str(c).strip()]

        summary_stats = {
            "mean_accuracy": float(valid_df["is_correct_norm"].mean()) if not valid_df.empty else 0.0,
            "min_interactions_per_learner": int(valid_df["learner_id"].value_counts().min()) if not valid_df.empty else 0,
            "max_interactions_per_learner": int(valid_df["learner_id"].value_counts().max()) if not valid_df.empty else 0,
        }

        is_valid = len(errors) == 0

        return DataValidationReport(
            is_valid=is_valid,
            total_records=total_records,
            valid_records=valid_count,
            invalid_records=invalid_count,
            unique_learners=unique_learners,
            unique_items=unique_items,
            competencies_found=competencies,
            errors=errors,
            warnings=warnings,
            summary_stats=summary_stats,
        )
