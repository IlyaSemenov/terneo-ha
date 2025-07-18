"""Constants for the Terneo integration."""
from typing import Final

DOMAIN: Final = "terneo"

# Discovery
UDP_PORT: Final = 23500
DISCOVERY_TIMEOUT: Final = 30
SCAN_INTERVAL: Final = 30

# API
API_ENDPOINT: Final = "/api.cgi"
API_TIMEOUT: Final = 10

# Commands
CMD_GET_PARAMETERS: Final = 1
CMD_GET_SCHEDULE: Final = 2
CMD_GET_TELEMETRY: Final = 4

# Parameter types
PARAM_TYPE_STRING: Final = 0
PARAM_TYPE_INT8: Final = 1
PARAM_TYPE_UINT8: Final = 2
PARAM_TYPE_INT16: Final = 3
PARAM_TYPE_UINT16: Final = 4
PARAM_TYPE_INT32: Final = 5
PARAM_TYPE_UINT32: Final = 6
PARAM_TYPE_BOOL: Final = 7

# Parameter IDs
PARAM_START_AWAY_TIME: Final = 0
PARAM_END_AWAY_TIME: Final = 1
PARAM_MODE: Final = 2
PARAM_CONTROL_TYPE: Final = 3
PARAM_MANUAL_AIR: Final = 4
PARAM_MANUAL_FLOOR_TEMPERATURE: Final = 5
PARAM_AWAY_AIR_TEMPERATURE: Final = 6
PARAM_AWAY_FLOOR_TEMPERATURE: Final = 7
PARAM_MIN_TEMP_ADVANCED: Final = 14
PARAM_MAX_TEMP_ADVANCED: Final = 15
PARAM_POWER: Final = 17
PARAM_SENSOR_TYPE: Final = 18
PARAM_HYSTERESIS: Final = 19
PARAM_AIR_CORRECTION: Final = 20
PARAM_FLOOR_CORRECTION: Final = 21
PARAM_BRIGHTNESS: Final = 23
PARAM_PROP_KOEF: Final = 25
PARAM_UPPER_LIMIT: Final = 26
PARAM_LOWER_LIMIT: Final = 27
PARAM_MAX_SCHEDULE_PERIOD: Final = 28
PARAM_TEMP_TEMPERATURE: Final = 29
PARAM_SET_TEMPERATURE: Final = 31
PARAM_UPPER_AIR_LIMIT: Final = 33
PARAM_LOWER_AIR_LIMIT: Final = 34
PARAM_NIGHT_BRIGHT_START: Final = 52
PARAM_NIGHT_BRIGHT_END: Final = 53
PARAM_OFF_BUTTON_LOCK: Final = 109
PARAM_ANDROID_BLOCK: Final = 114
PARAM_CLOUD_BLOCK: Final = 115
PARAM_NC_CONTACT_CONTROL: Final = 117
PARAM_COOLING_CONTROL_WAY: Final = 118
PARAM_USE_NIGHT_BRIGHT: Final = 120
PARAM_PRE_CONTROL: Final = 121
PARAM_WINDOW_OPEN_CONTROL: Final = 122
PARAM_CHILDREN_LOCK: Final = 124
PARAM_POWER_OFF: Final = 125

# Modes
MODE_SCHEDULE: Final = 0
MODE_MANUAL: Final = 1

# Control types
CONTROL_TYPE_FLOOR: Final = 0
CONTROL_TYPE_AIR: Final = 1
CONTROL_TYPE_EXTENDED: Final = 2

# Management types (from telemetry)
MGMT_TYPE_SCHEDULE: Final = 0
MGMT_TYPE_MANUAL: Final = 3
MGMT_TYPE_AWAY: Final = 4
MGMT_TYPE_TEMP: Final = 5

# Connection states
CONNECTION_WIFI_CON: Final = "wiFiCon"
CONNECTION_TCP_CON: Final = "tcpCon"
CONNECTION_HELLO_CON: Final = "helloCon"
CONNECTION_READY_CON: Final = "readyCon"
CONNECTION_SSL_CON: Final = "sslCon"
CONNECTION_CLOUD_CON: Final = "cloudCon"
CONNECTION_AP_MODE: Final = "APMode"
CONNECTION_CHANGE_STATE: Final = "changeState"
CONNECTION_NO_CON: Final = "noCon"

# Telemetry groups
TELEMETRY_TEMPERATURE: Final = "t"
TELEMETRY_MODES: Final = "m"
TELEMETRY_FLAGS: Final = "f"
TELEMETRY_OTHER: Final = "o"
TELEMETRY_PARAMS: Final = "par"
TELEMETRY_EXTRA_TEMP: Final = "te"

# Temperature indices
TEMP_OVERHEAT: Final = 0
TEMP_FLOOR: Final = 1
TEMP_AIR: Final = 2
TEMP_SETPOINT: Final = 5
TEMP_MCU: Final = 7

# Mode indices
MODE_CONTROL_TYPE: Final = 0
MODE_MANAGEMENT_TYPE: Final = 1
MODE_SCHEDULE_PERIOD: Final = 2
MODE_BLOCK_TYPE: Final = 3
MODE_HEATING_MODE: Final = 5

# Flag indices
FLAG_HEATING_STATE: Final = 0
FLAG_FLOOR_LIMIT: Final = 2
FLAG_FLOOR_SENSOR_BREAK: Final = 3
FLAG_FLOOR_SENSOR_SHORT: Final = 4
FLAG_AIR_SENSOR_BREAK: Final = 5
FLAG_AIR_SENSOR_SHORT: Final = 6
FLAG_PRE_HEATING: Final = 7
FLAG_WINDOW_OPEN: Final = 8
FLAG_OVERHEAT: Final = 9
FLAG_CLOCK_ISSUES: Final = 11
FLAG_NO_OVERHEAT_CONTROL: Final = 12
FLAG_PROPORTIONAL_MODE: Final = 13
FLAG_DIGITAL_FLOOR_SENSOR: Final = 14
FLAG_POWER_OFF: Final = 16

# Other indices
OTHER_WIFI_SIGNAL: Final = 0
OTHER_REBOOT_REASON: Final = 1

# Days of week
DAYS_OF_WEEK: Final = ["0", "1", "2", "3", "4", "5", "6"]  # Monday = 0

# Default values
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_TIMEOUT: Final = 10
