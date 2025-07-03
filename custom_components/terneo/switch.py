"""Switch platform for Terneo integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    PARAM_CHILDREN_LOCK,
    PARAM_NC_CONTACT_CONTROL,
    PARAM_PRE_CONTROL,
    PARAM_POWER_OFF,
    PARAM_USE_NIGHT_BRIGHT,
    PARAM_WINDOW_OPEN_CONTROL,
)
from .coordinator import TerneoCoordinator
from .device import TerneoDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Terneo switch entities."""
    coordinator: TerneoCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for serial_number, device in coordinator.devices.items():
        entities.extend([
            TerneoSwitch(
                coordinator, device, serial_number, "power",
                PARAM_POWER_OFF, "Power", "mdi:power", True
            ),
            TerneoSwitch(
                coordinator, device, serial_number, "child_lock",
                PARAM_CHILDREN_LOCK, "Child Lock", "mdi:lock"
            ),
            TerneoSwitch(
                coordinator, device, serial_number, "night_brightness",
                PARAM_USE_NIGHT_BRIGHT, "Night Brightness", "mdi:brightness-6"
            ),
            TerneoSwitch(
                coordinator, device, serial_number, "pre_heating",
                PARAM_PRE_CONTROL, "Pre-heating", "mdi:radiator"
            ),
            TerneoSwitch(
                coordinator, device, serial_number, "window_open_detection",
                PARAM_WINDOW_OPEN_CONTROL, "Window Open Detection", "mdi:window-open"
            ),
            TerneoSwitch(
                coordinator, device, serial_number, "inverted_relay",
                PARAM_NC_CONTACT_CONTROL, "Inverted Relay", "mdi:electric-switch"
            ),
        ])

    async_add_entities(entities)


class TerneoSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Terneo switch."""

    def __init__(
        self,
        coordinator: TerneoCoordinator,
        device: TerneoDevice,
        serial_number: str,
        switch_type: str,
        param_id: int,
        name: str,
        icon: str,
        inverted: bool = False,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device = device
        self._serial_number = serial_number
        self._switch_type = switch_type
        self._param_id = param_id
        self._inverted = inverted
        self._attr_unique_id = f"{serial_number}_{switch_type}"
        self._attr_name = name
        self._attr_icon = icon

        # Disable some switches by default
        if switch_type in ["inverted_relay", "pre_heating", "window_open_detection"]:
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
    def is_on(self) -> Optional[bool]:
        """Return true if switch is on."""
        value = self._device.get_parameter(self._param_id)
        if value is None:
            return None

        # Handle inverted logic for power switch
        if self._inverted:
            return not bool(value)
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        # Handle inverted logic for power switch
        value = False if self._inverted else True
        parameters = {self._param_id: value}
        await self.coordinator.set_device_parameters(self._serial_number, parameters)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        # Handle inverted logic for power switch
        value = True if self._inverted else False
        parameters = {self._param_id: value}
        await self.coordinator.set_device_parameters(self._serial_number, parameters)
