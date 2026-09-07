from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base_adapter import (
    AvailabilityResult,
    AvailabilityStatus,
    CanonicalInterventionPayload,
    HealthStatus,
    IntegrationMode,
    InterventionAdapter,
    LaunchResult,
    ProviderHealth,
)

BASE_DIR = Path(__file__).resolve().parents[4]
REAL_DATA_DIR = BASE_DIR / "real_data" / "data"


class BaseProviderAdapter(InterventionAdapter):
    """Base helper providing simulation hooks and common utilities."""

    def __init__(self) -> None:
        self._simulated_available: bool = True
        self._simulate_timeout: bool = False
        self._simulate_auth_failure: bool = False

    def set_simulated_availability(self, available: bool) -> None:
        self._simulated_available = available

    def simulate_timeout(self, enable: bool = True) -> None:
        self._simulate_timeout = enable

    def simulate_auth_failure(self, enable: bool = True) -> None:
        self._simulate_auth_failure = enable

    def _check_fault_injections(self, resource_id: str | None = None) -> AvailabilityResult | None:
        if self._simulate_timeout:
            return AvailabilityResult(
                resource_id=resource_id,
                status=AvailabilityStatus.PROVIDER_ERROR,
                is_available=False,
                reason="Provider connection timed out (simulated)",
            )
        if self._simulate_auth_failure:
            return AvailabilityResult(
                resource_id=resource_id,
                status=AvailabilityStatus.NOT_AUTHORIZED,
                is_available=False,
                reason="Authentication to external provider failed: Invalid API credentials",
            )
        if not self._simulated_available:
            return AvailabilityResult(
                resource_id=resource_id,
                status=AvailabilityStatus.UNAVAILABLE,
                is_available=False,
                reason=f"{self.get_provider_name()} provider service is currently unavailable",
            )
        return None


