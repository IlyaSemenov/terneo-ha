"""Terneo device communication."""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from .const import (
    API_ENDPOINT,
    API_TIMEOUT,
    CMD_GET_PARAMETERS,
    CMD_GET_SCHEDULE,
    CMD_GET_TELEMETRY,
    PARAM_TYPE_BOOL,
    PARAM_TYPE_INT8,
    PARAM_TYPE_INT16,
    PARAM_TYPE_INT32,
    PARAM_TYPE_STRING,
    PARAM_TYPE_UINT8,
    PARAM_TYPE_UINT16,
    PARAM_TYPE_UINT32,
)

_LOGGER = logging.getLogger(__name__)


class TerneoDevice:
    """Represents a Terneo device."""

    def __init__(self, host: str, serial_number: str) -> None:
        """Initialize the device."""
        self.host = host
        self.serial_number = serial_number
        self._session: Optional[aiohttp.ClientSession] = None
        self._parameters: Dict[int, Any] = {}
        self._telemetry: Dict[str, Any] = {}
        self._schedule: Dict[str, List[List[int]]] = {}

    @property
    def url(self) -> str:
        """Return the device API URL."""
        return f"http://{self.host}{API_ENDPOINT}"

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
            )
        return self._session

    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _send_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the device."""
        session = await self._ensure_session()

        try:
            async with session.post(self.url, json=data) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP {response.status}")

                result = await response.json()
                _LOGGER.debug("Device %s response: %s", self.serial_number, result)
                return result

        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout communicating with device %s", self.serial_number)
            raise aiohttp.ClientError("Timeout") from err
        except Exception as err:
            _LOGGER.error("Error communicating with device %s: %s", self.serial_number, err)
            raise

    async def get_parameters(self) -> Dict[int, Any]:
        """Get device parameters."""
        data = {"cmd": CMD_GET_PARAMETERS}
        response = await self._send_request(data)

        if "par" in response:
            self._parameters = {}
            for param in response["par"]:
                if len(param) >= 3:
                    param_id, param_type, param_value = param[0], param[1], param[2]
                    self._parameters[param_id] = self._parse_parameter_value(
                        param_value, param_type
                    )

        return self._parameters

    async def get_telemetry(self) -> Dict[str, Any]:
        """Get device telemetry."""
        data = {"cmd": CMD_GET_TELEMETRY}
        response = await self._send_request(data)

        # Remove serial number from telemetry data
        self._telemetry = {k: v for k, v in response.items() if k != "sn"}
        return self._telemetry

    async def get_schedule(self) -> Dict[str, List[List[int]]]:
        """Get device schedule."""
        data = {"cmd": CMD_GET_SCHEDULE}
        response = await self._send_request(data)

        if "tt" in response:
            self._schedule = response["tt"]

        return self._schedule

    async def set_parameters(self, parameters: Dict[int, Any]) -> bool:
        """Set device parameters."""
        if not parameters:
            return True

        # Convert parameters to the required format
        par_data = []
        for param_id, value in parameters.items():
            # Determine parameter type based on common parameter IDs
            param_type = self._get_parameter_type(param_id)
            par_data.append([param_id, param_type, str(value)])

        data = {
            "sn": self.serial_number,
            "par": par_data
        }

        response = await self._send_request(data)
        return response.get("success") == "true"

    async def set_schedule(self, day: str, periods: List[List[int]]) -> bool:
        """Set schedule for a specific day."""
        data = {
            "sn": self.serial_number,
            "tt": {day: periods}
        }

        response = await self._send_request(data)
        return response.get("success") == "true"

    def _parse_parameter_value(self, value: str, param_type: int) -> Any:
        """Parse parameter value based on type."""
        try:
            if param_type == PARAM_TYPE_STRING:
                return value
            elif param_type == PARAM_TYPE_BOOL:
                return value == "1"
            elif param_type in (PARAM_TYPE_INT8, PARAM_TYPE_INT16, PARAM_TYPE_INT32):
                return int(value)
            elif param_type in (PARAM_TYPE_UINT8, PARAM_TYPE_UINT16, PARAM_TYPE_UINT32):
                return int(value)
            else:
                return value
        except (ValueError, TypeError):
            _LOGGER.warning("Failed to parse parameter value: %s (type: %s)", value, param_type)
            return value

    def _get_parameter_type(self, param_id: int) -> int:
        """Get parameter type for a given parameter ID."""
        # Map common parameter IDs to their types
        type_mapping = {
            0: PARAM_TYPE_UINT32,   # startAwayTime
            1: PARAM_TYPE_UINT32,   # endAwayTime
            2: PARAM_TYPE_UINT8,    # mode
            3: PARAM_TYPE_UINT8,    # controlType
            4: PARAM_TYPE_INT8,     # manualAir
            5: PARAM_TYPE_INT8,     # manualFloorTemperature
            6: PARAM_TYPE_INT8,     # awayAirTemperature
            7: PARAM_TYPE_INT8,     # awayFloorTemperature
            14: PARAM_TYPE_UINT8,   # minTempAdvancedMode
            15: PARAM_TYPE_UINT8,   # maxTempAdvancedMode
            17: PARAM_TYPE_UINT16,  # power
            18: PARAM_TYPE_UINT8,   # sensorType
            19: PARAM_TYPE_UINT8,   # hysteresis
            20: PARAM_TYPE_INT8,    # airCorrection
            21: PARAM_TYPE_INT8,    # floorCorrection
            23: PARAM_TYPE_UINT8,   # brightness
            25: PARAM_TYPE_UINT8,   # propKoef
            26: PARAM_TYPE_INT8,    # upperLimit
            27: PARAM_TYPE_INT8,    # lowerLimit
            28: PARAM_TYPE_UINT8,   # maxSchedulePeriod
            29: PARAM_TYPE_UINT8,   # tempTemperature
            31: PARAM_TYPE_UINT8,   # setTemperature
            33: PARAM_TYPE_INT8,    # upperAirLimit
            34: PARAM_TYPE_INT8,    # lowerAirLimit
            52: PARAM_TYPE_UINT16,  # nightBrightStart
            53: PARAM_TYPE_UINT16,  # nightBrightEnd
            109: PARAM_TYPE_BOOL,   # offButtonLock
            114: PARAM_TYPE_BOOL,   # androidBlock
            115: PARAM_TYPE_BOOL,   # cloudBlock
            117: PARAM_TYPE_BOOL,   # NCContactControl
            118: PARAM_TYPE_BOOL,   # coolingControlWay
            120: PARAM_TYPE_BOOL,   # useNightBright
            121: PARAM_TYPE_BOOL,   # preControl
            122: PARAM_TYPE_BOOL,   # windowOpenControl
            124: PARAM_TYPE_BOOL,   # childrenLock
            125: PARAM_TYPE_BOOL,   # powerOff
        }

        return type_mapping.get(param_id, PARAM_TYPE_STRING)

    def get_parameter(self, param_id: int) -> Any:
        """Get a specific parameter value."""
        return self._parameters.get(param_id)

    def get_telemetry_value(self, group: str, index: int) -> Any:
        """Get a specific telemetry value."""
        key = f"{group}.{index}"
        value = self._telemetry.get(key)

        # Parse numeric values
        if value is not None and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return value

        return value

    def get_temperature(self, temp_index: int) -> Optional[float]:
        """Get temperature value in Celsius."""
        value = self.get_telemetry_value("t", temp_index)
        if value is not None:
            # Temperature is in 1/16 degrees Celsius
            return float(value) / 16.0
        return None

    def get_flag(self, flag_index: int) -> Optional[bool]:
        """Get flag value."""
        value = self.get_telemetry_value("f", flag_index)
        if value is not None:
            return bool(int(value))
        return None

    def get_mode(self, mode_index: int) -> Optional[int]:
        """Get mode value."""
        return self.get_telemetry_value("m", mode_index)

    @property
    def available(self) -> bool:
        """Return if device is available."""
        return bool(self._telemetry or self._parameters)
