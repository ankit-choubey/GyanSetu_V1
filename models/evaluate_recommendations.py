"""
models/evaluate_recommendations.py — Comparative Evaluation of Recommendation Policies.

Evaluates:
1. Deterministic Heuristic Baseline Policy (System of Record)
2. Historical Effectiveness Recommender (Contextual Multi-Armed Bandit / Thompson Sampling candidate)

DATA SOURCE:
[SANDBOX DATA] synthetic intervention outcomes (808 interactions across 200 learners).
Evaluation performed on a learner-disjoint 80/20 train/test split to prevent identity leakage.

SCIENTIFIC HONESTY DISCLAIMER:
Observed correlation between recommended intervention and post-intervention improvement
reflects historical associations in synthetic data, NOT proven causal efficacy.
Causal validation requires randomized controlled trials (RCT) or quasi-experimental designs (backlog).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from models.intervention_recommender import InterventionRecommender

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "synthetic_data" / "data" / "intervention_outcomes.csv"
OUTPUT_METRICS_PATH = BASE_DIR / "models" / "recommendation_evaluation_metrics.json"


class DeterministicBaselinePolicy:
    """Deterministic, rule-based recommendation policy based on cognitive load theory."""

    def recommend(self, mastery: float) -> str:
        if mastery < 0.30:
            # Low mastery: worked examples minimize cognitive load
            return "worked_example"
        elif mastery < 0.60:
            # Medium mastery: targeted practice strengthens application
            return "targeted_practice"
        else:
            # High mastery: active retrieval/adaptive quiz
            return "adaptive_quiz"


def evaluate_recommendation_policies() -> dict[str, Any]:
    print("=" * 80)
    print("GYANSETU PHASE 3 — RECOMMENDATION POLICY COMPARATIVE EVALUATION")
    print("=" * 80)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Intervention outcomes dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"[+] Loaded {len(df)} interaction events across {df['learner_id'].nunique()} unique learners.")

    # Disjoint 80/20 learner split
    unique_learners = sorted(df["learner_id"].unique())
    np.random.seed(42)
    test_learners = set(np.random.choice(unique_learners, size=int(len(unique_learners) * 0.20), replace=False))
    train_learners = set(unique_learners) - test_learners

    train_df = df[df["learner_id"].isin(train_learners)].copy()
    test_df = df[df["learner_id"].isin(test_learners)].copy()

    print(f"[+] Disjoint Learner Split: {len(train_learners)} train learners ({len(train_df)} events), {len(test_learners)} test learners ({len(test_df)} events).")

    # Fit Historical Recommender on Train Set
    train_data_path = BASE_DIR / "synthetic_data" / "data" / "_temp_train_outcomes.csv"
    train_df.to_csv(train_data_path, index=False)

    recommender = InterventionRecommender(train_data_path)
    recommender.fit()
    baseline = DeterministicBaselinePolicy()

    # Evaluate on Held-Out Test Set
    baseline_improvements: list[float] = []
    recommender_improvements: list[float] = []
    non_matched_improvements: list[float] = []

    baseline_matches = 0
    recommender_matches = 0
    total_test = len(test_df)

    for _, row in test_df.iterrows():
        mastery = float(row["mastery_before"])
        actual_type = row["intervention_type"]
        improvement = float(row["improvement"])

        # Baseline prediction
        base_rec = baseline.recommend(mastery)
        if base_rec == actual_type:
            baseline_matches += 1
            baseline_improvements.append(improvement)

        # Recommender prediction
        rec_res = recommender.recommend(mastery, top_k=1)
        top_rec = rec_res["recommendations"][0]["intervention_type"]
        if top_rec == actual_type:
            recommender_matches += 1
            recommender_improvements.append(improvement)
        else:
            non_matched_improvements.append(improvement)

    # Clean up temp file
    if train_data_path.exists():
        train_data_path.unlink()

    avg_baseline_imp = float(np.mean(baseline_improvements)) if baseline_improvements else 0.0
    avg_recommender_imp = float(np.mean(recommender_improvements)) if recommender_improvements else 0.0
    avg_non_matched_imp = float(np.mean(non_matched_improvements)) if non_matched_improvements else 0.0
    avg_overall_imp = float(test_df["improvement"].mean())

    metrics = {
        "dataset_events": len(df),
        "total_learners": df["learner_id"].nunique(),
        "test_events": total_test,
        "test_learners": len(test_learners),
        "baseline_policy": {
            "name": "Deterministic Rule-Based Baseline (Cognitive Load Theory)",
            "test_matches": baseline_matches,
            "match_rate": round(baseline_matches / total_test, 4),
            "mean_observed_improvement": round(avg_baseline_imp, 4),
            "status": "CANONICAL SYSTEM OF RECORD",
        },
        "bandit_recommender": {
            "name": "Historical Effectiveness Ranker (Multi-Armed Bandit candidate)",
            "test_matches": recommender_matches,
            "match_rate": round(recommender_matches / total_test, 4),
            "mean_observed_improvement": round(avg_recommender_imp, 4),
            "status": "REPLACEABLE CANDIDATE",
        },
        "unmatched_mean_improvement": round(avg_non_matched_imp, 4),
        "overall_mean_improvement": round(avg_overall_imp, 4),
        "scientific_validity_status": {
            "evidence_weight_status": "HEURISTIC (v1.0-heuristic)",
            "causality_claim": "OBSERVED ASSOCIATION (Non-causal in absence of prospective randomized trial)",
            "recommendation_scoring": "TRANSPARENT MULTI-FACTOR HEURISTIC POLICY",
        },
    }

    print("\n" + "=" * 80)
    print("EVALUATION RESULTS (HELD-OUT TEST SET):")
    print("-" * 80)
    print(f"Deterministic Baseline:  Mean Improvement = {avg_baseline_imp:.4f} | Match Rate = {baseline_matches / total_test:.2%}")
    print(f"Bandit Recommender:      Mean Improvement = {avg_recommender_imp:.4f} | Match Rate = {recommender_matches / total_test:.2%}")
    print(f"Overall Population Mean: Mean Improvement = {avg_overall_imp:.4f}")
    print("-" * 80)
    print("Policy Decision: Retain Deterministic Baseline as Canonical Backend System of Record;")
    print("Bandit / ML models remain replaceable parameterization candidates behind adapter interfaces.")
    print("=" * 80)

    with open(OUTPUT_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"[+] Metrics successfully written to: {OUTPUT_METRICS_PATH}")
    return metrics


if __name__ == "__main__":
    evaluate_recommendation_policies()
