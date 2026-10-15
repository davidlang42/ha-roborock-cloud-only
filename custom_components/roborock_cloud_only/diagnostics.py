"""Diagnostics support for Roborock Cloud Only."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import RoborockCloudOnlyDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: RoborockCloudOnlyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    diag_data = {
        "api_calls_count": len(coordinator.rate_limiter._api_calls),
        "recent_api_calls": [t.isoformat() for t in coordinator.rate_limiter._api_calls],
        "devices": [],
    }

    for duid, device_info in coordinator.data.items():
        device = device_info.get("device")
        status = device_info.get("status")
        diag_data["devices"].append({
            "duid": duid,
            "model": getattr(device, "model", "Unknown"),
            "name": getattr(device, "name", "Unknown"),
            "status_attributes": {
                attr: getattr(status, attr)
                for attr in dir(status)
                if not attr.startswith("_") and not callable(getattr(status, attr))
            } if status else None,
        })

    return diag_data