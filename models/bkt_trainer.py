"""
BKT Model Trainer & Trajectory Generator
GyanSetu - Phase 3.1
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import pandas as pd

from models.bkt_model import BKTModel


class BKTTrainer:
    def __init__(
        self,
        model: Optional[BKTModel] = None,
        data_path: str = "synthetic_data/data/learner_interactions.csv",
    ) -> None:
        self.model = model or BKTModel()
        self.data_path = data_path

    def load_data(self, path: Optional[str] = None) -> pd.DataFrame:
        target_path = path or self.data_path
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Data file not found at: {target_path}")
        return pd.read_csv(target_path)

    def train_trajectories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute knowledge state trajectories for learner interactions."""
        rows = []

        # Process per learner and competency to track progression sequentially
        for (learner_id, competency_id), group in df.groupby(
            ["learner_id", "competency_id"], sort=False
        ):
            p_known = self.model.initialize_knowledge()

            for _, record in group.iterrows():
                correct = bool(record["correct"])
                p_correct_before = self.model.predict_response_probability(p_known)
                p_known_before = p_known
                p_known_after = self.model.update_after_response(p_known, correct)

                rows.append({
                    "learner_id": learner_id,
                    "competency_id": competency_id,
                    "timestamp": record["timestamp"],
                    "correct": record["correct"],
                    "p_known_before": p_known_before,
                    "p_correct_before": p_correct_before,
                    "p_known_after": p_known_after,
                    "data_source": record.get("data_source", "[SANDBOX DATA]"),
                })

                p_known = p_known_after

        trajectories_df = pd.DataFrame(rows)
        return trajectories_df

    def save_config(self, path: str = "models/bkt_config.json") -> None:
        config = {
            "model": "Bayesian Knowledge Tracing",
            "parameters": {
                "p_init": self.model.p_init,
                "p_learn": self.model.p_learn,
                "p_guess": self.model.p_guess,
                "p_slip": self.model.p_slip,
            },
            "data_source": "[SANDBOX DATA]",
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def run(
        self,
        config_path: str = "models/bkt_config.json",
        output_path: str = "models/bkt_learner_trajectories.csv",
    ) -> None:
        df = self.load_data()
        trajectories = self.train_trajectories(df)
        trajectories.to_csv(output_path, index=False)
        self.save_config(config_path)
        print(f"Generated {len(trajectories)} BKT trajectories saved to {output_path}")


if __name__ == "__main__":
    trainer = BKTTrainer()
    trainer.run()
