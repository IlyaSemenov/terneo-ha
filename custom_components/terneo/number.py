"""Number platform for Terneo integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    PARAM_BRIGHTNESS,
    PARAM_HYSTERESIS,
    PARAM_LOWER_AIR_LIMIT,
    PARAM_LOWER_LIMIT,
    PARAM_MANUAL_AIR,
    PARAM_MANUAL_FLOOR_TEMPERATURE,
    PARAM_UPPER_AIR_LIMIT,
    PARAM_UPPER_LIMIT,
)
from .coordinator import TerneoCoordinator
from .device import TerneoDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Terneo number entities."""
    coordinator: TerneoCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for serial_number, device in coordinator.devices.items():
        entities.extend([
            TerneoTemperatureNumber(
                coordinator, device, serial_number, "manual_floor_temp",
                PARAM_MANUAL_FLOOR_TEMPERATURE, "Manual Floor Temperature",
                5, 45, UnitOfTemperature.CELSIUS
            ),
            TerneoTemperatureNumber(
                coordinator, device, serial_number, "manual_air_temp",
                PARAM_MANUAL_AIR, "Manual Air Temperature",
                5, 35, UnitOfTemperature.CELSIUS
            ),
            TerneoTemperatureNumber(
                coordinator, device, serial_number, "floor_temp_min",
                PARAM_LOWER_LIMIT, "Floor Temperature Minimum",
                5, 45, UnitOfTemperature.CELSIUS
            ),
            TerneoTemperatureNumber(
                coordinator, device, serial_number, "floor_temp_max",
                PARAM_UPPER_LIMIT, "Floor Temperature Maximum",
                5, 45, UnitOfTemperature.CELSIUS
            ),
            TerneoTemperatureNumber(
                coordinator, device, serial_number, "air_temp_min",
                PARAM_LOWER_AIR_LIMIT, "Air Temperature Minimum",
                5, 35, UnitOfTemperature.CELSIUS
            ),
            TerneoTemperatureNumber(
                coordinator, device, serial_number, "air_temp_max",
                PARAM_UPPER_AIR_LIMIT, "Air Temperature Maximum",
                5, 35, UnitOfTemperature.CELSIUS
            ),
            TerneoNumber(
                coordinator, device, serial_number, "brightness",
                PARAM_BRIGHTNESS, "Brightness", 0, 9, None, "mdi:brightness-6"
            ),
            TerneoNumber(
                coordinator, device, serial_number, "hysteresis",
                PARAM_HYSTERESIS, "Hysteresis", 1, 50, "0.1°C", "mdi:thermometer-lines",
                0.1, True
            ),
        ])

    async_add_entities(entities)


class TerneoNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Terneo number entity."""

    def __init__(
        self,
        coordinator: TerneoCoordinator,
        device: TerneoDevice,
        serial_number: str,
        number_type: str,
        param_id: int,
        name: str,
        min_value: float,
        max_value: float,
        unit: Optional[str],
        icon: str,
        step: float = 1.0,
        disabled_by_default: bool = False,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device = device
        self._serial_number = serial_number
        self._number_type = number_type
        self._param_id = param_id
        self._attr_unique_id = f"{serial_number}_{number_type}"
        self._attr_name = name
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_mode = NumberMode.BOX

        if disabled_by_default:
            self._attr_entity_registry_enabled_default = False

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._serial_number)},
            "name": f"Terneo {self._serial_number[-8:]}",  # Use last 8 chars of serial
            "manufacturer": "Terneo",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        device_data = self.coordinator.data.get(self._serial_number, {})
        return device_data.get("available", False)

    @property
    def native_value(self) -> Optional[float]:
        """Return the current value."""
        value = self._device.get_parameter(self._param_id)
        if value is not None:
            # Handle hysteresis which is in 1/10 degrees
            if self._param_id == PARAM_HYSTERESIS:
                return float(value) / 10.0
            return float(value)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        # Handle hysteresis which needs to be in 1/10 degrees
        if self._param_id == PARAM_HYSTERESIS:
            value = int(value * 10)
        else:
            value = int(value)

        parameters = {self._param_id: value}
        await self.coordinator.set_device_parameters(self._serial_number, parameters)


class TerneoTemperatureNumber(TerneoNumber):
    """Temperature number entity for Terneo device."""

    def __init__(
        self,
        coordinator: TerneoCoordinator,
        device: TerneoDevice,
        serial_number: str,
        number_type: str,
        param_id: int,
        name: str,
        min_value: float,
        max_value: float,
        unit: str,
    ) -> None:
        """Initialize the temperature number entity."""
        super().__init__(
            coordinator, device, serial_number, number_type, param_id, name,
            min_value, max_value, unit, "mdi:thermometer", 1.0,
            number_type.startswith(("manual_", "floor_temp_", "air_temp_"))
        )
