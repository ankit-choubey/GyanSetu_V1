"""
GyanSetu - Intervention Recommender

Recommends the most suitable intervention type for a learner
based on current mastery and historical intervention outcomes.

DATA SOURCE:
[SANDBOX DATA] synthetic intervention outcomes.

This is an MVP recommendation component. It does not replace
the backend competency engine.
"""

import json
from pathlib import Path

import pandas as pd


class InterventionRecommender:
    """Recommend interventions using historical effectiveness."""

    INTERVENTION_TYPES = [
        "targeted_practice",
        "worked_example",
        "video_lesson",
        "adaptive_quiz",
        "peer_discussion",
    ]

    WEIGHTS = {
        "improvement": 0.50,
        "retention_success": 0.30,
        "completion": 0.20,
    }

    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.data = None
        self.effectiveness = None

    def load_data(self):
        """Load and validate intervention outcome data."""

        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Intervention data not found: {self.data_path}"
            )

        df = pd.read_csv(self.data_path)

        required_columns = {
            "learner_id",
            "intervention_type",
            "completed",
            "mastery_before",
            "improvement",
            "retention_success",
            "data_source",
        }

        missing = required_columns - set(df.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        if not (df["data_source"] == "[SANDBOX DATA]").all():
            raise ValueError(
                "Intervention recommender requires sandbox-labelled data."
            )

        if df.empty:
            raise ValueError("Intervention dataset is empty.")

        if df["mastery_before"].isna().any():
            raise ValueError("mastery_before contains missing values.")

        if df["improvement"].isna().any():
            raise ValueError("improvement contains missing values.")

        if df["retention_success"].isna().any():
            raise ValueError("retention_success contains missing values.")

        if df["completed"].isna().any():
            raise ValueError("completed contains missing values.")

        self.data = df

        return df

    @staticmethod
    def mastery_band(mastery):
        """Convert mastery score into low, medium, or high band."""

        mastery = float(mastery)

        if not 0.0 <= mastery <= 1.0:
            raise ValueError("mastery must be between 0 and 1.")

        if mastery <= 0.30:
            return "low"
        elif mastery <= 0.60:
            return "medium"
        else:
            return "high"

    def fit(self):
        """Calculate historical effectiveness by mastery band."""

        if self.data is None:
            self.load_data()

        df = self.data.copy()

        df["mastery_band"] = df["mastery_before"].apply(
            self.mastery_band
        )

        effectiveness = (
            df.groupby(
                ["mastery_band", "intervention_type"],
                observed=True,
            )[
                [
                    "improvement",
                    "retention_success",
                    "completed",
                ]
            ]
            .mean()
            .reset_index()
        )

        effectiveness["score"] = (
            self.WEIGHTS["improvement"]
            * effectiveness["improvement"]
            + self.WEIGHTS["retention_success"]
            * effectiveness["retention_success"]
            + self.WEIGHTS["completion"]
            * effectiveness["completed"]
        )

        effectiveness = effectiveness.sort_values(
            ["mastery_band", "score"],
            ascending=[True, False],
        )

        self.effectiveness = effectiveness

        return effectiveness

    def recommend(self, mastery, top_k=3):
        """Return ranked intervention recommendations."""

        if self.effectiveness is None:
            self.fit()

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        band = self.mastery_band(mastery)

        results = self.effectiveness[
            self.effectiveness["mastery_band"] == band
        ].copy()

        results = results.head(
            min(top_k, len(results))
        )

        recommendations = []

        for rank, (_, row) in enumerate(
            results.iterrows(),
            start=1,
        ):
            recommendations.append(
                {
                    "rank": rank,
                    "intervention_type": row["intervention_type"],
                    "mastery_band": band,
                    "effectiveness_score": round(
                        float(row["score"]), 4
                    ),
                    "expected_improvement": round(
                        float(row["improvement"]), 4
                    ),
                    "retention_success_rate": round(
                        float(row["retention_success"]), 4
                    ),
                    "completion_rate": round(
                        float(row["completed"]), 4
                    ),
                }
            )

        return {
            "mastery": round(float(mastery), 4),
            "mastery_band": band,
            "recommendations": recommendations,
            "data_source": "[SANDBOX DATA]",
        }

    def save_effectiveness(self, output_path):
        """Save calculated effectiveness statistics."""

        if self.effectiveness is None:
            self.fit()

        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        records = self.effectiveness.to_dict(
            orient="records"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                records,
                f,
                indent=2,
            )


if __name__ == "__main__":

    DATA_PATH = (
        "synthetic_data/data/"
        "intervention_outcomes.csv"
    )

    OUTPUT_PATH = (
        "models/"
        "intervention_effectiveness.json"
    )

    recommender = InterventionRecommender(
        DATA_PATH
    )

    recommender.load_data()
    effectiveness = recommender.fit()

    print("\nIntervention effectiveness:")
    print(
        effectiveness.to_string(
            index=False
        )
    )

    print("\nExample recommendations:")

    for mastery in [0.20, 0.45, 0.80]:
        result = recommender.recommend(
            mastery,
            top_k=3,
        )

        print(
            f"\nMastery: {mastery} "
            f"({result['mastery_band']})"
        )

        for recommendation in result[
            "recommendations"
        ]:
            print(
                f"  {recommendation['rank']}. "
                f"{recommendation['intervention_type']} "
                f"(score="
                f"{recommendation['effectiveness_score']})"
            )

    recommender.save_effectiveness(
        OUTPUT_PATH
    )

    print(
        f"\nSaved effectiveness data to: "
        f"{OUTPUT_PATH}"
    )