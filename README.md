# Terneo Home Assistant Integration

A Home Assistant integration for Terneo smart heated floor thermostats that provides local control without requiring cloud connectivity.

## Features

- **Auto-discovery**: Automatically discovers Terneo devices on your network via UDP broadcasts
- **Local control**: Works entirely locally without cloud dependency
- **Comprehensive monitoring**: Temperature sensors, WiFi signal, power consumption, and status monitoring
- **Full climate control**: Temperature control, HVAC modes, and preset modes
- **Schedule management**: Set and manage weekly heating schedules
- **Advanced configuration**: Control limits, hysteresis, brightness, and other device parameters

## Supported Devices

This integration supports Terneo Wi-Fi thermostats with firmware version 2.3 and higher, including:

- Terneo AX
- Terneo SX
- Other Terneo Wi-Fi models

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/IlyaSemenov/terneo-ha`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Terneo" and install

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/IlyaSemenov/terneo-ha/releases)
2. Extract the `custom_components/terneo` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Automatic Discovery

The integration will automatically discover Terneo devices on your network. When a device is found, you'll see a notification in Home Assistant to add it.

### Manual Configuration

If automatic discovery doesn't work:

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Terneo"
4. Enter your device's IP address
5. Click "Submit"

## Entities

The integration creates the following entities for each device:

### Climate Entity

- **Thermostat control**: Main climate entity with temperature control
- **HVAC modes**: Heat, Off
- **Preset modes**: Schedule, Manual, Away, Temporary
- **Temperature limits**: Respects device-configured min/max temperatures

### Sensors

- **Floor Temperature**: Current floor temperature
- **Air Temperature**: Current air temperature
- **Setpoint Temperature**: Current target temperature
- **MCU Temperature**: Internal microcontroller temperature
- **Overheat Sensor**: Overheat protection sensor temperature
- **WiFi Signal**: Signal strength in dBm
- **Power**: Configured power consumption in watts
- **Status sensors**: Heating state, sensor errors, window detection, etc.

### Switches

- **Power**: Turn device on/off
- **Child Lock**: Enable/disable child lock
- **Night Brightness**: Enable/disable night brightness mode
- **Pre-heating**: Enable/disable pre-heating function
- **Window Open Detection**: Enable/disable window open detection
- **Inverted Relay**: Enable/disable inverted relay mode

### Number Entities

- **Manual Temperatures**: Set manual floor and air temperatures
- **Temperature Limits**: Configure min/max temperature limits
- **Brightness**: Adjust display brightness (0-9)
- **Hysteresis**: Set temperature hysteresis (0.1-5.0°C)

## Services

### `terneo.set_schedule`

Set a weekly schedule for a device.

```yaml
service: terneo.set_schedule
target:
  entity_id: climate.terneo_123456789
data:
  day: "0"  # Monday
  periods:
    - [480, 220]   # 8:00 AM, 22.0°C
    - [1080, 180]  # 6:00 PM, 18.0°C
```

### `terneo.get_schedule`

Get the current schedule for a device.

```yaml
service: terneo.get_schedule
target:
  entity_id: climate.terneo_123456789
```

### `terneo.set_away_mode`

Set away mode with specific times and temperatures.

```yaml
service: terneo.set_away_mode
target:
  entity_id: climate.terneo_123456789
data:
  start_time: "2024-01-15T08:00:00"
  end_time: "2024-01-20T18:00:00"
  floor_temperature: 15
  air_temperature: 16
```

## Device Requirements

- Terneo Wi-Fi thermostat with firmware 2.3+
- Device must be connected to the same network as Home Assistant
- Local API access must be enabled (unlocked for LAN operation)

## Network Configuration

The integration uses:

- **UDP port 23500**: For device discovery (broadcasts)
- **HTTP port 80**: For device communication (API calls)

Ensure these ports are not blocked by firewalls between Home Assistant and your Terneo devices.

## Troubleshooting

### Device Not Discovered

1. Check that the device is on the same network
2. Verify UDP port 23500 is not blocked
3. Try manual configuration with the device IP address
4. Check device firmware version (must be 2.3+)

### Connection Issues

1. Verify the device IP address is correct
2. Check that HTTP port 80 is accessible
3. Ensure local API access is enabled on the device
4. Try accessing `http://device_ip/api.html` in a browser

### Parameter Changes Not Working

1. Verify the device is not locked for local changes
2. Check parameter limits (temperatures must be within configured ranges)
3. Some parameters may require specific device modes

## API Reference

This integration uses the Terneo local API documented at:
<https://terneo-api.readthedocs.io/ru/latest/ru/intro_ru.html>

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/IlyaSemenov/terneo-ha/issues) page.
