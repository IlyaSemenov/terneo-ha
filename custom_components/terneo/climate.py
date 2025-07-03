"""Climate platform for Terneo integration."""

import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONTROL_TYPE_AIR,
    CONTROL_TYPE_EXTENDED,
    CONTROL_TYPE_FLOOR,
    DOMAIN,
    FLAG_HEATING_STATE,
    FLAG_POWER_OFF,
    MGMT_TYPE_AWAY,
    MGMT_TYPE_MANUAL,
    MGMT_TYPE_SCHEDULE,
    MGMT_TYPE_TEMP,
    MODE_CONTROL_TYPE,
    MODE_MANAGEMENT_TYPE,
    MODE_MANUAL,
    MODE_SCHEDULE,
    PARAM_AWAY_AIR_TEMPERATURE,
    PARAM_AWAY_FLOOR_TEMPERATURE,
    PARAM_CONTROL_TYPE,
    PARAM_LOWER_AIR_LIMIT,
    PARAM_LOWER_LIMIT,
    PARAM_MANUAL_AIR,
    PARAM_MANUAL_FLOOR_TEMPERATURE,
    PARAM_MODE,
    PARAM_POWER_OFF,
    PARAM_UPPER_AIR_LIMIT,
    PARAM_UPPER_LIMIT,
    TEMP_AIR,
    TEMP_FLOOR,
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
    """Set up Terneo climate entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for serial_number in coordinator.devices:
        entities.append(TerneoClimate(coordinator, serial_number))

    async_add_entities(entities)


class TerneoClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Terneo climate entity."""

    def __init__(
        self,
        coordinator: TerneoCoordinator,
        serial_number: str,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._attr_unique_id = f"{serial_number}_climate"
        self._attr_name = None  # Use device name
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_precision = PRECISION_WHOLE
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_preset_modes = ["schedule", "manual", "away", "temporary"]

    @property
    def _device(self) -> TerneoDevice:
        """Get the device from coordinator."""
        return self.coordinator.get_device(self._serial_number)

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._serial_number)},
            "name": f"Terneo {self._serial_number[-8:]}",  # Use last 8 chars of serial
            "manufacturer": "Terneo",
            "model": self._get_device_model(),
            "sw_version": self._get_software_version(),
        }

    def _get_device_model(self) -> str:
        """Get device model from hardware type."""
        hw_type = getattr(self._device, "hw_type", "unknown")
        return f"Terneo {hw_type.upper()}" if hw_type != "unknown" else "Terneo"

    def _get_software_version(self) -> Optional[str]:
        """Get software version if available."""
        # This would need to be implemented if version info is available
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        device_data = self.coordinator.data.get(self._serial_number, {})
        return device_data.get("available", False)

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        control_type = self._get_control_type()

        if control_type == CONTROL_TYPE_AIR:
            return self._device.get_temperature(TEMP_AIR)
        elif control_type == CONTROL_TYPE_FLOOR:
            return self._device.get_temperature(TEMP_FLOOR)
        elif control_type == CONTROL_TYPE_EXTENDED:
            # In extended mode, show air temperature as current
            return self._device.get_temperature(TEMP_AIR)

        # Default to floor temperature
        return self._device.get_temperature(TEMP_FLOOR)

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the target temperature."""
        setpoint = self._device.get_temperature(TEMP_SETPOINT)
        if setpoint is not None:
            return round(setpoint)
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if self._device.get_flag(FLAG_POWER_OFF):
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action."""
        if self._device.get_flag(FLAG_POWER_OFF):
            return HVACAction.OFF

        if self._device.get_flag(FLAG_HEATING_STATE):
            return HVACAction.HEATING

        return HVACAction.IDLE

    @property
    def preset_mode(self) -> Optional[str]:
        """Return current preset mode."""
        mgmt_type = self._device.get_mode(MODE_MANAGEMENT_TYPE)

        if mgmt_type == MGMT_TYPE_SCHEDULE:
            return "schedule"
        elif mgmt_type == MGMT_TYPE_MANUAL:
            return "manual"
        elif mgmt_type == MGMT_TYPE_AWAY:
            return "away"
        elif mgmt_type == MGMT_TYPE_TEMP:
            return "temporary"

        return None

    @property
    def min_temp(self) -> float:
        """Return minimum temperature."""
        control_type = self._get_control_type()

        if control_type == CONTROL_TYPE_AIR:
            limit = self._device.get_parameter(PARAM_LOWER_AIR_LIMIT)
            return float(limit) if limit is not None else 5.0
        else:
            limit = self._device.get_parameter(PARAM_LOWER_LIMIT)
            return float(limit) if limit is not None else 5.0

    @property
    def max_temp(self) -> float:
        """Return maximum temperature."""
        control_type = self._get_control_type()

        if control_type == CONTROL_TYPE_AIR:
            limit = self._device.get_parameter(PARAM_UPPER_AIR_LIMIT)
            return float(limit) if limit is not None else 35.0
        else:
            limit = self._device.get_parameter(PARAM_UPPER_LIMIT)
            return float(limit) if limit is not None else 45.0

    def _get_control_type(self) -> int:
        """Get current control type."""
        return self._device.get_mode(MODE_CONTROL_TYPE) or CONTROL_TYPE_FLOOR

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        temperature = int(temperature)
        control_type = self._get_control_type()
        mgmt_type = self._device.get_mode(MODE_MANAGEMENT_TYPE)

        # Determine which parameter to set based on current mode and control type
        parameters = {}

        if mgmt_type == MGMT_TYPE_AWAY:
            # Away mode
            if control_type == CONTROL_TYPE_AIR:
                parameters[PARAM_AWAY_AIR_TEMPERATURE] = temperature
            else:
                parameters[PARAM_AWAY_FLOOR_TEMPERATURE] = temperature
        else:
            # Manual mode (switch to manual if not already)
            if mgmt_type != MGMT_TYPE_MANUAL:
                parameters[PARAM_MODE] = MODE_MANUAL

            if control_type == CONTROL_TYPE_AIR:
                parameters[PARAM_MANUAL_AIR] = temperature
            else:
                parameters[PARAM_MANUAL_FLOOR_TEMPERATURE] = temperature

        await self.coordinator.set_device_parameters(self._serial_number, parameters)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            parameters = {PARAM_POWER_OFF: True}
        elif hvac_mode == HVACMode.HEAT:
            parameters = {PARAM_POWER_OFF: False}
        else:
            return

        await self.coordinator.set_device_parameters(self._serial_number, parameters)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        parameters = {}

        if preset_mode == "schedule":
            parameters[PARAM_MODE] = MODE_SCHEDULE
        elif preset_mode == "manual":
            parameters[PARAM_MODE] = MODE_MANUAL
        elif preset_mode == "away":
            # Away mode is handled differently - would need to set away times
            # For now, just switch to manual mode
            parameters[PARAM_MODE] = MODE_MANUAL
        elif preset_mode == "temporary":
            # Temporary mode would need special handling
            # For now, just switch to manual mode
            parameters[PARAM_MODE] = MODE_MANUAL

        if parameters:
            await self.coordinator.set_device_parameters(
                self._serial_number, parameters
            )

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        attributes = {}

        # Add floor temperature if in air control mode
        control_type = self._get_control_type()
        if control_type == CONTROL_TYPE_AIR:
            floor_temp = self._device.get_temperature(TEMP_FLOOR)
            if floor_temp is not None:
                attributes["floor_temperature"] = round(floor_temp, 1)

        # Add air temperature if in floor control mode
        if control_type == CONTROL_TYPE_FLOOR:
            air_temp = self._device.get_temperature(TEMP_AIR)
            if air_temp is not None:
                attributes["air_temperature"] = round(air_temp, 1)

        # Add control type
        control_types = {
            CONTROL_TYPE_FLOOR: "floor",
            CONTROL_TYPE_AIR: "air",
            CONTROL_TYPE_EXTENDED: "extended",
        }
        attributes["control_type"] = control_types.get(control_type, "unknown")

        return attributes
