from __future__ import annotations

from app.seed_data.runner import seed_full_taxonomy


def seed_data(seed_password: str | None = None) -> None:
    seed_full_taxonomy(seed_password)
