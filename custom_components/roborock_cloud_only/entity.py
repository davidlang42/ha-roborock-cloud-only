"""Base entity for Roborock Cloud Only integration."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RoborockCloudOnlyDataUpdateCoordinator


class RoborockCloudOnlyEntity(CoordinatorEntity[RoborockCloudOnlyDataUpdateCoordinator]):
    """Base class for Roborock Cloud Only entities."""

    def __init__(self, coordinator: RoborockCloudOnlyDataUpdateCoordinator, duid: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._duid = duid

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device registry information."""
        device_info = self.coordinator.data.get(self._duid, {})
        device = device_info.get("device")
        name = getattr(device, "name", "Roborock Vacuum")
        model = getattr(device, "model", "Unknown")
        return {
            "identifiers": {(DOMAIN, self._duid)},
            "name": name,
            "manufacturer": "Roborock",
            "model": model,
        }