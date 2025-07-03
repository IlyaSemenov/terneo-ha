"""Discovery component for Terneo integration."""

import asyncio
import json
import logging
import socket
from typing import Any, Dict, Set

from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

from .const import DOMAIN, UDP_PORT

_LOGGER = logging.getLogger(__name__)


class TerneoDiscovery:
    """Handle Terneo device discovery."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize discovery."""
        self.hass = hass
        self._discovery_task = None
        self._discovery_socket = None
        self._discovered_devices: Set[str] = set()

    async def start_discovery(self) -> None:
        """Start UDP discovery."""
        if self._discovery_task is not None:
            return

        try:
            # Create UDP socket for discovery
            self._discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._discovery_socket.bind(("", UDP_PORT))
            self._discovery_socket.setblocking(False)

            # Start discovery task
            self._discovery_task = asyncio.create_task(self._discovery_loop())
            _LOGGER.info("Started Terneo device discovery on port %s", UDP_PORT)

        except Exception as err:
            _LOGGER.error("Failed to start discovery: %s", err)
            if self._discovery_socket:
                self._discovery_socket.close()
                self._discovery_socket = None

    async def stop_discovery(self) -> None:
        """Stop UDP discovery."""
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
            self._discovery_task = None

        if self._discovery_socket:
            self._discovery_socket.close()
            self._discovery_socket = None

        _LOGGER.info("Stopped Terneo device discovery")

    async def _discovery_loop(self) -> None:
        """Discovery loop for UDP broadcasts."""
        while True:
            try:
                # Check for UDP packets
                loop = asyncio.get_event_loop()
                data, addr = await loop.sock_recvfrom(self._discovery_socket, 1024)

                try:
                    broadcast_data = json.loads(data.decode("utf-8"))
                    await self._handle_discovery_packet(broadcast_data, addr[0])
                except (json.JSONDecodeError, UnicodeDecodeError) as err:
                    _LOGGER.debug("Invalid discovery packet from %s: %s", addr[0], err)

            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.error("Error in discovery loop: %s", err)
                await asyncio.sleep(1)

    async def _handle_discovery_packet(self, data: Dict[str, Any], host: str) -> None:
        """Handle a discovery packet."""
        serial_number = data.get("sn")
        if not serial_number:
            return

        # Check if this is a new device
        if serial_number not in self._discovered_devices:
            _LOGGER.info("Discovered new Terneo device: %s at %s", serial_number, host)
            self._discovered_devices.add(serial_number)

            # Trigger config flow for new device
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": "discovery"},
                    data={
                        "host": host,
                        "serial_number": serial_number,
                        "hw": data.get("hw", "unknown"),
                        "connection": data.get("connection", "unknown"),
                    },
                )
            )


# Global discovery instance
_discovery_instance = None


async def async_setup_discovery(hass: HomeAssistant) -> None:
    """Set up discovery if not already running."""
    global _discovery_instance

    if _discovery_instance is None:
        _discovery_instance = TerneoDiscovery(hass)
        await _discovery_instance.start_discovery()


async def async_stop_discovery(hass: HomeAssistant) -> None:
    """Stop discovery."""
    global _discovery_instance

    if _discovery_instance is not None:
        await _discovery_instance.stop_discovery()
        _discovery_instance = None
