# AI Agent Quick Reference Guide

## Repository Identity
**Name**: Home Assistant Energy Management Suite
**Focus**: Energy tracking, solar reporting, Zigbee device support
**Architecture**: Multi-component Home Assistant repository + Zigbee2MQTT converters

## Quick Context for AI Agents

### 🎯 Primary Use Cases
1. **Switch Energy Tracking**: Multi-gang switch consumption estimation (1-8 gangs)
2. **Solar Reporting**: Generation tracking with billing periods and ApexCharts
3. **Zigbee Device Support**: Custom Tuya switch converters for Zigbee2MQTT

### 🔧 Development Workflow
```bash
make setup          # Complete environment setup
make format lint    # Code quality (Black + yamllint only, no flake8)
make commit-check   # Pre-commit validation
```

### 📁 Key File Locations
```
custom_components/
├── switch_energy_statistics_estimation/    # Multi-gang switch energy tracking
└── energy_generation_report/               # Solar generation reporting

relay-2-types/                              # Zigbee2MQTT converters
├── 2-gang-switch-converter.mjs             # Tuya 2-gang no-neutral
└── 2type-switch-converter.mjs              # Alternative implementation

.github/instructions/                        # AI agent guidance
├── instructions.md                          # Detailed development guidance
├── repository-context.md                    # Architecture overview
└── project-overview.md                      # Comprehensive project docs
```

### 🏗️ Architecture Patterns

#### Home Assistant Entity Pattern
```python
class EnergyEstimationSensor(SensorEntity):
    """Energy sensor with HA Energy Dashboard integration."""

    def __init__(self, coordinator, description):
        self._attr_unique_id = f"{coordinator.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(...)  # Device registry integration

        # Energy Dashboard compatibility
        if description.device_class == SensorDeviceClass.ENERGY:
            self._attr_state_class = SensorStateClass.TOTAL
```

#### Configuration Flow Pattern (Multi-Step)
```python
async def async_step_user(self, user_input=None):
    """Step 1: Gang count selection."""
    if user_input:
        self._gang_count = user_input[CONF_GANG_COUNT]
        return await self.async_step_power_config()
    # Show form for gang count selection

async def async_step_power_config(self, user_input=None):
    """Step 2: Power configuration per gang."""
    # Dynamic schema based on gang count
```

#### Zigbee Converter Pattern
```javascript
const definition = {
    fingerprint: [{modelID: 'TS000F', manufacturerName: '_TZ3000_pe6rtun6'}],
    model: 'TS000F_2_gang_switch',
    vendor: 'Tuya',
    exposes: [e.switch().withEndpoint("l1"), e.switch().withEndpoint("l2")],
    extend: [tuya.modernExtend.tuyaBase({dp: true})],
    meta: {
        multiEndpoint: true,
        tuyaDatapoints: [[1, "state_l1", tuya.valueConverter.onOff], ...]
    }
};
```

### 🔄 Release Strategy
- **Component Versioning**: Independent semantic versioning per component
- **Tag Format**: `switch_energy_statistics_estimation-v1.2.3`
- **HACS Integration**: Multi-component with release_filter patterns
- **GitHub Actions**: Automated component-specific releases

### ⚡ Code Quality Standards
- **Formatting**: Black only (88 chars, no flake8)
- **Import Sorting**: isort with black profile
- **YAML**: yamllint with 200-char line length
- **Pre-commit**: Automated validation on commit

### 🎯 Common Tasks & Solutions

#### Adding New Energy Sensor
1. Define `SensorEntityDescription` with proper `device_class` and `state_class`
2. Implement entity with `unique_id` and `device_info`
3. Ensure Energy Dashboard compatibility
4. Add to `SENSORS` constant in appropriate component

#### Creating New Configuration Step
1. Add step method: `async def async_step_your_step(self, user_input=None)`
2. Define validation schema with `vol.Schema({})`
3. Handle user input and navigate to next step or create entry
4. Update config flow VERSION if schema changes

#### Adding Zigbee Device Support
1. Identify device fingerprint (modelID, manufacturerName)
2. Define exposes for device capabilities
3. Map Tuya datapoints to Zigbee attributes
4. Test with physical device and Zigbee2MQTT

This quick reference provides essential context for AI agents to understand the repository structure, development patterns, and common tasks without needing to read extensive documentation.
