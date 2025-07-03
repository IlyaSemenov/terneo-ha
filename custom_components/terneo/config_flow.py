"""Config flow for Terneo integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .device import TerneoDevice

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]

    # Create a temporary device to test connection
    device = TerneoDevice(host, "")

    try:
        # Try to get parameters to validate connection
        parameters = await device.get_parameters()
        if not parameters:
            raise CannotConnect("No parameters received from device")

        # Try to get telemetry to get serial number
        telemetry = await device.get_telemetry()

        # Get serial number from device response
        # We need to make a request that returns the serial number
        test_response = await device._send_request({"cmd": 1})
        serial_number = test_response.get("sn")

        if not serial_number:
            raise CannotConnect("Could not get device serial number")

        return {
            "title": f"Terneo {serial_number}",
            "serial_number": serial_number,
            "host": host,
        }

    except Exception as err:
        _LOGGER.error("Failed to connect to device at %s: %s", host, err)
        raise CannotConnect(f"Cannot connect to device: {err}") from err

    finally:
        await device.close()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Terneo."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: Optional[Dict[str, Any]] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            if user_input.get("manual_ip"):
                # Manual IP entry
                return await self.async_step_manual()
            elif user_input.get("discovered_device"):
                # Selected discovered device
                device_info = user_input["discovered_device"]
                try:
                    info = await validate_input(
                        self.hass, {"host": device_info["host"]}
                    )

                    # Check if device is already configured
                    await self.async_set_unique_id(info["serial_number"])
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=info["title"],
                        data={
                            CONF_HOST: info["host"],
                            "serial_number": info["serial_number"],
                        },
                    )
                except CannotConnect:
                    return self.async_abort(reason="cannot_connect")
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    return self.async_abort(reason="unknown")

        # Start discovery to find devices
        from .discovery import async_setup_discovery

        await async_setup_discovery(self.hass)

        # Wait a bit for discovery
        import asyncio

        await asyncio.sleep(2)

        # Get discovered devices
        discovered_devices = []
        if hasattr(self.hass.data.get(DOMAIN, {}), "_discovered_devices"):
            # This would need to be implemented in discovery
            pass

        # For now, show manual entry option
        return await self.async_step_manual()

    async def async_step_manual(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle manual IP entry."""
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                # Check if device is already configured
                await self.async_set_unique_id(info["serial_number"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: info["host"],
                        "serial_number": info["serial_number"],
                    },
                )
            except CannotConnect:
                errors = {"base": "cannot_connect"}
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors = {"base": "unknown"}
        else:
            errors = {}

        return self.async_show_form(
            step_id="manual",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_discovery(self, discovery_info: Dict[str, Any]) -> FlowResult:
        """Handle discovery."""
        self._discovery_info = discovery_info
        serial_number = discovery_info["serial_number"]
        host = discovery_info["host"]

        # Check if device is already configured
        await self.async_set_unique_id(serial_number)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        # Set title for discovery
        self.context["title_placeholders"] = {
            "name": f"Terneo {serial_number}",
            "host": host,
        }

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None or self._discovery_info is None:
            return self.async_create_entry(
                title=f"Terneo {self._discovery_info['serial_number']}",
                data={
                    CONF_HOST: self._discovery_info["host"],
                    "serial_number": self._discovery_info["serial_number"],
                    "hw": self._discovery_info.get("hw", "unknown"),
                    "connection": self._discovery_info.get("connection", "unknown"),
                },
            )

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={
                "name": f"Terneo {self._discovery_info['serial_number']}",
                "host": self._discovery_info["host"],
            },
        )

    async def async_step_reconfigure(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle reconfiguration."""
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                # Verify this is the same device
                if info["serial_number"] != config_entry.data["serial_number"]:
                    return self.async_abort(reason="different_device")

                return self.async_update_reload_and_abort(
                    config_entry,
                    data={
                        **config_entry.data,
                        CONF_HOST: info["host"],
                    },
                )
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=config_entry.data[CONF_HOST]): str,
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
