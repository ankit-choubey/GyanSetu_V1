from abc import ABC, abstractmethod
from typing import Any


class InterventionAdapter(ABC):
    """Abstract interface for external/internal intervention provider ecosystems."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Name of the provider (e.g. iGOT, NSSTA, TPAC, VIRTUAL_LAB, INTERNAL)."""
        pass

    @abstractmethod
    def get_integration_mode(self) -> str:
        """Integration mode: 'LIVE', 'SANDBOX', or 'REPLAY'."""
        pass

    @abstractmethod
    def check_availability(self, resource_id: str | None = None) -> bool:
        """Check whether the provider or specific resource is currently available."""
        pass

    @abstractmethod
    def fetch_resource(self, resource_id: str) -> dict[str, Any] | None:
        """Fetch resource metadata from the provider catalog/replay store."""
        pass
