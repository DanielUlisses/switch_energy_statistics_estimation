# Example Configurations for Switch Energy Statistics

## Basic Single Gang Switch
For a simple single gang switch controlling LED lights:

```yaml
Name: Living Room Lights
Switch Entity: switch.living_room_main
Gang Count: 1
Gang 1 Power: 12.0W
```

## Dual Gang Kitchen Switch
For a 2-gang switch in kitchen:

```yaml
Name: Kitchen Lights
Switch Entity: switch.kitchen_2gang
Gang Count: 2
Gang 1 Power: 15.0W  # Main ceiling lights
Gang 2 Power: 8.0W   # Under cabinet LED strips
```

## 4-Gang Bathroom Switch
For a 4-gang bathroom switch:

```yaml
Name: Master Bathroom
Switch Entity: switch.bathroom_4gang
Gang Count: 4
Gang 1 Power: 10.0W   # Vanity lights
Gang 2 Power: 8.0W    # Mirror lights
Gang 3 Power: 120.0W  # Exhaust fan
Gang 4 Power: 25.0W   # Heat lamp
```

## 6-Gang Office Setup
For a 6-gang office switch:

```yaml
Name: Home Office
Switch Entity: switch.office_6gang
Gang Count: 6
Gang 1 Power: 18.0W   # Desk lamp
Gang 2 Power: 22.0W   # Ceiling fan light
Gang 3 Power: 95.0W   # Ceiling fan motor
Gang 4 Power: 12.0W   # Accent lighting
Gang 5 Power: 5.0W    # Night light
Gang 6 Power: 45.0W   # Air purifier
```

## 8-Gang Commercial/Large Room
For an 8-gang switch in a large room or commercial space:

```yaml
Name: Conference Room
Switch Entity: switch.conference_8gang
Gang Count: 8
Gang 1 Power: 24.0W   # Main lights zone 1
Gang 2 Power: 24.0W   # Main lights zone 2
Gang 3 Power: 24.0W   # Main lights zone 3
Gang 4 Power: 24.0W   # Main lights zone 4
Gang 5 Power: 15.0W   # Accent lighting
Gang 6 Power: 180.0W  # Projector
Gang 7 Power: 85.0W   # Air circulation fan
Gang 8 Power: 12.0W   # Emergency lighting
```

## Typical Power Consumption Values

### LED Lighting
- Single LED bulb: 8-15W
- LED strip (1m): 5-12W
- LED panel light: 18-24W
- LED downlights: 7-12W each

### Traditional Lighting
- Incandescent bulb: 25-100W
- Halogen bulb: 20-50W
- CFL bulb: 13-23W
- Fluorescent tube: 15-40W

### Appliances & Devices
- Ceiling fan (light only): 15-25W
- Ceiling fan (motor): 60-120W
- Exhaust fan: 80-150W
- Night light: 1-5W
- Under cabinet lighting: 8-15W
- Accent lighting: 10-20W
- Heat lamp: 250W
- Air purifier: 30-60W
- Small appliances: 50-200W

## Energy Dashboard Configuration

After setting up your switch energy statistics, add them to the Home Assistant Energy Dashboard:

1. Go to **Configuration** → **Energy**
2. Under "Individual Devices", click **Add Device**
3. Select your energy sensors:
   - For daily tracking: `sensor.{name}_gang_{n}_energy_daily`
   - For longer term: `sensor.{name}_gang_{n}_energy_monthly`

## Automation Examples

### Track Total Daily Usage
```yaml
template:
  - sensor:
      - name: "Kitchen Total Daily Energy"
        unit_of_measurement: "Wh"
        device_class: energy
        state: >
          {{ (states('sensor.kitchen_gang_1_energy_daily') | float) +
             (states('sensor.kitchen_gang_2_energy_daily') | float) +
             (states('sensor.kitchen_gang_3_energy_daily') | float) +
             (states('sensor.kitchen_gang_4_energy_daily') | float) }}
```

### Cost Calculation
```yaml
template:
  - sensor:
      - name: "Living Room Daily Energy Cost"
        unit_of_measurement: "$"
        state: >
          {{ (states('sensor.living_room_gang_1_energy_daily') | float * 0.12 / 1000) | round(2) }}
        # Assumes $0.12 per kWh
```

### Weekly Energy Reset Notification
```yaml
automation:
  - alias: "Weekly Energy Reset"
    trigger:
      platform: time
      at: "00:00:00"
    condition:
      condition: time
      weekday:
        - mon
    action:
      service: notify.mobile_app
      data:
        title: "Weekly Energy Reset"
        message: >
          Last week's total:
          Living Room: {{ states('sensor.living_room_gang_1_energy_weekly') }}Wh
          Kitchen: {{ states('sensor.kitchen_gang_1_energy_weekly') }}Wh
```

## Tips for Accurate Power Values

1. **Measure if possible**: Use a power meter to measure actual consumption
2. **Check device labels**: Many devices list power consumption on labels
3. **Use manufacturer specs**: Check product documentation
4. **Start conservative**: Begin with lower estimates and adjust based on usage patterns
5. **Consider efficiency**: LED drivers, transformers may add 10-20% overhead
6. **Update seasonally**: Some devices (fans, heaters) may vary by season
