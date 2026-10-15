# Example Configurations for Switch Energy Statistics

Each entry lists its entities (one per gang, in order). For each gang you set the **watts per load** and the **number of loads**.

## Basic Single Gang Switch
A switch controlling one LED ceiling light:

```yaml
Name: Living Room Lights
Entities: switch.living_room_main
Gang 1: 12.0 W × 1
```

## One Switch, Several Identical Lamps
A switch driving 3 spots of 5 W each (estimated at 15 W when on):

```yaml
Name: Sala Spots
Entities: light.sala_spots
Gang 1: 5.0 W × 3
```

The same entry from a script or automation:

```yaml
action: switch_energy_statistics.attach
data:
  entity_id: light.sala_spots
  power: 5
  quantity: 3
```

## Dimmable Light
A 9 W bulb on a dimmer, with power following the brightness (50 % brightness → about 4.5 W):

```yaml
Name: Quarto Teto
Entities: light.quarto_teto
Gang 1: 9.0 W × 1
Scale light power by brightness: on
```

## Dual Gang Kitchen Switch
For a 2-gang switch in a kitchen:

```yaml
Name: Kitchen Lights
Entities: switch.kitchen_l1, switch.kitchen_l2
Gang 1: 15.0 W × 1   # Main ceiling light
Gang 2: 4.0 W × 2    # Two under-cabinet LED strips
```

## 4-Gang Bathroom Switch

```yaml
Name: Master Bathroom
Entities: switch.bath_l1, switch.bath_l2, fan.bath_exhaust, switch.bath_l4
Gang 1: 10.0 W × 1    # Vanity light
Gang 2: 8.0 W × 1     # Mirror light
Gang 3: 120.0 W × 1   # Exhaust fan
Gang 4: 250.0 W × 1   # Heat lamp
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

1. Go to **Settings** → **Dashboards** → **Energy**
2. Under "Individual devices", click **Add device**
3. Select the **lifetime** sensor of each load: `sensor.<name>_<load>_energy`. For a multi-gang entry, either `sensor.<name>_total_energy` or the per-gang lifetime sensors, not both.

Don't add the daily, weekly or monthly sensors to the dashboard: the dashboard already splits energy by day, and adding them counts the same energy again.

## Automation and Template Examples

### Today's consumption ("Consumo de hoje")
The daily sensor already holds today's value and resets at local midnight:

```yaml
type: entity
entity: sensor.garagem_energy_statistics_total_energy_daily
name: Consumo de hoje
```

Yesterday's value is the `yesterday` attribute:

```yaml
template:
  - sensor:
      - name: "Garagem Consumo de Ontem"
        unit_of_measurement: "Wh"
        device_class: energy
        state: "{{ state_attr('sensor.garagem_energy_statistics_total_energy_daily', 'yesterday') | float(0) }}"
```

### Daily Energy Report

```yaml
automation:
  - alias: "Daily Energy Report"
    triggers:
      - trigger: time
        at: "23:59:00"
    actions:
      - action: notify.mobile_app
        data:
          title: "Daily Energy Usage"
          message: >
            Kitchen: {{ states('sensor.kitchen_lights_total_energy_daily') }} Wh
            Living Room: {{ states('sensor.living_room_lights_living_room_main_energy_daily') }} Wh
```

### Cost Calculation

```yaml
template:
  - sensor:
      - name: "Living Room Daily Energy Cost"
        unit_of_measurement: "R$"
        # Assumes R$ 0.90 per kWh
        state: >
          {{ (states('sensor.living_room_lights_living_room_main_energy_daily') | float(0) * 0.90 / 1000) | round(2) }}
```

### Export last month's daily history

```yaml
action: switch_energy_statistics.export_data
data:
  entity_id: sensor.kitchen_lights_total_energy_daily
  start_date: "2026-09-01"
  end_date: "2026-09-30"
response_variable: export
```

## Tips for Accurate Power Values

1. **Measure if possible**: Use a power meter to measure actual consumption
2. **Check device labels**: Many devices list power consumption on labels
3. **Use manufacturer specs**: Check product documentation
4. **Start conservative**: Begin with lower estimates and adjust based on usage patterns
5. **Consider efficiency**: LED drivers, transformers may add 10-20% overhead
6. **Update seasonally**: Some devices (fans, heaters) may vary by season
