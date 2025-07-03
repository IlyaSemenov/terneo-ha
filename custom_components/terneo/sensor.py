"""Sensor platform for Terneo integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    FLAG_AIR_SENSOR_BREAK,
    FLAG_AIR_SENSOR_SHORT,
    FLAG_FLOOR_SENSOR_BREAK,
    FLAG_FLOOR_SENSOR_SHORT,
    FLAG_HEATING_STATE,
    FLAG_OVERHEAT,
    FLAG_PROPORTIONAL_MODE,
    FLAG_WINDOW_OPEN,
    OTHER_WIFI_SIGNAL,
    PARAM_POWER,
    TEMP_AIR,
    TEMP_FLOOR,
    TEMP_MCU,
    TEMP_OVERHEAT,
    TEMP_SETPOINT,
)
from .coordinator import TerneoCoordinator
from .device import TerneoDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Terneo sensor entities."""
    coordinator: TerneoCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for serial_number, device in coordinator.devices.items():
        # Temperature sensors
        entities.extend([
            TerneoTemperatureSensor(
                coordinator, device, serial_number, "floor_temperature",
                TEMP_FLOOR, "Floor Temperature"
            ),
            TerneoTemperatureSensor(
                coordinator, device, serial_number, "air_temperature",
                TEMP_AIR, "Air Temperature"
            ),
            TerneoTemperatureSensor(
                coordinator, device, serial_number, "setpoint_temperature",
                TEMP_SETPOINT, "Setpoint Temperature"
            ),
            TerneoTemperatureSensor(
                coordinator, device, serial_number, "mcu_temperature",
                TEMP_MCU, "MCU Temperature"
            ),
            TerneoTemperatureSensor(
                coordinator, device, serial_number, "overheat_temperature",
                TEMP_OVERHEAT, "Overheat Sensor Temperature"
            ),
        ])

        # WiFi signal sensor
        entities.append(
            TerneoWiFiSensor(coordinator, device, serial_number)
        )

        # Power sensor
        entities.append(
            TerneoPowerSensor(coordinator, device, serial_number)
        )

        # Status sensors
        entities.extend([
            TerneoStatusSensor(
                coordinator, device, serial_number, "heating_state",
                FLAG_HEATING_STATE, "Heating State"
            ),
            TerneoStatusSensor(
                coordinator, device, serial_number, "floor_sensor_error",
                FLAG_FLOOR_SENSOR_BREAK, "Floor Sensor Break"
            ),
            TerneoStatusSensor(
                coordinator, device, serial_number, "floor_sensor_short",
                FLAG_FLOOR_SENSOR_SHORT, "Floor Sensor Short"
            ),
            TerneoStatusSensor(
                coordinator, device, serial_number, "air_sensor_error",
                FLAG_AIR_SENSOR_BREAK, "Air Sensor Break"
            ),
            TerneoStatusSensor(
                coordinator, device, serial_number, "air_sensor_short",
                FLAG_AIR_SENSOR_SHORT, "Air Sensor Short"
            ),
            TerneoStatusSensor(
                coordinator, device, serial_number, "overheat",
                FLAG_OVERHEAT, "Overheat"
            ),
            TerneoStatusSensor(
                coordinator, device, serial_number, "window_open",
                FLAG_WINDOW_OPEN, "Window Open Detection"
            ),
            TerneoStatusSensor(
                coordinator, device, serial_number, "proportional_mode",
                FLAG_PROPORTIONAL_MODE, "Proportional Mode"
            ),
        ])

    async_add_entities(entities)


class TerneoBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Terneo sensors."""

    def __init__(
        self,
        coordinator: TerneoCoordinator,
        device: TerneoDevice,
        serial_number: str,
        sensor_type: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device = device
        self._serial_number = serial_number
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{serial_number}_{sensor_type}"
        self._attr_name = name

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


class TerneoTemperatureSensor(TerneoBaseSensor):
    """Temperature sensor for Terneo device."""

    def __init__(
        self,
        coordinator: TerneoCoordinator,
        device: TerneoDevice,
        serial_number: str,
        sensor_type: str,
        temp_index: int,
        name: str,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, device, serial_number, sensor_type, name)
        self._temp_index = temp_index
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> Optional[float]:
        """Return the temperature value."""
        temp = self._device.get_temperature(self._temp_index)
        if temp is not None:
            return round(temp, 1)
        return None


class TerneoWiFiSensor(TerneoBaseSensor):
    """WiFi signal sensor for Terneo device."""

    def __init__(
        self,
        coordinator: TerneoCoordinator,
        device: TerneoDevice,
        serial_number: str,
    ) -> None:
        """Initialize the WiFi sensor."""
        super().__init__(coordinator, device, serial_number, "wifi_signal", "WiFi Signal")
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "dBm"
        self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> Optional[int]:
        """Return the WiFi signal strength."""
        return self._device.get_telemetry_value("o", OTHER_WIFI_SIGNAL)

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        signal = self.native_value
        if signal is None:
            return "mdi:wifi-off"
        elif signal > -50:
            return "mdi:wifi-strength-4"
        elif signal > -60:
            return "mdi:wifi-strength-3"
        elif signal > -70:
            return "mdi:wifi-strength-2"
        else:
            return "mdi:wifi-strength-1"


class TerneoPowerSensor(TerneoBaseSensor):
    """Power sensor for Terneo device."""

    def __init__(
        self,
        coordinator: TerneoCoordinator,
        device: TerneoDevice,
        serial_number: str,
    ) -> None:
        """Initialize the power sensor."""
        super().__init__(coordinator, device, serial_number, "power", "Power")
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self) -> Optional[int]:
        """Return the power value."""
        power_param = self._device.get_parameter(PARAM_POWER)
        if power_param is not None:
            # Convert from device units to watts
            # P=(power<=150)?(power*10):(1500+power*20)
            if power_param <= 150:
                return power_param * 10
            else:
                return 1500 + (power_param * 20)
        return None


class TerneoStatusSensor(TerneoBaseSensor):
    """Status sensor for Terneo device."""

    def __init__(
        self,
        coordinator: TerneoCoordinator,
        device: TerneoDevice,
        serial_number: str,
        sensor_type: str,
        flag_index: int,
        name: str,
    ) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator, device, serial_number, sensor_type, name)
        self._flag_index = flag_index
        self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> Optional[str]:
        """Return the status value."""
        flag_value = self._device.get_flag(self._flag_index)
        if flag_value is None:
            return None
        return "on" if flag_value else "off"

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        value = self.native_value

        if self._sensor_type == "heating_state":
            return "mdi:radiator" if value == "on" else "mdi:radiator-off"
        elif "sensor" in self._sensor_type and "error" in self._sensor_type:
            return "mdi:alert-circle" if value == "on" else "mdi:check-circle"
        elif "sensor" in self._sensor_type and "short" in self._sensor_type:
            return "mdi:alert-circle" if value == "on" else "mdi:check-circle"
        elif self._sensor_type == "overheat":
            return "mdi:thermometer-alert" if value == "on" else "mdi:thermometer"
        elif self._sensor_type == "window_open":
            return "mdi:window-open" if value == "on" else "mdi:window-closed"
        elif self._sensor_type == "proportional_mode":
            return "mdi:sine-wave" if value == "on" else "mdi:square-wave"

        return "mdi:information"
