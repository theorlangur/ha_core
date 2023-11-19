"""The vvm_transport integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_DIRECTION, CONF_STOP_ID, CONF_TIMEFRAME, DOMAIN
from .vvm_access import VVMStopMonitorHA

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up vvm_transport from a config entry."""
    api = VVMStopMonitorHA(
        entry.data[CONF_STOP_ID], entry.data[CONF_TIMEFRAME], entry.data[CONF_DIRECTION]
    )

    async def async_update_data() -> VVMStopMonitorHA:
        """Fetch data from the API."""
        await api.async_update()
        return api

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="vvm_public_transport_stop",
        update_method=async_update_data,
        update_interval=timedelta(minutes=1),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