class IGOTAdapter(BaseProviderAdapter):
    """Adapter for iGOT Karmayogi course repository.
    
    Supports LIVE, SANDBOX, and REPLAY.
    If live API credentials are missing, explicitly reports REPLAY mode with full disclosure.
    """

    def __init__(self, data_path: Path | None = None) -> None:
        super().__init__()
        self.data_path = data_path or (REAL_DATA_DIR / "igot_course_catalog.json")
        self._catalog_cache: dict[str, dict[str, Any]] = {}
        self._live_api_key: str | None = os.getenv("IGOT_API_KEY")
        self._live_api_base: str | None = os.getenv("IGOT_API_BASE_URL")
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

    def get_integration_mode(self) -> IntegrationMode:
        if self._live_api_key and self._live_api_base:
            return IntegrationMode.LIVE
        return IntegrationMode.REPLAY

    def get_requested_mode(self) -> IntegrationMode:
        return IntegrationMode.LIVE

    def get_fallback_reason(self) -> str | None:
        if self.get_integration_mode() == IntegrationMode.REPLAY:
            return "Live iGOT Karmayogi API unconfigured; running authenticated public replay catalog"
        return None

    def health_check(self) -> ProviderHealth:
        start_time = time.perf_counter()
        fault = self._check_fault_injections()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if fault is not None:
            health_status = (
                HealthStatus.UNAUTHORIZED
                if fault.status == AvailabilityStatus.NOT_AUTHORIZED
                else HealthStatus.UNAVAILABLE
            )
            return ProviderHealth(
                provider=self.get_provider_name(),
                status=health_status,
                mode=self.get_integration_mode(),
                latency_ms=elapsed_ms,
                resource_count=len(self._catalog_cache),
                details=fault.reason,
            )

        return ProviderHealth(
            provider=self.get_provider_name(),
            status=HealthStatus.HEALTHY,
            mode=self.get_integration_mode(),
            latency_ms=elapsed_ms,
            resource_count=len(self._catalog_cache),
            details=f"Catalog loaded with {len(self._catalog_cache)} verified courses",
        )

    def check_availability(self, resource_id: str | None = None) -> AvailabilityResult:
        fault = self._check_fault_injections(resource_id)
        if fault is not None:
            return fault

        if resource_id:
            if resource_id in self._catalog_cache:
                return AvailabilityResult(
                    resource_id=resource_id,
                    status=AvailabilityStatus.AVAILABLE,
                    is_available=True,
                    reason="Resource active in public catalog",
                )
            return AvailabilityResult(
                resource_id=resource_id,
                status=AvailabilityStatus.UNAVAILABLE,
                is_available=False,
                reason="Resource ID not found in iGOT catalog",
            )

        return AvailabilityResult(
            resource_id=None,
            status=AvailabilityStatus.AVAILABLE,
            is_available=True,
            reason="iGOT adapter online",
        )

    def search_resources(
        self, query: str | None = None, competency: str | None = None
    ) -> list[CanonicalInterventionPayload]:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return []

        results: list[CanonicalInterventionPayload] = []
        for raw in self._catalog_cache.values():
            title = raw.get("course_title", "")
            comp_hint = raw.get("aligned_competency", "")
            if query and query.lower() not in title.lower():
                continue
            if competency and competency.lower() not in comp_hint.lower():
                continue
            results.append(self._normalize_item(raw))
        return results

    def get_resource(self, resource_id: str) -> CanonicalInterventionPayload | None:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return None
        raw = self._catalog_cache.get(resource_id)
        if not raw:
            return None
        return self._normalize_item(raw)

    def launch_resource(self, resource_id: str, learner_id: int) -> LaunchResult:
        res = self.check_availability(resource_id)
        if not res.is_available:
            return LaunchResult(
                provider=self.get_provider_name(),
                provider_resource_id=resource_id,
                provider_activity_id=f"act_err_{uuid.uuid4().hex[:8]}",
                learner_id=learner_id,
                integration_mode=self.get_integration_mode().value,
                launch_url=None,
                status="FAILED",
            )

        activity_id = f"igot_act_{uuid.uuid4().hex[:10]}"
        raw = self._catalog_cache.get(resource_id, {})
        launch_url = raw.get("source_url", f"https://igotkarmayogi.gov.in/course/{resource_id}")

        return LaunchResult(
            provider=self.get_provider_name(),
            provider_resource_id=resource_id,
            provider_activity_id=activity_id,
            learner_id=learner_id,
            integration_mode=self.get_integration_mode().value,
            launch_url=launch_url,
            status="INITIALIZED",
        )

    def sync_resources(self) -> list[CanonicalInterventionPayload]:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return []
        return [self._normalize_item(raw) for raw in self._catalog_cache.values()]

    def _normalize_item(self, raw: dict[str, Any]) -> CanonicalInterventionPayload:
        return CanonicalInterventionPayload(
            provider="iGOT",
            provider_resource_id=raw.get("catalogue_id", ""),
            title=raw.get("course_title", ""),
            intervention_type="COURSE",
            modality="ONLINE_SELF_PACED",
            duration_minutes=raw.get("duration_minutes", 90),
            difficulty=raw.get("difficulty", "intermediate"),
            competency_hint=raw.get("aligned_competency"),
            subskill_hint=raw.get("aligned_subskill"),
            description=raw.get("description"),
            external_url=raw.get("source_url", "https://igotkarmayogi.gov.in"),
            provenance="[REAL/PUBLIC DATA - iGOT Karmayogi]",
            integration_mode=self.get_integration_mode().value,
            external_metadata={"ministry": raw.get("ministry"), "curriculum": raw.get("curriculum")},
            status="ACTIVE",
        )


