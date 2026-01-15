# Switch Energy Statistics Estimation

A custom Home Assistant integration that provides energy consumption tracking and statistics for multi-gang switches (1-gang to 8-gang).

## Features

- **Multi-gang Support**: Track energy consumption for switches with 1 to 8 gangs
- **Flexible Power Configuration**: Set different power consumption values for each gang
- **Historical Data**: Track energy consumption over daily, weekly, and monthly periods
- **Home Assistant Energy Dashboard**: Compatible with HA Energy Dashboard
- **Real-time Monitoring**: Tracks switch state changes to calculate accurate energy consumption
- **Data Persistence**: Historical data is stored and survives Home Assistant restarts
- **Service Management**: Built-in services for data management and export

## Installation

### HACS Installation (Recommended)

1. **Install HACS** if you haven't already: [HACS Installation Guide](https://hacs.xyz/docs/setup/download)

2. **Add Custom Repository**:
   - Go to HACS → Integrations
   - Click the three dots menu (⋮) → Custom repositories
   - Add repository URL: `https://github.com/danielulisses/zigbee-devices`
   - Category: Integration
   - Click Add

3. **Install the Integration**:
   - Search for "Switch Energy Statistics Estimation" in HACS
   - Click Install
   - Restart Home Assistant

4. **Add the Integration**:
   - Go to Settings → Devices & Services → Integrations
   - Click "Add Integration"
   - Search for "Switch Energy Statistics Estimation"
   - Follow the configuration wizard

### Manual Installation

1. Copy the `switch_energy_statistics_estimation` folder to your Home Assistant `custom_components` directory:
   ```
   custom_components/
   └── switch_energy_statistics_estimation/
       ├── __init__.py
       ├── manifest.json
       ├── config_flow.py
       ├── const.py
       ├── sensor.py
       ├── services.py
       ├── services.yaml
       ├── hacs.json
       └── translations/
           └── en.json
   ```

2. Restart Home Assistant

3. Go to Settings → Devices & Services → Integrations → Add Integration

4. Search for "Switch Energy Statistics Estimation" and add it

## Configuration

### Setup Process

1. **Choose Switch Entity**: Select the switch entity you want to monitor
2. **Set Gang Count**: Specify how many gangs your switch has (1-8)
3. **Configure Power Consumption**: Set the power consumption in watts for each gang

### Configuration Options

- **Switch Entity**: The Home Assistant entity ID of your switch
- **Gang Count**: Number of gangs (1-8)
- **Gang Power Settings**: Power consumption in watts for each gang

## Entities Created

For each gang, the integration creates the following entities:

### Energy Sensors
- `sensor.{name}_gang_{n}_energy_daily` - Daily energy consumption
- `sensor.{name}_gang_{n}_energy_weekly` - Weekly energy consumption
- `sensor.{name}_gang_{n}_energy_monthly` - Monthly energy consumption

### Power Sensor
- `sensor.{name}_gang_{n}_power` - Current power consumption (0W when off, configured watts when on)

### Entity Attributes

Each energy sensor includes these attributes:
- `switch_entity`: The monitored switch entity
- `gang_number`: Gang number (1-8)
- `gang_power`: Configured power consumption in watts
- `period`: Time period (daily/weekly/monthly)
- `is_on`: Current switch state
- `last_changed`: Last state change timestamp
- `historical_data`: Recent historical consumption data

## How It Works

1. **State Monitoring**: The integration monitors your switch entity for state changes (on/off)
2. **Energy Calculation**: When the switch is on, it calculates energy consumption based on:
   - Time the switch was on
   - Configured power consumption for that gang
3. **Period Tracking**: Energy is accumulated and reset based on the tracking period:
   - **Daily**: Resets at midnight
   - **Weekly**: Resets on Monday
   - **Monthly**: Resets on the 1st of each month
4. **Data Storage**: Historical data is stored persistently and survives restarts

## Services

The integration provides several services for data management:

### switch_energy_statistics.reset_energy
Reset accumulated energy data for a sensor.

