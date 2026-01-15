# Repository Architecture & AI Agent Instructions

## Repository Overview

This repository contains the **Switch Energy Statistics Estimation** Home Assistant custom component for tracking energy consumption of multi-gang switches.

### Repository Structure
```
switch_energy_statistics_estimation/
├── custom_components/              # Home Assistant custom integration
│   └── switch_energy_statistics_estimation/  # Energy tracking for multi-gang switches
├── .github/                        # GitHub Actions workflows & templates
│   ├── workflows/                  # CI/CD automation
│   └── instructions/               # AI agent guidance
├── DEVELOPMENT.md                  # Development environment setup
├── README.md                       # Component documentation
├── pyproject.toml                  # Python project configuration
├── requirements.txt                # Runtime dependencies
└── requirements-dev.txt            # Development dependencies
```

## Component Architecture

### Switch Energy Statistics Estimation
- **Purpose**: Track energy consumption for multi-gang switches (1-8 gangs)
- **Technology Stack**: Home Assistant Custom Integration, Python 3.9+
- **Key Features**: Energy dashboard integration, configurable power per gang, historical tracking
- **Dependencies**: Home Assistant Core 2024.1+

## Related Repositories

This component was separated from a multi-component repository. Related repositories:

- **[Energy Generation Report](https://github.com/danielulisses/energy-generation-report)**: Solar generation reporting with interactive charts
- **[Zigbee Devices](https://github.com/danielulisses/zigbee-devices)**: Zigbee2MQTT device converters for Tuya switches

## Development Workflow

### Code Quality Standards
- **Formatter**: Black (88 character line length)
- **Import Sorting**: isort (black profile)
- **YAML Linting**: yamllint with relaxed line length (200 chars)
- **Pre-commit Hooks**: Automated formatting and validation

### Build & Release Process
- **Component Versioning**: manifest.json version management
- **Release Strategy**: GitHub releases with semantic versioning tags
- **HACS Integration**: Single-component repository with automatic discovery
- **CI/CD**: GitHub Actions for PR validation and automated releases

## AI Agent Guidance

### Context Understanding
When working with this repository, understand that:

1. **Single Component Focus**: This repository contains only the Switch Energy Statistics Estimation component
2. **Energy Management**: Specialized for tracking multi-gang switch energy consumption
3. **Home Assistant Integration**: Built for seamless Home Assistant Energy Dashboard integration
4. **HACS Compatible**: Designed for easy installation and updates through HACS

### Code Patterns to Recognize

#### Home Assistant Integration Patterns
```python
# Standard integration entry point
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up integration from a config entry."""

# Entity pattern with unique_id and device_info
class EnergyEstimationSensor(SensorEntity):
    def __init__(self, config_entry, description):
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(...)
```

#### Configuration Flow Patterns
```python
# Multi-step configuration with validation
class SwitchEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        # Handle gang count selection and power configuration
```

### File Naming Conventions
- **Components**: snake_case directory names
- **Python Files**: snake_case.py
- **Configuration**: lowercase with hyphens (e.g., .pre-commit-config.yaml)
- **Documentation**: UPPERCASE.md for root level, README.md for component docs

### Common Operations

#### Version Management
- Component uses semantic versioning in manifest.json
- Release workflow creates version tags (e.g., v1.2.3)
- HACS automatically detects component updates from releases

#### Development Commands
```bash
make setup          # Initialize development environment
make format lint    # Format and check code quality
make commit-check   # Validate changes before commit
make help          # Show all available commands
```

### Testing Strategy
- **Manual Testing**: Use development environment with make commands
- **CI Validation**: GitHub Actions for structure validation and code quality
- **Integration Testing**: Test in Home Assistant development environment
- **Device Testing**: Physical Zigbee devices for converter validation

## Component-Specific Context

### Switch Energy Statistics Estimation
- **Entity Types**: Sensor entities for energy tracking
- **State Management**: Uses hass.data for persistent storage
- **Configuration**: Multi-step flow for gang count and power settings
- **Services**: Custom services for data management and export
- **Energy Integration**: Compatible with HA Energy Dashboard
- **Gang Support**: Configurable for 1-8 gang switches
- **Power Estimation**: Configurable power consumption per gang
- **Historical Tracking**: Maintains energy consumption history
