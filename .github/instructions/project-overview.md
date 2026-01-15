# Project Documentation for AI Agents

## Project Overview

**Project Name**: Home Assistant Energy Management Suite
**Repository**: zigbee-devices
**Primary Domain**: Energy management and consumption tracking
**Technology Stack**: Python 3.9+, Home Assistant Core 2024.1+, Zigbee2MQTT

## Architecture Summary

This repository implements a multi-component architecture with three main areas:

### 1. Home Assistant Custom Components
Located in `custom_components/`, these are standalone Python packages that extend Home Assistant functionality:

#### Switch Energy Statistics Estimation (`switch_energy_statistics_estimation/`)
- **Core Function**: Estimates and tracks energy consumption for multi-gang switches (1-8 gangs)
- **Key Files**:
  - `manifest.json`: Component metadata and dependencies
  - `__init__.py`: Integration setup and lifecycle management
  - `config_flow.py`: Multi-step configuration wizard
  - `sensor.py`: Energy sensor entities with Home Assistant Energy Dashboard integration
  - `services.py`: Custom services for data management
  - `const.py`: Constants and configuration definitions

#### Energy Generation Report (`energy_generation_report/`)
- **Core Function**: Solar energy generation reporting with billing period management
- **Key Features**: ApexCharts integration, grid balance tracking, service-based data entry
- **Integration Points**: Home Assistant Energy Dashboard, ApexCharts frontend

### 2. Zigbee Device Converters
Located in `relay-2-types/`, these are JavaScript modules for Zigbee2MQTT:

- **Purpose**: Extend Zigbee2MQTT device support for specialized Tuya switches
- **Format**: Modern Zigbee2MQTT converter definitions (.mjs files)
- **Target Devices**: Multi-gang switches without neutral wire requirement

### 3. Development Infrastructure
- **Code Quality**: Black formatter (88 chars), isort, yamllint
- **Automation**: Comprehensive Makefile with 20+ development targets
- **CI/CD**: GitHub Actions for component-specific releases and PR validation
- **Version Management**: Independent semantic versioning per component

## Key Design Patterns

### Home Assistant Integration Patterns

#### Entity Lifecycle Management
```python
# Integration Entry Point
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up integration from config entry."""
    hass.data.setdefault(DOMAIN, {})
    coordinator = IntegrationDataCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
```

#### Entity Implementation with Energy Dashboard Integration
```python
class EnergyEstimationSensor(SensorEntity):
    """Energy consumption sensor for multi-gang switches."""

    def __init__(self, coordinator, description: SensorEntityDescription):
        """Initialize sensor with energy dashboard compatibility."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.title,
            manufacturer="Energy Management Suite",
        )

        # Energy Dashboard Integration
        if description.device_class == SensorDeviceClass.ENERGY:
            self._attr_state_class = SensorStateClass.TOTAL
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
```

#### Multi-Step Configuration Flow
```python
class SwitchEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle multi-step configuration for switch energy estimation."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1: Gang count selection."""
        if user_input is not None:
            self._gang_count = user_input[CONF_GANG_COUNT]
            return await self.async_step_power_config()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_GANG_COUNT, default=2): vol.In(range(1, 9))
            })
        )

    async def async_step_power_config(self, user_input: dict[str, Any] | None = None):
        """Step 2: Power configuration per gang."""
        # Dynamic schema based on gang count
        schema = {}
        for i in range(1, self._gang_count + 1):
            schema[vol.Required(f"power_gang_{i}", default=10)] = vol.Coerce(float)

        if user_input is not None:
            return self.async_create_entry(
                title=f"{self._gang_count}-Gang Switch Energy",
                data={
                    CONF_GANG_COUNT: self._gang_count,
                    CONF_POWER_CONSUMPTION: user_input,
                }
            )

        return self.async_show_form(step_id="power_config", data_schema=vol.Schema(schema))
```

### Zigbee2MQTT Converter Patterns

#### Modern Tuya Device Definition
```javascript
const definition = {
    fingerprint: [{
        modelID: 'TS000F',
        manufacturerName: '_TZ3000_pe6rtun6',
    }],
    model: 'TS000F_2_gang_switch',
    vendor: 'Tuya',
    description: '2 gang switch module without neutral wire',
    exposes: [
        e.switch().withEndpoint("l1").setAccess("state", ea.STATE_SET),
        e.switch().withEndpoint("l2").setAccess("state", ea.STATE_SET),
        e.power_on_behavior().withAccess(ea.STATE_SET),
    ],
    extend: [tuya.modernExtend.tuyaBase({dp: true})],
    meta: {
        multiEndpoint: true,
        multiEndpointSkip: ["power_on_behavior"],
        tuyaDatapoints: [
            [1, "state_l1", tuya.valueConverter.onOff],
            [2, "state_l2", tuya.valueConverter.onOff],
            [14, "power_on_behavior", tuya.valueConverter.powerOnBehavior],
        ],
    },
};
```

## Development Workflow Automation

### Makefile Targets (Key Operations)
```bash
make setup           # Complete development environment setup
make format lint     # Code formatting and quality checks
make commit-check    # Pre-commit validation
make clean-build     # Clean rebuild of environment
make help           # Show all available targets
```

### Release Management
- **Component-Specific Tags**: `switch_energy_statistics_estimation-v1.2.3`
- **GitHub Actions**: Automated releases with component change detection
- **HACS Integration**: Multi-component repository with release filters

### Code Quality Standards
- **Black**: 88-character line length, no flake8 (simplified toolchain)
- **isort**: Black profile compatibility for import sorting
- **yamllint**: 200-character line length for GitHub Actions workflows
- **Pre-commit hooks**: Automated enforcement of quality standards

## Integration Points & Dependencies

### Home Assistant Core Integration
- **Minimum Version**: Home Assistant Core 2024.1+
- **Entity Platform**: Sensor entities with Energy Dashboard compatibility
- **Configuration**: Multi-step config flows with validation
- **Services**: Custom services for data management and export
- **Data Storage**: Persistent data using `hass.data` and file storage

### HACS Multi-Component Support
- **Repository Type**: Custom multi-component repository
- **Release Detection**: Component-specific release filters
- **Individual Downloads**: Separate component ZIP files per release

### Zigbee2MQTT Integration
- **Converter Location**: External converters directory
- **Format**: Modern ESM modules (.mjs)
- **Device Support**: Tuya multi-gang switches, no-neutral configurations

## Testing & Validation Strategy

### Automated Testing
- **GitHub Actions**: PR validation with code quality checks
- **Pre-commit**: Local validation before commit
- **Structure Validation**: Component structure and manifest validation

### Manual Testing
- **Development Environment**: Local Home Assistant setup
- **Physical Devices**: Zigbee device testing for converters
- **Energy Dashboard**: Integration testing with HA Energy features

This comprehensive documentation provides AI agents with deep context about the repository architecture, development patterns, and integration points for more effective assistance with code development, debugging, and feature enhancement.
