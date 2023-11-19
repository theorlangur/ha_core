"""Config flow for vvm_transport integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_FILTER_DIRECTION,
    CONF_FILTER_NUM,
    CONF_FILTER_TYPE,
    CONF_STATION,
    CONF_STOP_ID,
    CONF_TIMEFRAME,
    DOMAIN,
)
from .vvm_access import VVMAccessApi, VVMStopMonitor

_LOGGER = logging.getLogger(__name__)

STEP_STATION_DATA_SCHEMA = vol.Schema({vol.Required(CONF_STATION): str})


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    stop_id = data[CONF_STOP_ID]
    valid_stop = await VVMStopMonitor.is_stop_id_valid(stop_id)
    if not valid_stop[0]:
        raise InvalidStopId

    # Return info that you want to store in the config entry.
    return {
        "title": valid_stop[1],
        "stop_id": stop_id,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for vvm_transport."""

    VERSION = 1

    def __init__(self):
        """Construct config flow."""
        super().__init__()
        self.stops = []
        self.station_names = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # info = await validate_input(self.hass, user_input)
                self.stops = await VVMAccessApi.get_stop_list(user_input[CONF_STATION])
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if len(self.stops) > 0:
                    self.station_names = [x["name"] for x in self.stops]
                    return await self.async_step_station_select()
                return self.async_show_form(
                    step_id="user",
                    data_schema=STEP_STATION_DATA_SCHEMA,
                    errors=errors,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_STATION_DATA_SCHEMA, errors=errors
        )

    async def async_step_station_select(self, user_input=None):
        """Handle the step where the user inputs his/her station."""

        schema = vol.Schema(
            {vol.Required(CONF_STATION): vol.In(list(self.station_names))}
        )

        if user_input is None:
            return self.async_show_form(step_id="station_select", data_schema=schema)
        stops = [
            item["id"]
            for item in self.stops
            if item["name"] == user_input[CONF_STATION]
        ]
        title = user_input[CONF_STATION]
        return self.async_create_entry(
            title=title,
            data={
                CONF_STOP_ID: stops[0],
                CONF_TIMEFRAME: 15,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize VVM Departures options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        self.departure_filters: dict[str, Any] = {}

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        vvm = self.hass.data[DOMAIN][self.config_entry.entry_id]

        if user_input is not None and not errors:
            options = {
                CONF_FILTER_TYPE: user_input[CONF_FILTER_TYPE],
                CONF_FILTER_NUM: user_input[CONF_FILTER_NUM],
                CONF_FILTER_DIRECTION: user_input[CONF_FILTER_DIRECTION],
            }
            # init here filters
            vvm.data.filter_types = user_input[CONF_FILTER_TYPE]
            vvm.data.filter_nums = user_input[CONF_FILTER_NUM]
            vvm.data.filter_direction = user_input[CONF_FILTER_DIRECTION]
            return self.async_create_entry(title="", data=options)

        if CONF_FILTER_TYPE in self.config_entry.options:
            old_filter_types = self.config_entry.options.get(CONF_FILTER_TYPE)
        else:
            old_filter_types = []

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TIMEFRAME,
                        default=self.config_entry.options.get(CONF_TIMEFRAME, 15),
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_FILTER_TYPE, default=old_filter_types
                    ): cv.multi_select(
                        [
                            "Straßenbahn",
                            "Bus",
                            "Regionalbus",
                            "Nachtbus",
                            "Ersatzverkehr",
                            "S-Bahn",
                            "U-Bahn",
                        ]
                    ),
                    vol.Optional(
                        CONF_FILTER_NUM,
                        default=self.config_entry.options.get(CONF_FILTER_NUM, "*"),
                    ): str,
                    vol.Optional(
                        CONF_FILTER_DIRECTION,
                        default=self.config_entry.options.get(
                            CONF_FILTER_DIRECTION, ""
                        ),
                    ): str,
                }
            ),
            errors=errors,
        )


class InvalidStopId(HomeAssistantError):
    """Error happens when the stop id is invalid."""
