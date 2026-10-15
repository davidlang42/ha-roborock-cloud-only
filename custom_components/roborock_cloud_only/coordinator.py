"""DataUpdateCoordinator combining group updates and cloud rate limiting."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from roborock.api import RoborockApiClient
from roborock.devices.device_manager import UserParams, create_device_manager
from roborock.exceptions import RoborockException
from roborock.models import UserData

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_USER_DATA, DOMAIN, RATE_LIMIT_UPDATE_COOLDOWN_MINUTES
from .rate_limiter import RoborockRateLimiter

_LOGGER = logging.getLogger(__name__)


class RoborockCloudOnlyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator handling group updates for all cloud vacuums."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self.username = entry.data[CONF_USERNAME]
        self.user_data_dict = entry.data[CONF_USER_DATA]
        self.rate_limiter = RoborockRateLimiter()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=RATE_LIMIT_UPDATE_COOLDOWN_MINUTES),
        )
        self.api_client: RoborockApiClient | None = None
        self.device_manager: Any | None = None
        self.devices: list[Any] = []

    async def async_setup(self) -> None:
        """Set up cloud client and device manager."""
        self.api_client = RoborockApiClient(username=self.username)

        user_data = (
            UserData.from_dict(self.user_data_dict)
            if hasattr(UserData, "from_dict")
            else self.user_data_dict
        )

        user_params = UserParams(username=self.username, user_data=user_data)
        self.device_manager = await create_device_manager(user_params)

        await self._async_update_data()

    async def _async_update_data(self) -> dict[str, Any]:
        """Perform a single group update fetching information for all vacuums at once."""
        now = datetime.now(timezone.utc)

        # Update polling interval based on current rate-limiter cooldown formula
        cooldown_mins = self.rate_limiter.get_update_cooldown(now)
        self.update_interval = timedelta(minutes=cooldown_mins)

        try:
            self.rate_limiter.record_call(now)

            # Combined group update pulling home data and all devices in one pass
            await self.device_manager.get_home_data()
            devices = await self.device_manager.get_devices()
            self.devices = devices

            device_data = {}
            for device in devices:
                status = None
                if hasattr(device, "v1_properties") and device.v1_properties:
                    if hasattr(device.v1_properties, "status"):
                        try:
                            await device.v1_properties.status.refresh()
                            status = device.v1_properties.status
                        except Exception:
                            pass
                elif hasattr(device, "get_status"):
                    try:
                        status = await device.get_status()
                    except Exception:
                        pass

                device_data[device.duid] = {
                    "device": device,
                    "status": status,
                    "model": getattr(device, "model", "Unknown"),
                }

            _LOGGER.debug("Roborock cloud group update successful. Next interval: %.2f mins", cooldown_mins)
            return device_data
        except RoborockException as err:
            raise UpdateFailed(f"Cloud communication error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected update error: {err}") from err

    async def async_send_command(self, device: Any, command_func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute a command respecting strict command rate-limiting rules."""
        now = datetime.now(timezone.utc)
        if not self.rate_limiter.can_send_command(now):
            raise RoborockException("Command rate limit or cooldown active. Command skipped.")

        self.rate_limiter.record_command(now)
        _LOGGER.debug("Executing cloud command with rate limiter compliance.")
        return await command_func(*args, **kwargs)