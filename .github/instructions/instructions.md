# AI Agent Instructions for Zigbee Devices Repository

You are an expert AI agent specializing in Home Assistant custom component development and Zigbee device integration. This repository contains energy management integrations and Zigbee device converters.

## Repository Context

**Primary Focus**: Energy management and consumption tracking for Home Assistant
**Technology Stack**: Python 3.9+, Home Assistant Core 2024.1+, Zigbee2MQTT converters
**Development Approach**: Black-only formatting, comprehensive Makefile automation, multi-component releases

## Core Responsibilities

### 1. Home Assistant Custom Components
- **Energy Tracking**: Multi-gang switch energy estimation with configurable power consumption
- **Solar Reporting**: Generation tracking with billing periods and ApexCharts integration
- **Entity Management**: Sensor entities with proper unique_id and device_info patterns
- **Configuration Flows**: Multi-step wizards for complex device setup
- **Service Integration**: Custom services for data management and export

### 2. Zigbee Device Integration
- **Zigbee2MQTT Converters**: Custom device definitions for Tuya multi-gang switches
- **Device Fingerprinting**: Manufacturer/model identification patterns
- **Endpoint Mapping**: Multi-endpoint switch configurations without neutral wire
- **Datapoint Translation**: Tuya-specific protocol translations

### 3. Development Automation
- **Code Quality**: Black formatter (88 chars), isort, yamllint automation
- **CI/CD Pipeline**: Component-specific releases, HACS integration, PR validation
- **Development Tools**: Comprehensive Makefile with 20+ automated targets

## Code Standards & Architecture

### Python & Home Assistant Patterns
```python
# Integration Entry Point Pattern
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up integration from config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = IntegrationData(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

# Entity Pattern with Energy Dashboard Integration
class EnergyEstimationSensor(SensorEntity):
    """Energy consumption sensor for multi-gang switches."""

    def __init__(self, config_entry: ConfigEntry, description: SensorEntityDescription):
        """Initialize the sensor."""
        super().__init__()
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.title,
            manufacturer="Custom Integration",
            model="Energy Statistics Estimation",
        )

# Configuration Flow with Multi-Step Validation
class SwitchEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle configuration flow for switch energy estimation."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle initial step - gang count selection."""
        if user_input is not None:
            self._gang_count = user_input[CONF_GANG_COUNT]
            return await self.async_step_power_config()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_GANG_COUNT, default=2): vol.In(range(1, 9))
            })
        )
```

### Zigbee2MQTT Converter Patterns
```javascript
// Modern Converter Definition
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

### Development Workflow Standards
- **Formatting**: Black with 88-character line length (no flake8)
- **Import Sorting**: isort with black profile compatibility
- **YAML**: yamllint with 200-character line length for workflows
- **Pre-commit**: Automated formatting validation before commits
- **Makefile**: Use `make format lint` and `make commit-check` for quality assurance

## Component-Specific Guidance

### Switch Energy Statistics Estimation
**Purpose**: Track energy consumption for multi-gang switches (1-8 gangs)

```python
# Key Constants
CONF_GANG_COUNT = "gang_count"
CONF_POWER_CONSUMPTION = "power_consumption"
DEFAULT_POWER_PER_GANG = 10  # watts

# Entity Descriptions for Energy Dashboard Integration
SENSORS = [
    SensorEntityDescription(
        key="daily_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    SensorEntityDescription(
        key="current_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
]

# Service Implementation Pattern
async def async_reset_energy_data(hass: HomeAssistant, call: ServiceCall) -> None:
    """Reset energy statistics for specified entity."""
    entity_id = call.data.get(ATTR_ENTITY_ID)
    # Implementation for data reset
```

### Energy Generation Report
**Purpose**: Solar energy generation reporting with billing periods

```python
# ApexCharts Integration Pattern
CHARTS_CONFIG = {
    "type": "area",
    "height": "400px",
    "show": {"legend": True},
    "series": [
        {
            "entity": "sensor.solar_generation",
            "name": "Solar Generation",
            "color": "#ff9800",
        }
    ]
}

# Billing Period Management
class BillingPeriodManager:
    """Manage billing periods for energy reporting."""

    def calculate_period_totals(self, start_date: date, end_date: date) -> dict:
        """Calculate energy totals for billing period."""
        return {
            "generation": 0.0,
            "consumption": 0.0,
            "balance": 0.0,
        }
```

## Release & Versioning Strategy

### Component Versioning
- Each component maintains independent semantic versioning in `manifest.json`
- Release workflow creates component-specific tags: `switch_energy_statistics_estimation-v1.2.3`
- HACS uses `release_filter` pattern matching for component detection

### HACS Configuration
```json
// Per-component hacs.json
{
    "name": "Switch Energy Statistics Estimation",
    "content_in_root": false,
    "filename": "switch_energy_statistics_estimation.zip",
    "release_filter": "switch_energy_statistics_estimation-v*"
}
```

### Development Commands
```bash
make setup          # Initialize development environment
make format lint    # Format code and check quality
make commit-check   # Run pre-commit validation
make clean-build    # Clean and rebuild environment
make help          # Show all available targets
```

## Response Guidelines for AI Agents

When providing assistance with this repository:

### 1. **Context Awareness**
- Recognize this as a multi-component Home Assistant repository
- Understand the energy management focus and Zigbee device integration
- Reference specific component architectures and patterns shown above
- Consider the Black-only formatting workflow (no flake8)

### 2. **Code Examples**
- Provide complete, working code that follows the established patterns
- Include proper type hints and async/await usage
- Use the specific constants and entity descriptions shown
- Follow the established file structure and naming conventions

### 3. **Development Workflow**
- Always reference Makefile targets for code quality tasks
- Suggest pre-commit hook usage for validation
- Consider component-specific versioning when making changes
- Reference HACS multi-component configuration requirements

### 4. **Testing & Validation**
- Recommend testing with `make commit-check` before committing
- Suggest component-specific testing approaches
- Consider energy dashboard integration testing
- Validate Zigbee2MQTT converter functionality with physical devices

### 5. **Documentation Standards**
- Update component READMEs when adding features
- Include configuration examples in YAML format
- Document service parameters and usage patterns
- Explain device-specific setup requirements for Zigbee converters

### 6. **Common Problem Areas**
- **Energy Dashboard Integration**: Ensure proper device_class and state_class
- **Multi-Component Releases**: Understand component-specific tagging
- **Zigbee Converter Testing**: Physical device validation requirements
- **Configuration Flow UX**: Multi-step wizard usability

### 7. **Architecture Decisions**
- Prefer async patterns for all Home Assistant integrations
- Use hass.data for persistent storage between restarts
- Implement proper cleanup in async_unload_entry
- Follow Home Assistant entity lifecycle management

This specialized guidance helps ensure all assistance aligns with the repository's specific architecture, development workflow, and component requirements.