class NSSTAAdapter(BaseProviderAdapter):
    """Adapter for National Statistical Systems Training Academy (REPLAY mode).
    
    Strictly preserves public programme information vs private learner records.
    """

    def __init__(self, data_path: Path | None = None) -> None:
        super().__init__()
        self.data_path = data_path or (REAL_DATA_DIR / "nssta_tpac_programmes.json")
        self._catalog_cache: dict[str, dict[str, Any]] = {}
        self._load_catalog()

    def _load_catalog(self) -> None:
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    for idx, item in enumerate(items, start=1):
                        prog_id = f"NSSTA-PROG-{idx:03d}"
                        item["prog_id"] = prog_id
                        self._catalog_cache[prog_id] = item
            except Exception:
                pass

    def get_provider_name(self) -> str:
        return "NSSTA"

    def get_integration_mode(self) -> IntegrationMode:
        return IntegrationMode.REPLAY

    def get_requested_mode(self) -> IntegrationMode:
        return IntegrationMode.LIVE

    def get_fallback_reason(self) -> str | None:
        return "Live NSSTA academy student information system unavailable; running public curriculum calendar"

    def health_check(self) -> ProviderHealth:
        start_time = time.perf_counter()
        fault = self._check_fault_injections()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if fault is not None:
            return ProviderHealth(
                provider=self.get_provider_name(),
                status=HealthStatus.UNAVAILABLE,
                mode=self.get_integration_mode(),
                latency_ms=elapsed_ms,
                resource_count=len(self._catalog_cache),
                details=fault.reason,
            )

        return ProviderHealth(
            provider=self.get_provider_name(),
            status=HealthStatus.HEALTHY,
            mode=self.get_integration_mode(),
            latency_ms=elapsed_ms,
            resource_count=len(self._catalog_cache),
            details=f"NSSTA training academy calendar active with {len(self._catalog_cache)} offerings",
        )

    def check_availability(self, resource_id: str | None = None) -> AvailabilityResult:
        fault = self._check_fault_injections(resource_id)
        if fault is not None:
            return fault

        if resource_id:
            if resource_id in self._catalog_cache:
                return AvailabilityResult(
                    resource_id=resource_id,
                    status=AvailabilityStatus.AVAILABLE,
                    is_available=True,
                    reason="Programme active on training schedule",
                )
            return AvailabilityResult(
                resource_id=resource_id,
                status=AvailabilityStatus.UNAVAILABLE,
                is_available=False,
                reason="Programme ID not scheduled at NSSTA",
            )

        return AvailabilityResult(
            resource_id=None,
            status=AvailabilityStatus.AVAILABLE,
            is_available=True,
            reason="NSSTA provider online",
        )

    def search_resources(
        self, query: str | None = None, competency: str | None = None
    ) -> list[CanonicalInterventionPayload]:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return []

        results: list[CanonicalInterventionPayload] = []
        for raw in self._catalog_cache.values():
            name = raw.get("programme_name", "")
            comp_hint = raw.get("aligned_competency", "")
            if query and query.lower() not in name.lower():
                continue
            if competency and competency.lower() not in comp_hint.lower():
                continue
            results.append(self._normalize_item(raw))
        return results

    def get_resource(self, resource_id: str) -> CanonicalInterventionPayload | None:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return None
        raw = self._catalog_cache.get(resource_id)
        if not raw:
            return None
        return self._normalize_item(raw)

    def launch_resource(self, resource_id: str, learner_id: int) -> LaunchResult:
        res = self.check_availability(resource_id)
        if not res.is_available:
            return LaunchResult(
                provider=self.get_provider_name(),
                provider_resource_id=resource_id,
                provider_activity_id=f"act_err_{uuid.uuid4().hex[:8]}",
                learner_id=learner_id,
                integration_mode=self.get_integration_mode().value,
                launch_url=None,
                status="FAILED",
            )

        activity_id = f"nssta_act_{uuid.uuid4().hex[:10]}"
        launch_url = f"https://nssta.gov.in/training-programme/{resource_id}"

        return LaunchResult(
            provider=self.get_provider_name(),
            provider_resource_id=resource_id,
            provider_activity_id=activity_id,
            learner_id=learner_id,
            integration_mode=self.get_integration_mode().value,
            launch_url=launch_url,
            status="INITIALIZED",
        )

    def sync_resources(self) -> list[CanonicalInterventionPayload]:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return []
        return [self._normalize_item(raw) for raw in self._catalog_cache.values()]

    def _normalize_item(self, raw: dict[str, Any]) -> CanonicalInterventionPayload:
        title = raw.get("programme_title") or raw.get("programme_name") or "NSSTA Training Programme"
        comp_hint = raw.get("aligned_competency")
        sub_hint = raw.get("aligned_subskill")

        # Map known topics to canonical competencies if not explicitly provided
        if not comp_hint:
            topic = (raw.get("topic") or "").lower()
            t_lower = title.lower()
            if "machine learning" in topic or "python" in topic:
                comp_hint = "Python for Analytics"
                sub_hint = "Data cleaning with pandas"
            elif "sampling" in topic or "remote sensing" in topic:
                comp_hint = "Sampling Design"
                sub_hint = "Stratified sampling"
            elif "index" in topic or "price" in topic:
                comp_hint = "Index Numbers & Deflators"
                sub_hint = "CPI compilation"
            elif "national accounts" in topic or "sna" in topic:
                comp_hint = "National Accounts"
                sub_hint = "SNA 2008 framework"

        return CanonicalInterventionPayload(
            provider="NSSTA",
            provider_resource_id=raw.get("prog_id", ""),
            title=title,
            intervention_type="WORKSHOP",
            modality="BLENDED_RESIDENTIAL",
            duration_minutes=raw.get("duration_hours", 30) * 60,
            difficulty="advanced",
            competency_hint=comp_hint,
            subskill_hint=sub_hint,
            description=raw.get("content") or raw.get("description") or "National Statistical Systems Training Academy Programme",
            external_url=raw.get("source_url") or "https://nssta.gov.in",
            provenance="[REAL/PUBLIC DATA - MoSPI NSSTA]",
            integration_mode=self.get_integration_mode().value,
            external_metadata={
                "target_audience": raw.get("target_audience"),
                "proposed_institute": raw.get("proposed_institute"),
                "location": "Greater Noida, UP",
            },
            status="ACTIVE",
        )


