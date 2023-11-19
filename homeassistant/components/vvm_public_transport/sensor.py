"""VVM Stop departure monitor as a sensor."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .vvm_access import VVMStopMonitorHA

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up VVM Stop entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            VVMStopDepartureNearest(coordinator),
            VVMStopDepartureNearestLeft(coordinator),
            VVMStopDepartureNearestDelay(coordinator),
        ]
    )


class VVMStopSensorEntityBase(
    CoordinatorEntity[DataUpdateCoordinator[VVMStopMonitorHA]], SensorEntity
):
    """Base functionality for all VVM sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_id) -> None:
        """Construct the base class."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.data.stop_id}_{sensor_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.data.stop_id)},
            name="VVM Public Transport Stop",
            manufacturer="VVM",
        )
        self._name = sensor_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name


class VVMStopDepartureNearest(VVMStopSensorEntityBase):
    """Entity representing a public transport stop to monitor for departures."""

    def __init__(self, coordinator: DataUpdateCoordinator[VVMStopMonitorHA]) -> None:
        """Construct the nearest sensor."""
        super().__init__(coordinator, "Nearest Summary")
        self.extra = {
            "departures": self.coordinator.data.departures,
            "last_updated": self.coordinator.data.last_updated,
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        return self.extra

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.nearest_summary


class VVMStopDepartureNearestLeft(VVMStopSensorEntityBase):
    """Entity representing a public transport stop to monitor for departures."""

    def __init__(self, coordinator: DataUpdateCoordinator[VVMStopMonitorHA]) -> None:
        """Construct the Nearest Left sensor."""
        super().__init__(coordinator, "Nearest Left")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.nearest_left_minutes


class VVMStopDepartureNearestDelay(VVMStopSensorEntityBase):
    """Entity representing a public transport stop to monitor for departures."""

    def __init__(self, coordinator: DataUpdateCoordinator[VVMStopMonitorHA]) -> None:
        """Construct the Nearest Delay sensor."""
        super().__init__(coordinator, "Nearest Delay")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.nearest_delay_minutes
