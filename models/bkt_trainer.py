"""
Bayesian Knowledge Tracing (BKT) Trainer
GyanSetu - Phase 3.1
"""

import json
import os
from typing import Optional

import pandas as pd

try:
    from models.bkt_model import BKTModel
except ModuleNotFoundError:
    from bkt_model import BKTModel


class BKTTrainer:
    """
    Trains BKT knowledge trajectories from learner interaction logs.
    """

    def __init__(self, model: Optional[BKTModel] = None, data_path: Optional[str] = None):
        self.model = model or BKTModel()
        if data_path:
            self.data_path = data_path
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate = os.path.join(base_dir, "synthetic_data", "data", "learner_interactions.csv")
            if os.path.exists(candidate):
                self.data_path = candidate
            elif os.path.exists("synthetic_data/data/learner_interactions.csv"):
                self.data_path = "synthetic_data/data/learner_interactions.csv"
            else:
                self.data_path = candidate

    def load_data(self) -> pd.DataFrame:
        """Loads learner interactions dataset."""
        df = pd.read_csv(self.data_path)
        return df

    def train_trajectories(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes learner interaction sequences using BKT and produces knowledge trajectories.
        """
        p_known_befores = []
        p_correct_befores = []
        p_known_afters = []

        knowledge_states = {}

        for _, row in df.iterrows():
            learner_id = row["learner_id"]
            competency_id = row["competency_id"]
            correct = bool(row["correct"])

            key = (learner_id, competency_id)
            if key not in knowledge_states:
                knowledge_states[key] = self.model.initialize_knowledge()

            p_before = knowledge_states[key]
            p_correct = self.model.predict_response_probability(p_before)
            p_after = self.model.update_after_response(p_before, correct)

            knowledge_states[key] = p_after

            p_known_befores.append(p_before)
            p_correct_befores.append(p_correct)
            p_known_afters.append(p_after)

        trajectories = pd.DataFrame({
            "learner_id": df["learner_id"].values,
            "competency_id": df["competency_id"].values,
            "timestamp": df["timestamp"].values,
            "correct": df["correct"].values,
            "p_known_before": p_known_befores,
            "p_correct_before": p_correct_befores,
            "p_known_after": p_known_afters,
            "data_source": "[SANDBOX DATA]",
        })
        return trajectories

    def train_and_save(
        self,
        output_csv_path: str = "models/bkt_learner_trajectories.csv",
        config_json_path: str = "models/bkt_config.json",
    ):
        df = self.load_data()
        trajectories = self.train_trajectories(df)
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        trajectories.to_csv(output_csv_path, index=False)

        config = {
            "model": "Bayesian Knowledge Tracing",
            "parameters": {
                "p_init": self.model.p_init,
                "p_learn": self.model.p_learn,
                "p_guess": self.model.p_guess,
                "p_slip": self.model.p_slip,
            },
            "data_source": "[SANDBOX DATA]",
            "training_data": "synthetic_data/data/learner_interactions.csv",
        }
        with open(config_json_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return trajectories, config


if __name__ == "__main__":
    trainer = BKTTrainer()
    print("Training BKT trajectories...")
    trainer.train_and_save()
    print("BKT trajectories and config saved successfully.")
