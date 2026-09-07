from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base_adapter import InterventionAdapter

BASE_DIR = Path(__file__).resolve().parents[4]
REAL_DATA_DIR = BASE_DIR / "real_data" / "data"


class IGOTAdapter(InterventionAdapter):
    """Adapter for iGOT Karmayogi course repository (REPLAY mode using public catalog)."""

    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or (REAL_DATA_DIR / "igot_course_catalog.json")
        self._simulated_available: bool = True
        self._catalog_cache: dict[str, dict[str, Any]] = {}
        self._load_catalog()

    def _load_catalog(self) -> None:
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("courses", []):
                        cid = item.get("catalogue_id")
                        if cid:
                            self._catalog_cache[cid] = item
            except Exception:
                pass

    def get_provider_name(self) -> str:
        return "iGOT"

    def get_integration_mode(self) -> str:
        return "REPLAY"

    def set_simulated_availability(self, available: bool) -> None:
        self._simulated_available = available

    def check_availability(self, resource_id: str | None = None) -> bool:
        if not self._simulated_available:
            return False
        if resource_id:
            return resource_id in self._catalog_cache
        return True

    def fetch_resource(self, resource_id: str) -> dict[str, Any] | None:
        if not self._simulated_available:
            return None
        return self._catalog_cache.get(resource_id)


class NSSTAAdapter(InterventionAdapter):
    """Adapter for National Statistical Systems Training Academy (REPLAY mode)."""

    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or (REAL_DATA_DIR / "nssta_tpac_programmes.json")
        self._simulated_available: bool = True
        self._catalog_cache: dict[str, dict[str, Any]] = {}
        self._load_catalog()

    def _load_catalog(self) -> None:
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    for idx, item in enumerate(items, start=1):
                        prog_id = f"NSSTA-PROG-{idx:03d}"
                        self._catalog_cache[prog_id] = item
            except Exception:
                pass

    def get_provider_name(self) -> str:
        return "NSSTA"

    def get_integration_mode(self) -> str:
        return "REPLAY"

    def set_simulated_availability(self, available: bool) -> None:
        self._simulated_available = available

    def check_availability(self, resource_id: str | None = None) -> bool:
        if not self._simulated_available:
            return False
        if resource_id:
            return resource_id in self._catalog_cache
        return True

    def fetch_resource(self, resource_id: str) -> dict[str, Any] | None:
        if not self._simulated_available:
            return None
        return self._catalog_cache.get(resource_id)


class TPACAdapter(NSSTAAdapter):
    """Adapter for Training Programme Advisory Committee recommendations (REPLAY mode)."""

    def get_provider_name(self) -> str:
        return "TPAC"


class VirtualLabAdapter(InterventionAdapter):
    """Adapter for interactive statistical simulation environments (SANDBOX mode)."""

    def __init__(self) -> None:
        self._simulated_available: bool = True

    def get_provider_name(self) -> str:
        return "VIRTUAL_LAB"

    def get_integration_mode(self) -> str:
        return "SANDBOX"

    def set_simulated_availability(self, available: bool) -> None:
        self._simulated_available = available

    def check_availability(self, resource_id: str | None = None) -> bool:
        return self._simulated_available

    def fetch_resource(self, resource_id: str) -> dict[str, Any] | None:
        if not self._simulated_available:
            return None
        return {
            "resource_id": resource_id,
            "provider": "VIRTUAL_LAB",
            "type": "virtual_lab",
            "provenance": "[SANDBOX DATA]",
            "status": "ACTIVE",
        }


class InternalAdapter(InterventionAdapter):
    """Adapter for native GyanSetu assessments, scenarios, and practice drills (LIVE mode)."""

    def __init__(self) -> None:
        self._simulated_available: bool = True

    def get_provider_name(self) -> str:
        return "INTERNAL"

    def get_integration_mode(self) -> str:
        return "LIVE"

    def set_simulated_availability(self, available: bool) -> None:
        self._simulated_available = available

    def check_availability(self, resource_id: str | None = None) -> bool:
        return self._simulated_available

    def fetch_resource(self, resource_id: str) -> dict[str, Any] | None:
        if not self._simulated_available:
            return None
        return {
            "resource_id": resource_id,
            "provider": "INTERNAL",
            "provenance": "[CURATED]",
            "status": "ACTIVE",
        }


_REGISTRY_ADAPTERS: dict[str, InterventionAdapter] = {
    "IGOT": IGOTAdapter(),
    "NSSTA": NSSTAAdapter(),
    "TPAC": TPACAdapter(),
    "VIRTUAL_LAB": VirtualLabAdapter(),
    "INTERNAL": InternalAdapter(),
}


def get_adapter_for_provider(provider_name: str) -> InterventionAdapter:
    normalized = provider_name.upper().strip()
    return _REGISTRY_ADAPTERS.get(normalized, _REGISTRY_ADAPTERS["INTERNAL"])
