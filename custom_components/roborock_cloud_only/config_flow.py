"""Config flow for Roborock Cloud Only integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from roborock.exceptions import RoborockException
from roborock.web_api import RoborockApiClient

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_USER_DATA, DOMAIN

_LOGGER = logging.getLogger(__name__)


class RoborockCloudOnlyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Roborock Cloud Only."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._client: RoborockApiClient | None = None
        self._username: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - email entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._client = RoborockApiClient(username=self._username)
            try:
                await self._client.request_code()
            except RoborockException:
                _LOGGER.exception("Failed to request verification code")
                errors["base"] = "invalid_email"
            except Exception:
                _LOGGER.exception("Unexpected error requesting code")
                errors["base"] = "unknown"
            else:
                return await self.async_step_code()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_USERNAME): str}),
            errors=errors,
        )

    async def async_step_code(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the verification code step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            code = user_input["code"]
            try:
                user_data = await self._client.code_login_v4(code)
            except RoborockException:
                _LOGGER.exception("Failed to login with verification code")
                errors["base"] = "invalid_code"
            except Exception:
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(self._username)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=self._username,
                    data={
                        CONF_USERNAME: self._username,
                        CONF_USER_DATA: user_data.as_dict()
                        if hasattr(user_data, "as_dict")
                        else user_data,
                    },
                )

        return self.async_show_form(
            step_id="code",
            data_schema=vol.Schema({vol.Required("code"): str}),
            errors=errors,
        )