```yaml
service: switch_energy_statistics.reset_energy
data:
  entity_id: sensor.switch_gang_1_energy_daily
  period: daily  # optional: daily, weekly, monthly
```

### switch_energy_statistics.set_energy
Set energy value for a specific date.

```yaml
service: switch_energy_statistics.set_energy
data:
  entity_id: sensor.switch_gang_1_energy_daily
  energy: 150.5  # Wh
  date: 2024-01-15  # optional, defaults to today
```

### switch_energy_statistics.export_data
Export historical energy data via event.

```yaml
service: switch_energy_statistics.export_data
data:
  entity_id: sensor.switch_gang_1_energy_daily
  start_date: 2024-01-01  # optional
  end_date: 2024-01-31    # optional
```

## Home Assistant Energy Dashboard Integration

The energy sensors are fully compatible with Home Assistant's Energy Dashboard:

1. Go to Configuration > Energy
2. Add your energy sensors under "Individual Devices"
3. The sensors will appear in your energy usage statistics

## Example Configurations

### Single Gang Switch (10W LED Light)
```yaml
# Configuration
Switch Entity: switch.living_room_light
Gang Count: 1
Gang 1 Power: 10.0W
```

### 4-Gang Switch (Mixed Loads)
```yaml
# Configuration
Switch Entity: switch.kitchen_4gang
Gang Count: 4
Gang 1 Power: 15.0W  # LED strips
Gang 2 Power: 8.0W   # Under cabinet lights
Gang 3 Power: 100.0W # Exhaust fan
Gang 4 Power: 5.0W   # Night light
```

### 8-Gang Switch (Commercial Application)
```yaml
# Configuration
Switch Entity: switch.office_8gang
Gang Count: 8
Gang 1-4 Power: 12.0W each  # LED panels
Gang 5-6 Power: 25.0W each  # Fluorescent lights
Gang 7 Power: 150.0W        # Air circulation fan
Gang 8 Power: 75.0W         # Emergency lighting
```

## Automation Examples

### Daily Energy Report
```yaml
automation:
  - alias: "Daily Energy Report"
    trigger:
      platform: time
      at: "23:59:00"
    action:
      service: notify.mobile_app
      data:
        title: "Daily Energy Usage"
        message: >
          Kitchen Lights: {{ states('sensor.kitchen_gang_1_energy_daily') }}Wh
          Living Room: {{ states('sensor.living_room_gang_1_energy_daily') }}Wh
```

### High Energy Usage Alert
```yaml
automation:
  - alias: "High Energy Usage Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.kitchen_gang_1_energy_daily
      above: 500  # 500Wh
    action:
      service: notify.mobile_app
      data:
        title: "High Energy Usage"
        message: "Kitchen lights have used {{ trigger.to_state.state }}Wh today"
```

## Troubleshooting

### Common Issues

1. **Sensor not updating**:
   - Check that the switch entity exists and is updating
   - Verify the switch entity is in the correct format (switch.xxx or light.xxx)

2. **Energy values seem incorrect**:
   - Verify the power consumption settings for each gang
   - Check if the switch state changes are being detected
   - Use the reset service to clear incorrect data

3. **Historical data missing**:
   - Data is stored in Home Assistant's storage
   - Check Home Assistant logs for storage errors
   - Historical data accumulates over time

### Debug Logging

Enable debug logging by adding this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.switch_energy_statistics: debug
```

## Supported Switch Types

- **Physical Switches**: Any switch entity that reports on/off states
- **Smart Switches**: Zigbee, Z-Wave, WiFi switches
- **Light Entities**: Can also monitor light entities as switches
- **Multi-gang Devices**: Sonoff 4CH, Shelly devices, etc.

## Limitations

- Maximum 8 gangs per switch
- Energy calculation is based on estimated power consumption, not measured
- Requires the switch entity to properly report state changes
- Historical data storage uses Home Assistant's storage system

## Contributing

This is a custom component. If you find bugs or want to suggest improvements, please create an issue or pull request in the repository.

## License

This project is licensed under the MIT License.
