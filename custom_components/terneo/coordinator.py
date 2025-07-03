"""Data update coordinator for Terneo integration."""

import asyncio
import json
import logging
import socket
from datetime import timedelta
from typing import Any, Dict, List, Optional, Set

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    SCAN_INTERVAL,
    UDP_PORT,
)
from .device import TerneoDevice

_LOGGER = logging.getLogger(__name__)


class TerneoCoordinator(DataUpdateCoordinator):
    """Coordinator for Terneo devices."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.devices: Dict[str, TerneoDevice] = {}

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        for device in self.devices.values():
            await device.close()

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data for all devices."""
        if not self.devices:
            return {}

        data = {}
        tasks = []

        for serial_number, device in self.devices.items():
            tasks.append(self._update_device_data(serial_number, device))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            serial_number = list(self.devices.keys())[i]
            if isinstance(result, Exception):
                _LOGGER.error("Failed to update device %s: %s", serial_number, result)
            else:
                data[serial_number] = result

        return data

    async def _update_device_data(
        self, serial_number: str, device: TerneoDevice
    ) -> Dict[str, Any]:
        """Update data for a single device."""
        try:
            # Get telemetry (most important for real-time data)
            telemetry = await device.get_telemetry()

            # Get parameters less frequently (they don't change often)
            parameters = device._parameters
            if not parameters:
                parameters = await device.get_parameters()

            return {
                "telemetry": telemetry,
                "parameters": parameters,
                "available": True,
            }

        except Exception as err:
            _LOGGER.warning("Failed to update device %s: %s", serial_number, err)
            return {
                "telemetry": {},
                "parameters": {},
                "available": False,
            }

    async def add_device(self, host: str, serial_number: str) -> TerneoDevice:
        """Add a device manually."""
        if serial_number in self.devices:
            return self.devices[serial_number]

        device = TerneoDevice(host, serial_number)

        # Test connection
        try:
            await device.get_parameters()
            await device.get_telemetry()
        except Exception as err:
            await device.close()
            raise UpdateFailed(f"Failed to connect to device: {err}") from err

        self.devices[serial_number] = device

        # Trigger immediate update
        await self.async_request_refresh()

        return device

    async def remove_device(self, serial_number: str) -> None:
        """Remove a device."""
        if serial_number in self.devices:
            device = self.devices.pop(serial_number)
            await device.close()

    def get_device(self, serial_number: str) -> Optional[TerneoDevice]:
        """Get a device by serial number."""
        return self.devices.get(serial_number)

    async def set_device_parameters(
        self, serial_number: str, parameters: Dict[int, Any]
    ) -> bool:
        """Set parameters for a device."""
        device = self.get_device(serial_number)
        if not device:
            return False

        try:
            result = await device.set_parameters(parameters)
            if result:
                # Trigger immediate update to get new state
                await self.async_request_refresh()
            return result
        except Exception as err:
            _LOGGER.error(
                "Failed to set parameters for device %s: %s", serial_number, err
            )
            return False

    async def set_device_schedule(
        self, serial_number: str, day: str, periods: List[List[int]]
    ) -> bool:
        """Set schedule for a device."""
        device = self.get_device(serial_number)
        if not device:
            return False

        try:
            result = await device.set_schedule(day, periods)
            if result:
                # Trigger immediate update to get new state
                await self.async_request_refresh()
            return result
        except Exception as err:
            _LOGGER.error(
                "Failed to set schedule for device %s: %s", serial_number, err
            )
            return False