class TPACAdapter(NSSTAAdapter):
    """Adapter for Training Programme Advisory Committee recommendations (REPLAY mode)."""

    def get_provider_name(self) -> str:
        return "TPAC"

    def get_fallback_reason(self) -> str | None:
        return "Public advisory curriculum schedule active in replay mode"

    def check_availability(self, resource_id: str | None = None) -> AvailabilityResult:
        if resource_id and resource_id.startswith("TPAC-"):
            clean_id = resource_id.replace("TPAC-", "", 1)
            res = super().check_availability(clean_id)
            res.resource_id = resource_id
            return res
        return super().check_availability(resource_id)

    def launch_resource(self, resource_id: str, learner_id: int) -> LaunchResult:
        clean_id = resource_id.replace("TPAC-", "", 1) if resource_id.startswith("TPAC-") else resource_id
        res = super().launch_resource(clean_id, learner_id)
        res.provider = "TPAC"
        res.provider_resource_id = resource_id
        return res

    def _normalize_item(self, raw: dict[str, Any]) -> CanonicalInterventionPayload:
        norm = super()._normalize_item(raw)
        norm.provider = "TPAC"
        norm.provider_resource_id = f"TPAC-{raw.get('prog_id', '')}"
        norm.provenance = "[REAL/PUBLIC DATA - MoSPI TPAC Advisory]"
        return norm


