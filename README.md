# Switch Energy Statistics Estimation

A custom Home Assistant integration that estimates the energy used by loads behind on/off entities (switches, lights, fans, input_booleans) from the watts of the load each one drives. One entry covers 1 to 8 entities ("gangs"), and each gang can drive several identical loads (for example 3 lamps × 5 W).

Upstream repository: <https://github.com/DanielUlisses/switch_energy_statistics_estimation>. The repository name ends in `_estimation`, but the integration domain and folder are `switch_energy_statistics`.

## Features

- **1 to 8 gangs per entry**, each with its own watts per load and number of loads
- **Brightness scaling** (optional): a light's power follows its brightness
- **Lifetime energy sensor** for the Home Assistant Energy dashboard
- **Daily, weekly (ISO week) and monthly sensors** that reset at local midnight, Monday and the 1st
- **Live values**: energy accrues every 60 seconds while a load is on
- **Persistent history** (about 400 days, 104 weeks, 36 months) that survives restarts
- **One device per entry**, grouping its sensors
- **Services** to attach loads, export history, and correct or reset values

## Installation

### HACS (recommended)

1. In HACS → Integrations → ⋮ → **Custom repositories**, add `https://github.com/DanielUlisses/switch_energy_statistics_estimation` as an **Integration**.
2. Install **Switch Energy Statistics Estimation** and restart Home Assistant.

### Manual

Copy this folder to `custom_components/switch_energy_statistics/` in your Home Assistant config (or run `./install.sh manual <config dir>`), then restart Home Assistant:

```
custom_components/
└── switch_energy_statistics/
    ├── __init__.py
    ├── config_flow.py
    ├── const.py
    ├── manifest.json
    ├── sensor.py
    ├── services.py
    ├── services.yaml
    ├── tracker.py
    └── translations/
        ├── en.json
        └── pt-BR.json
```

## Configuration

### Adding an entry (UI)

Settings → Devices & Services → **Add Integration** → *Switch Energy Statistics Estimation*:

1. **Entities**: pick the switch / light / fan / input_boolean entities, one per gang, in gang order. **Name** is optional and defaults to the first entity's name.
2. **Loads per gang**: for each gang, the **watts per load** (0.1 to 5000 W) and the **number of loads** (1 to 100). Turn on **Scale light power by brightness** for dimmable lights.

An entity can only be attached to one entry.

### Changing an entry

- **Configure** (options): change watts, number of loads and brightness scaling. The entry reloads by itself.
- **Reconfigure**: rename the entry or add, replace or remove gangs. Kept entities keep their gang number and history. New entities get a new gang number, and the sensors of removed gangs are deleted.

### Attaching loads from a script (`attach` service)

```yaml
action: switch_energy_statistics.attach
data:
  entity_id: light.sala_spots
  power: 5          # W per load
  quantity: 3       # 3 spots on this switch
  name: Sala Spots  # optional, defaults to the entity name
  brightness_scaling: false
response_variable: attached  # optional: {"entry_id": ..., "title": ...}
```

Several entities in `entity_id` become the gangs of one entry, all with the same watts and load count. The call fails if an entity is already attached.

## Entities created

