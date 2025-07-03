"""The Terneo integration."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PARAM_AWAY_AIR_TEMPERATURE,
    PARAM_AWAY_FLOOR_TEMPERATURE,
    PARAM_END_AWAY_TIME,
    PARAM_START_AWAY_TIME,
)
from .coordinator import TerneoCoordinator
from .discovery import async_setup_discovery, async_stop_discovery

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Terneo from a config entry."""
    host = entry.data[CONF_HOST]
    serial_number = entry.data["serial_number"]

    # Initialize coordinator
    coordinator = TerneoCoordinator(hass)

    # Store coordinator in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    try:
        # Add the specific device to coordinator
        await coordinator.add_device(host, serial_number)

        # Perform initial data fetch
        await coordinator.async_config_entry_first_refresh()

    except Exception as err:
        _LOGGER.error("Failed to set up Terneo device %s: %s", serial_number, err)
        await coordinator.async_shutdown()
        raise ConfigEntryNotReady from err

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_setup_services(hass)

    # Start discovery for finding new devices (only once)
    await async_setup_discovery(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up coordinator
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_shutdown()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # No migration needed yet
        pass

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True


# Service schemas
SET_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required("day"): cv.string,
        vol.Required("periods"): vol.All(
            cv.ensure_list, [vol.All(cv.ensure_list, [cv.positive_int])]
        ),
    }
)

SET_AWAY_MODE_SCHEMA = vol.Schema(
    {
        vol.Required("start_time"): cv.datetime,
        vol.Required("end_time"): cv.datetime,
        vol.Optional("floor_temperature"): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=45)
        ),
        vol.Optional("air_temperature"): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=35)
        ),
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Terneo integration."""

    async def handle_set_schedule(call: ServiceCall) -> None:
        """Handle set schedule service call."""
        entity_ids = call.data.get("entity_id", [])
        day = call.data["day"]
        periods = call.data["periods"]

        for entity_id in entity_ids:
            # Extract serial number from entity_id
            if entity_id.startswith("climate.terneo_"):
                serial_number = entity_id.replace("climate.terneo_", "").replace(
                    "_climate", ""
                )

                # Find coordinator with this device
                for coordinator in hass.data[DOMAIN].values():
                    if (
                        isinstance(coordinator, TerneoCoordinator)
                        and serial_number in coordinator.devices
                    ):
                        await coordinator.set_device_schedule(
                            serial_number, day, periods
                        )
                        break

    async def handle_get_schedule(call: ServiceCall) -> None:
        """Handle get schedule service call."""
        entity_ids = call.data.get("entity_id", [])

        for entity_id in entity_ids:
            # Extract serial number from entity_id
            if entity_id.startswith("climate.terneo_"):
                serial_number = entity_id.replace("climate.terneo_", "").replace(
                    "_climate", ""
                )

                # Find coordinator with this device
                for coordinator in hass.data[DOMAIN].values():
                    if (
                        isinstance(coordinator, TerneoCoordinator)
                        and serial_number in coordinator.devices
                    ):
                        device = coordinator.get_device(serial_number)
                        if device:
                            schedule = await device.get_schedule()
                            _LOGGER.info(
                                "Schedule for device %s: %s", serial_number, schedule
                            )
                        break

    async def handle_set_away_mode(call: ServiceCall) -> None:
        """Handle set away mode service call."""
        entity_ids = call.data.get("entity_id", [])
        start_time = call.data["start_time"]
        end_time = call.data["end_time"]
        floor_temp = call.data.get("floor_temperature")
        air_temp = call.data.get("air_temperature")

        # Convert datetime to seconds since 2000-01-01
        epoch_2000 = datetime(2000, 1, 1)
        start_seconds = int((start_time - epoch_2000).total_seconds())
        end_seconds = int((end_time - epoch_2000).total_seconds())

        for entity_id in entity_ids:
            # Extract serial number from entity_id
            if entity_id.startswith("climate.terneo_"):
                serial_number = entity_id.replace("climate.terneo_", "").replace(
                    "_climate", ""
                )

                # Find coordinator with this device
                for coordinator in hass.data[DOMAIN].values():
                    if (
                        isinstance(coordinator, TerneoCoordinator)
                        and serial_number in coordinator.devices
                    ):
                        parameters = {
                            PARAM_START_AWAY_TIME: start_seconds,
                            PARAM_END_AWAY_TIME: end_seconds,
                        }

                        if floor_temp is not None:
                            parameters[PARAM_AWAY_FLOOR_TEMPERATURE] = floor_temp
                        if air_temp is not None:
                            parameters[PARAM_AWAY_AIR_TEMPERATURE] = air_temp

                        await coordinator.set_device_parameters(
                            serial_number, parameters
                        )
                        break

    # Register services only if not already registered
    if not hass.services.has_service(DOMAIN, "set_schedule"):
        hass.services.async_register(
            DOMAIN,
            "set_schedule",
            handle_set_schedule,
            schema=SET_SCHEDULE_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, "get_schedule"):
        hass.services.async_register(
            DOMAIN,
            "get_schedule",
            handle_get_schedule,
        )

    if not hass.services.has_service(DOMAIN, "set_away_mode"):
        hass.services.async_register(
            DOMAIN,
            "set_away_mode",
            handle_set_away_mode,
            schema=SET_AWAY_MODE_SCHEMA,
        )