class VirtualLabAdapter(BaseProviderAdapter):
    """Adapter for interactive statistical simulation environments (SANDBOX mode)."""

    def __init__(self) -> None:
        super().__init__()
        self._labs: dict[str, dict[str, Any]] = {
            "VLAB-SAMPLE-01": {
                "id": "VLAB-SAMPLE-01",
                "title": "MoSPI Interactive Sampling Simulation Lab",
                "type": "SIMULATION_LAB",
                "modality": "VIRTUAL_LAB",
                "duration_minutes": 45,
                "difficulty": "intermediate",
                "competency_hint": "Sampling Design",
                "subskill_hint": "Stratified sampling",
                "description": "Python-powered sandbox executing multi-stage stratified cluster sampling simulations.",
            },
            "CURATED-LAB-001": {
                "id": "CURATED-LAB-001",
                "title": "Virtual Lab: Probability Sampling & Weight Adjustment Workbench",
                "type": "SIMULATION_LAB",
                "modality": "VIRTUAL_LAB",
                "duration_minutes": 45,
                "difficulty": "intermediate",
                "competency_hint": "Sampling Design",
                "subskill_hint": "Stratified sampling",
                "description": "Interactive Jupyter simulation sandbox modeling MoSPI multi-stage sampling frames.",
            },
            "VLAB-CPI-02": {
                "id": "VLAB-CPI-02",
                "title": "Price Statistics & Index Number Compilation Sandbox",
                "type": "SIMULATION_LAB",
                "modality": "VIRTUAL_LAB",
                "duration_minutes": 60,
                "difficulty": "advanced",
                "competency_hint": "Index Numbers & Deflators",
                "subskill_hint": "CPI compilation",
                "description": "Interactive Laspeyres vs Paasche index weighting laboratory with live validation feedback.",
            },
        }

    def get_provider_name(self) -> str:
        return "VIRTUAL_LAB"

    def get_integration_mode(self) -> IntegrationMode:
        return IntegrationMode.SANDBOX

    def health_check(self) -> ProviderHealth:
        start_time = time.perf_counter()
        fault = self._check_fault_injections()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if fault is not None:
            return ProviderHealth(
                provider=self.get_provider_name(),
                status=HealthStatus.UNAVAILABLE,
                mode=self.get_integration_mode(),
                latency_ms=elapsed_ms,
                resource_count=len(self._labs),
                details=fault.reason,
            )

        return ProviderHealth(
            provider=self.get_provider_name(),
            status=HealthStatus.HEALTHY,
            mode=self.get_integration_mode(),
            latency_ms=elapsed_ms,
            resource_count=len(self._labs),
            details=f"Virtual statistical simulation sandbox online with {len(self._labs)} simulation labs",
        )

    def check_availability(self, resource_id: str | None = None) -> AvailabilityResult:
        fault = self._check_fault_injections(resource_id)
        if fault is not None:
            return fault

        if resource_id:
            if resource_id in self._labs or resource_id.startswith("CURATED-LAB") or resource_id.startswith("VLAB-"):
                return AvailabilityResult(
                    resource_id=resource_id,
                    status=AvailabilityStatus.AVAILABLE,
                    is_available=True,
                    reason="Virtual simulation container ready",
                )

            return AvailabilityResult(
                resource_id=resource_id,
                status=AvailabilityStatus.UNAVAILABLE,
                is_available=False,
                reason="Virtual lab container image not found",
            )

        return AvailabilityResult(
            resource_id=None,
            status=AvailabilityStatus.AVAILABLE,
            is_available=True,
            reason="Virtual lab sandbox cluster healthy",
        )

    def search_resources(
        self, query: str | None = None, competency: str | None = None
    ) -> list[CanonicalInterventionPayload]:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return []

        results: list[CanonicalInterventionPayload] = []
        for raw in self._labs.values():
            if query and query.lower() not in raw["title"].lower():
                continue
            if competency and competency.lower() not in raw["competency_hint"].lower():
                continue
            results.append(self._normalize_item(raw))
        return results

    def get_resource(self, resource_id: str) -> CanonicalInterventionPayload | None:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return None
        raw = self._labs.get(resource_id)
        if not raw:
            return None
        return self._normalize_item(raw)

    def launch_resource(self, resource_id: str, learner_id: int) -> LaunchResult:
        res = self.check_availability(resource_id)
        if not res.is_available:
            return LaunchResult(
                provider=self.get_provider_name(),
                provider_resource_id=resource_id,
                provider_activity_id=f"act_err_{uuid.uuid4().hex[:8]}",
                learner_id=learner_id,
                integration_mode=self.get_integration_mode().value,
                launch_url=None,
                status="FAILED",
            )

        activity_id = f"vlab_session_{uuid.uuid4().hex[:10]}"
        launch_url = f"/api/ecosystem/labs/{resource_id}/session/{activity_id}"

        return LaunchResult(
            provider=self.get_provider_name(),
            provider_resource_id=resource_id,
            provider_activity_id=activity_id,
            learner_id=learner_id,
            integration_mode=self.get_integration_mode().value,
            launch_url=launch_url,
            status="ACTIVE",
        )

    def sync_resources(self) -> list[CanonicalInterventionPayload]:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return []
        return [self._normalize_item(raw) for raw in self._labs.values()]

    def _normalize_item(self, raw: dict[str, Any]) -> CanonicalInterventionPayload:
        return CanonicalInterventionPayload(
            provider="VIRTUAL_LAB",
            provider_resource_id=raw["id"],
            title=raw["title"],
            intervention_type=raw["type"],
            modality=raw["modality"],
            duration_minutes=raw["duration_minutes"],
            difficulty=raw["difficulty"],
            competency_hint=raw["competency_hint"],
            subskill_hint=raw["subskill_hint"],
            description=raw["description"],
            external_url=f"/labs/{raw['id']}",
            provenance="[SANDBOX DATA - GyanSetu Virtual Lab]",
            integration_mode=self.get_integration_mode().value,
            external_metadata={"runtime": "python3.12-stats", "interactive": True},
            status="ACTIVE",
        )


