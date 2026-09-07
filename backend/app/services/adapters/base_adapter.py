from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class IntegrationMode(str, Enum):
    LIVE = "LIVE"
    SANDBOX = "SANDBOX"
    REPLAY = "REPLAY"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    NOT_SUPPORTED = "NOT_SUPPORTED"


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAUTHORIZED = "UNAUTHORIZED"


@dataclass
class ProviderHealth:
    provider: str
    status: HealthStatus
    mode: IntegrationMode
    latency_ms: float = 0.0
    resource_count: int = 0
    details: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status.value,
            "mode": self.mode.value,
            "latency_ms": round(self.latency_ms, 2),
            "resource_count": self.resource_count,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
        }


@dataclass
class AvailabilityResult:
    resource_id: str | None
    status: AvailabilityStatus
    is_available: bool
    reason: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "status": self.status.value,
            "is_available": self.is_available,
            "reason": self.reason,
            "checked_at": self.checked_at.isoformat(),
        }



@dataclass
class CanonicalInterventionPayload:
    provider: str
    provider_resource_id: str
    title: str
    intervention_type: str
    modality: str
    duration_minutes: int
    difficulty: str
    competency_hint: str | None = None
    subskill_hint: str | None = None
    prerequisites_json: str | None = None
    description: str | None = None
    external_url: str | None = None
    provenance: str = "[CURATED]"
    integration_mode: str = "REPLAY"
    version: str = "v1.0"
    last_verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    external_metadata: dict[str, Any] = field(default_factory=dict)
    target_misconception_pattern: str | None = None
    status: str = "ACTIVE"
    priority: int = 1


@dataclass
class LaunchResult:
    provider: str
    provider_resource_id: str
    provider_activity_id: str
    learner_id: int
    integration_mode: str
    launch_url: str | None
    status: str
    launched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_resource_id": self.provider_resource_id,
            "provider_activity_id": self.provider_activity_id,
            "learner_id": self.learner_id,
            "integration_mode": self.integration_mode,
            "launch_url": self.launch_url,
            "status": self.status,
            "launched_at": self.launched_at.isoformat(),
        }


class InterventionAdapter(ABC):
    """Abstract interface for external/internal intervention provider ecosystems."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Name of the provider (e.g. iGOT, NSSTA, TPAC, VIRTUAL_LAB, INTERNAL)."""
        pass

    @abstractmethod
    def get_integration_mode(self) -> IntegrationMode:
        """Active integration mode: LIVE, SANDBOX, or REPLAY."""
        pass

    def get_requested_mode(self) -> IntegrationMode:
        """Requested mode before any fallback."""
        return self.get_integration_mode()

    def get_fallback_reason(self) -> str | None:
        """Explanation if fallback from LIVE to REPLAY occurred."""
        return None

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Inspect provider health and responsiveness."""
        pass

    @abstractmethod
    def check_availability(self, resource_id: str | None = None) -> AvailabilityResult:
        """Check whether the provider or specific resource is currently available."""
        pass

    @abstractmethod
    def search_resources(
        self, query: str | None = None, competency: str | None = None
    ) -> list[CanonicalInterventionPayload]:
        """Search available provider resources matching query or competency."""
        pass

    @abstractmethod
    def get_resource(self, resource_id: str) -> CanonicalInterventionPayload | None:
        """Fetch normalized resource metadata from the provider."""
        pass

    @abstractmethod
    def launch_resource(self, resource_id: str, learner_id: int) -> LaunchResult:
        """Launch or reference external resource, creating a unique provider activity ID."""
        pass

    @abstractmethod
    def sync_resources(self) -> list[CanonicalInterventionPayload]:
        """Harvest raw resources and normalize into canonical payloads."""
        pass

    # Dynamic failure simulation hooks for resilience testing
    @abstractmethod
    def set_simulated_availability(self, available: bool) -> None:
        pass

    def simulate_timeout(self, enable: bool = True) -> None:
        pass

    def simulate_auth_failure(self, enable: bool = True) -> None:
        pass
