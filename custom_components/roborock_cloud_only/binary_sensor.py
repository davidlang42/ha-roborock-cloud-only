"""Support for Roborock Cloud Only binary sensors."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntityPlatform

from .const import DOMAIN
from .coordinator import RoborockCloudOnlyDataUpdateCoordinator
from .entity import RoborockCloudOnlyEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntityPlatform,
) -> None:
    """Set up binary sensors."""
    coordinator: RoborockCloudOnlyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        RoborockCloudOnlyOnlineBinarySensor(coordinator, duid)
        for duid in coordinator.data
    ]
    async_add_entities(entities)


class RoborockCloudOnlyOnlineBinarySensor(RoborockCloudOnlyEntity, BinarySensorEntity):
    """Representation of vacuum online status binary sensor."""

    def __init__(self, coordinator: RoborockCloudOnlyDataUpdateCoordinator, duid: str) -> None:
        """Initialize binary sensor."""
        super().__init__(coordinator, duid)
        device = coordinator.data[duid]["device"]
        self._attr_unique_id = f"{duid}_online"
        self._attr_name = f"{getattr(device, 'name', 'Roborock')} Online"
        self._attr_icon = "mdi:wifi"

    @property
    def is_on(self) -> bool | None:
        """Return true if device is online."""
        device_info = self.coordinator.data.get(self._duid, {})
        device = device_info.get("device")
        if device and hasattr(device, "in_use"):
            return bool(device.in_use)
        return True