"""Support for Roborock Cloud Only sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    """Set up sensors."""
    coordinator: RoborockCloudOnlyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for duid in coordinator.data:
        entities.append(RoborockCloudOnlyBatterySensor(coordinator, duid))
        entities.append(RoborockCloudOnlyCleanAreaSensor(coordinator, duid))
        entities.append(RoborockCloudOnlyCleanTimeSensor(coordinator, duid))

    async_add_entities(entities)


class RoborockCloudOnlyBatterySensor(RoborockCloudOnlyEntity, SensorEntity):
    """Representation of battery level sensor."""

    def __init__(self, coordinator: RoborockCloudOnlyDataUpdateCoordinator, duid: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, duid)
        device = coordinator.data[duid]["device"]
        self._attr_unique_id = f"{duid}_battery"
        self._attr_name = f"{getattr(device, 'name', 'Roborock')} Battery"
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:battery"

    @property
    def native_value(self) -> int | None:
        """Return battery percentage."""
        device_data = self.coordinator.data.get(self._duid, {})
        status = device_data.get("status")
        if status and hasattr(status, "battery"):
            return int(status.battery)
        return None


class RoborockCloudOnlyCleanAreaSensor(RoborockCloudOnlyEntity, SensorEntity):
    """Representation of clean area sensor."""

    def __init__(self, coordinator: RoborockCloudOnlyDataUpdateCoordinator, duid: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, duid)
        device = coordinator.data[duid]["device"]
        self._attr_unique_id = f"{duid}_clean_area"
        self._attr_name = f"{getattr(device, 'name', 'Roborock')} Clean Area"
        self._attr_native_unit_of_measurement = "m²"
        self._attr_icon = "mdi:floor-plan"

    @property
    def native_value(self) -> float | None:
        """Return clean area in square meters."""
        device_data = self.coordinator.data.get(self._duid, {})
        status = device_data.get("status")
        if status and hasattr(status, "clean_area"):
            return round(float(status.clean_area) / 1000000.0, 2)
        return None


class RoborockCloudOnlyCleanTimeSensor(RoborockCloudOnlyEntity, SensorEntity):
    """Representation of clean time sensor."""

    def __init__(self, coordinator: RoborockCloudOnlyDataUpdateCoordinator, duid: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, duid)
        device = coordinator.data[duid]["device"]
        self._attr_unique_id = f"{duid}_clean_time"
        self._attr_name = f"{getattr(device, 'name', 'Roborock')} Clean Time"
        self._attr_native_unit_of_measurement = "min"
        self._attr_icon = "mdi:timer"

    @property
    def native_value(self) -> int | None:
        """Return clean time in minutes."""
        device_data = self.coordinator.data.get(self._duid, {})
        status = device_data.get("status")
        if status and hasattr(status, "clean_time"):
            return int(status.clean_time) // 60
        return None