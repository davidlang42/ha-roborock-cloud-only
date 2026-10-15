"""Support for Roborock Cloud Only vacuums."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntityPlatform

from .const import DOMAIN
from .coordinator import RoborockCloudOnlyDataUpdateCoordinator
from .entity import RoborockCloudOnlyEntity

_LOGGER = logging.getLogger(__name__)

SUPPORT_ROBOROCK = (
    VacuumEntityFeature.START
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.LOCATE
    | VacuumEntityFeature.CLEAN_SPOT
    | VacuumEntityFeature.SET_FAN_SPEED
    | VacuumEntityFeature.SEND_COMMAND
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntityPlatform,
) -> None:
    """Set up Roborock vacuum entities."""
    coordinator: RoborockCloudOnlyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        RoborockCloudOnlyVacuum(coordinator, duid)
        for duid in coordinator.data
    ]
    async_add_entities(entities)


class RoborockCloudOnlyVacuum(RoborockCloudOnlyEntity, StateVacuumEntity):
    """Representation of a Roborock Cloud Only Vacuum cleaner."""

    def __init__(self, coordinator: RoborockCloudOnlyDataUpdateCoordinator, duid: str) -> None:
        """Initialize vacuum entity."""
        super().__init__(coordinator, duid)
        device = coordinator.data[duid]["device"]
        self._attr_unique_id = f"{duid}_vacuum"
        self._attr_name = getattr(device, "name", "Roborock Vacuum")
        self._attr_supported_features = SUPPORT_ROBOROCK

    @property
    def state(self) -> str | None:
        """Return current vacuum state."""
        device_data = self.coordinator.data.get(self._duid, {})
        status = device_data.get("status")
        if status:
            if hasattr(status, "state"):
                return str(status.state)
            if hasattr(status, "state_name"):
                return str(status.state_name)
        return None

    async def async_start(self) -> None:
        """Start cleaning."""
        device = self.coordinator.data[self._duid]["device"]
        if hasattr(device, "v1_properties") and device.v1_properties and hasattr(device.v1_properties, "command"):
            await self.coordinator.async_send_command(device, device.v1_properties.command.app_start)
        else:
            await self.coordinator.async_send_command(device, device.send_command, "app_start")
        await self.coordinator.async_request_refresh()

    async def async_pause(self) -> None:
        """Pause cleaning."""
        device = self.coordinator.data[self._duid]["device"]
        if hasattr(device, "v1_properties") and device.v1_properties and hasattr(device.v1_properties, "command"):
            await self.coordinator.async_send_command(device, device.v1_properties.command.app_pause)
        else:
            await self.coordinator.async_send_command(device, device.send_command, "app_pause")
        await self.coordinator.async_request_refresh()

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop cleaning."""
        device = self.coordinator.data[self._duid]["device"]
        if hasattr(device, "v1_properties") and device.v1_properties and hasattr(device.v1_properties, "command"):
            await self.coordinator.async_send_command(device, device.v1_properties.command.app_stop)
        else:
            await self.coordinator.async_send_command(device, device.send_command, "app_stop")
        await self.coordinator.async_request_refresh()

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Return to dock."""
        device = self.coordinator.data[self._duid]["device"]
        if hasattr(device, "v1_properties") and device.v1_properties and hasattr(device.v1_properties, "command"):
            await self.coordinator.async_send_command(device, device.v1_properties.command.app_charge)
        else:
            await self.coordinator.async_send_command(device, device.send_command, "app_charge")
        await self.coordinator.async_request_refresh()

    async def async_locate(self, **kwargs: Any) -> None:
        """Locate vacuum."""
        device = self.coordinator.data[self._duid]["device"]
        if hasattr(device, "v1_properties") and device.v1_properties and hasattr(device.v1_properties, "command"):
            await self.coordinator.async_send_command(device, device.v1_properties.command.find_me)
        else:
            await self.coordinator.async_send_command(device, device.send_command, "find_me")

    async def async_send_command(
        self, command: str, params: dict[str, Any] | list[Any] | None = None, **kwargs: Any
    ) -> None:
        """Send custom command."""
        device = self.coordinator.data[self._duid]["device"]
        await self.coordinator.async_send_command(
            device, device.send_command, command, params
        )
        await self.coordinator.async_request_refresh()