For each gang (`<name>` is the entry name, `<load>` the entity's name):

| Entity | Device class / state class | Resets |
| --- | --- | --- |
| `sensor.<name>_<load>_energy` | energy, total_increasing (Wh, shown in kWh) | never (lifetime) |
| `sensor.<name>_<load>_energy_daily` | energy, total_increasing (Wh) | local midnight |
| `sensor.<name>_<load>_energy_weekly` | energy, total_increasing (Wh) | Monday 00:00 (ISO week) |
| `sensor.<name>_<load>_energy_monthly` | energy, total_increasing (Wh) | the 1st, 00:00 |
| `sensor.<name>_<load>_power` | power, measurement (W) | — |

Entries with more than one gang also get `sensor.<name>_total_energy`, `..._total_energy_daily`, `..._total_energy_weekly`, `..._total_energy_monthly` and `..._total_power`.

Example (entry "Garagem Energy Statistics", entity "Garagem Luz"): `sensor.garagem_energy_statistics_garagem_luz_energy_daily`.

### Attributes

- Gang sensors: `switch_entity`, `gang_number`, `gang_power` (watts × loads), `load_power`, `load_count`, `is_on`, `brightness_factor` (when scaling applies)
- Energy sensors also: `period`, `last_changed`, `historical_data` (last 7 periods); daily sensors also `yesterday`
- Total sensors: `switch_entities`, `gang_powers`, `gang_states`, `total_gangs`, `gangs_on`

`historical_data` and `last_changed` are not written to the recorder database.

## Energy dashboard

Add **one** energy sensor per load under *Individual devices*: the lifetime sensor `sensor.<name>_<load>_energy`, or `sensor.<name>_total_energy` for a multi-gang entry. Don't add the daily, weekly and monthly sensors as well, or the same energy is counted several times.

## Today's consumption ("Consumo de hoje")

Use the daily sensor (`..._energy_daily`, or `..._total_energy_daily` for a multi-gang entry). It resets at local midnight and updates every minute while a load is on. Its `yesterday` attribute holds the previous day.

## How it works

1. The integration follows the state of each entity. `on` counts as on, and anything else (`off`, `unavailable`, ...) as off.
2. Power = watts per load × number of loads, × brightness / 255 for a scaled light.
3. Energy (Wh) = power × hours on. It accrues on every state change and every 60 s while on.
4. At local midnight (and on start-up, if Home Assistant was off over midnight) each daily, weekly and monthly counter closes its period into history and starts again at 0.
5. Counters and history are saved to `.storage/switch_energy_statistics_storage_<entry_id>` within 30 s of a change and on shutdown.

## Services

All services are admin-only.

### switch_energy_statistics.reset_energy

Reset the current period of an energy sensor to 0. With `period`, reset that period of the same load instead.

```yaml
action: switch_energy_statistics.reset_energy
data:
  entity_id: sensor.garagem_energy_statistics_garagem_luz_energy_daily
  period: weekly  # optional: daily, weekly, monthly, lifetime
```

### switch_energy_statistics.set_energy

Set the energy (Wh) of the period containing `date` (the day, ISO week or month, matching the sensor). Without `date` it sets the current period. On the lifetime sensor it sets the total.

```yaml
action: switch_energy_statistics.set_energy
data:
  entity_id: sensor.garagem_energy_statistics_garagem_luz_energy_daily
  energy: 150.5
  date: "2026-10-14"
```

### switch_energy_statistics.export_data

Return a sensor's history and fire it as a `switch_energy_statistics_data_export` event. `start_date` and `end_date` filter by the first day of each period.

```yaml
action: switch_energy_statistics.export_data
data:
  entity_id: sensor.garagem_energy_statistics_garagem_luz_energy_weekly
  start_date: "2026-09-01"
response_variable: export
```

### switch_energy_statistics.attach

See [Attaching loads from a script](#attaching-loads-from-a-script-attach-service).

## Upgrading from 2.1.x

Existing entries migrate automatically (config entry 1.1 → 1.2, storage 1.1 → 1.2). Unique IDs and entity IDs don't change.

- Gang keys are normalised, a missing load count defaults to 1, and the legacy single `switch_entity` shape becomes gang 1.
- Weekly history keys are relabelled from the old `%Y-W%U` format to ISO weeks (`2026-W42`). Values are kept, and keys that can't be parsed are left as they are.
- On the first start, each daily/weekly/monthly counter continues from the sensor's restored state if that state is from the current period. Otherwise it starts at 0. The restored state replaces the pre-upgrade history value for the current period; closed periods are untouched.
- The lifetime sensors are new and start at 0.

## Troubleshooting

- **Values look wrong**: check the watts and load counts (Configure). Fix a period with `set_energy` or `reset_energy`.
- **Sensor stays at 0**: the entity has to report `on`. Check its state in Developer tools.
- **Debug logging**:

```yaml
logger:
  logs:
    custom_components.switch_energy_statistics: debug
```

## Limitations

- At most 8 gangs per entry; the watts are estimates, not measurements.
- Energy used while Home Assistant is stopped is not counted.

## Changelog

### 2.2.0

This release implements the 33 reviewed improvements:

**Bugs**
1. Daily/weekly/monthly totals now reset at each period boundary. Before, they could keep growing across days, and a reset saved the old total under the new period's key.
2. Periods follow local time (not UTC) and reset on a schedule at midnight / Monday / the 1st, also when the load is idle, and on start-up.
3. Energy accrues every 60 s while a load is on, not only when it switches off.
4. One shared store per entry, saved with a 30 s delayed write and on shutdown. Before, it was only saved on unload, and the sensors overwrote each other's keys.
5. Gang keys are normalised. Before, opening the options form showed 10 W and pressing Submit saved it.
6. Options changes apply right away (the entry reloads).
7. The services work. Before, all three did nothing.
8. The legacy `switch_entity` entry shape is migrated.
9. Total sensors are built from the same gangs as the gang sensors, so watts can't be matched to the wrong gang.

**Energy dashboard**
10. New lifetime energy sensors (per gang and total) that never reset.
11. `historical_data` and `last_changed` are kept out of the recorder.
12. Existing sensors stay in Wh; the new lifetime sensors are suggested in kWh.
13. The docs recommend a single energy sensor per load.

**Multi-load**
14. Number of loads per gang (power = watts × loads).
15. Watts limit raised to 5000 W.
16. Optional brightness scaling for lights.
17. `fan` and `input_boolean` entities are supported.

**Attach UX**
18. Entity selector instead of a scraped dropdown.
19. Two-step setup: name + entities, then watts and loads.
20. English and Brazilian Portuguese translations.
21. An entity can only be attached once.
22. Options flow uses the current `self.config_entry` pattern.
23. New `attach` service.
24. Reconfigure step (add, replace or remove gangs).
25. One device per entry.

**Daily energy**
26. The daily sensor is a correct "today" value.
27. `yesterday` attribute on daily sensors.

**Housekeeping**
28. Runtime data in `entry.runtime_data`.
29. History trimmed to about 400 days / 104 weeks / 36 months.
30. Manifest and HACS metadata point at the upstream repository; version 2.2.0.
31. README, HACS guide, examples and install script updated.
32. Cleanups: no `@callback` on coroutines, config-entry-only `CONFIG_SCHEMA`, unused constants removed.
33. ISO week labels, with a storage migration that relabels existing weekly history.

## License

This project is licensed under the MIT License.