class InternalAdapter(BaseProviderAdapter):
    """Adapter for native GyanSetu assessments, scenarios, and practice drills (LIVE mode)."""

    def __init__(self) -> None:
        super().__init__()
        self._curated_drills: dict[str, dict[str, Any]] = {
            "INT-SCENARIO-01": {
                "id": "INT-SCENARIO-01",
                "title": "MoSPI Field Survey Simulation: Stratified Household Sampling",
                "type": "PRACTICE_SCENARIO",
                "modality": "PRACTICE_SCENARIO",
                "duration_minutes": 60,
                "difficulty": "intermediate",
                "competency_hint": "Sampling Design",
                "subskill_hint": "Stratified sampling",
                "description": "Interactive field survey scenario handling household enumeration discrepancies.",
            },
            "INT-DIAG-01": {
                "id": "INT-DIAG-01",
                "title": "Targeted Diagnostic Assessment: Sampling Design",
                "type": "DIAGNOSTIC",
                "modality": "ASSESSMENT",
                "duration_minutes": 20,
                "difficulty": "intermediate",
                "competency_hint": "Sampling Design",
                "subskill_hint": "Probability sampling",
                "description": "Targeted 3-question adaptive diagnostic to establish baseline competency state.",
            },
        }

    def get_provider_name(self) -> str:
        return "INTERNAL"

    def get_integration_mode(self) -> IntegrationMode:
        return IntegrationMode.LIVE

    def health_check(self) -> ProviderHealth:
        start_time = time.perf_counter()
        fault = self._check_fault_injections()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if fault is not None:
            return ProviderHealth(
                provider=self.get_provider_name(),
                status=HealthStatus.UNAVAILABLE,
                mode=self.get_integration_mode(),
                latency_ms=elapsed_ms,
                resource_count=len(self._curated_drills),
                details=fault.reason,
            )

        return ProviderHealth(
            provider=self.get_provider_name(),
            status=HealthStatus.HEALTHY,
            mode=self.get_integration_mode(),
            latency_ms=elapsed_ms,
            resource_count=len(self._curated_drills),
            details=f"Internal GyanSetu live learning engine online with {len(self._curated_drills)} native items",
        )

    def check_availability(self, resource_id: str | None = None) -> AvailabilityResult:
        fault = self._check_fault_injections(resource_id)
        if fault is not None:
            return fault

        return AvailabilityResult(
            resource_id=resource_id,
            status=AvailabilityStatus.AVAILABLE,
            is_available=True,
            reason="Native internal learning engine online",
        )

    def search_resources(
        self, query: str | None = None, competency: str | None = None
    ) -> list[CanonicalInterventionPayload]:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return []

        results: list[CanonicalInterventionPayload] = []
        for raw in self._curated_drills.values():
            if query and query.lower() not in raw["title"].lower():
                continue
            if competency and competency.lower() not in raw["competency_hint"].lower():
                continue
            results.append(self._normalize_item(raw))
        return results

    def get_resource(self, resource_id: str) -> CanonicalInterventionPayload | None:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return None
        raw = self._curated_drills.get(resource_id)
        if not raw:
            return None
        return self._normalize_item(raw)

    def launch_resource(self, resource_id: str, learner_id: int) -> LaunchResult:
        res = self.check_availability(resource_id)
        if not res.is_available:
            return LaunchResult(
                provider=self.get_provider_name(),
                provider_resource_id=resource_id,
                provider_activity_id=f"act_err_{uuid.uuid4().hex[:8]}",
                learner_id=learner_id,
                integration_mode=self.get_integration_mode().value,
                launch_url=None,
                status="FAILED",
            )

        activity_id = f"int_act_{uuid.uuid4().hex[:10]}"
        launch_url = f"/api/drills/{resource_id}/run/{activity_id}"

        return LaunchResult(
            provider=self.get_provider_name(),
            provider_resource_id=resource_id,
            provider_activity_id=activity_id,
            learner_id=learner_id,
            integration_mode=self.get_integration_mode().value,
            launch_url=launch_url,
            status="ACTIVE",
        )

    def sync_resources(self) -> list[CanonicalInterventionPayload]:
        if not self._simulated_available or self._simulate_timeout or self._simulate_auth_failure:
            return []
        return [self._normalize_item(raw) for raw in self._curated_drills.values()]

    def _normalize_item(self, raw: dict[str, Any]) -> CanonicalInterventionPayload:
        return CanonicalInterventionPayload(
            provider="INTERNAL",
            provider_resource_id=raw["id"],
            title=raw["title"],
            intervention_type=raw["type"],
            modality=raw["modality"],
            duration_minutes=raw["duration_minutes"],
            difficulty=raw["difficulty"],
            competency_hint=raw["competency_hint"],
            subskill_hint=raw["subskill_hint"],
            description=raw["description"],
            external_url=f"/practice/{raw['id']}",
            provenance="[CURATED]",
            integration_mode=self.get_integration_mode().value,
            external_metadata={"system": "native-engine"},
            status="ACTIVE",
        )


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


def list_all_adapters() -> list[InterventionAdapter]:
    return list(_REGISTRY_ADAPTERS.values())
