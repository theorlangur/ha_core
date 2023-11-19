"""Config flow for vvm_transport integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_DIRECTION, CONF_STOP_ID, CONF_TIMEFRAME, DOMAIN
from .vvm_access import VVMStopMonitor

_LOGGER = logging.getLogger(__name__)

STEP_STOP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STOP_ID): str,
        vol.Required(CONF_TIMEFRAME, default=15): int,
        vol.Optional(CONF_DIRECTION, default=""): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_STOP_DATA_SCHEMA with values provided by the user.
    """

    if data["timeframe"] <= 0:
        raise InvalidTimeframe

    stop_id = data["stop_id"]
    valid_stop = await VVMStopMonitor.is_stop_id_valid(stop_id)
    if not valid_stop[0]:
        raise InvalidStopId

    # Return info that you want to store in the config entry.
    return {
        "title": valid_stop[1],
        "stop_id": stop_id,
        "timeframe": data["timeframe"],
        "direction": data["direction"],
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for vvm_transport."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidStopId:
                errors["base"] = "Invalid stop id:" + user_input["stop_id"]
            except InvalidTimeframe:
                errors["base"] = "Invalid time frame: cannot be <= 0"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input["stop_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_STOP_DATA_SCHEMA, errors=errors
        )


class InvalidStopId(HomeAssistantError):
    """Error to indicate that the stop id is invalid."""


class InvalidTimeframe(HomeAssistantError):
    """Error to indicate that the timeframe is invalid."""
