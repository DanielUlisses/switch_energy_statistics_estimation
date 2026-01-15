# Switch Energy Statistics Estimation

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/danielulisses/switch-energy-statistics-estimation.svg?style=for-the-badge)](https://github.com/danielulisses/switch-energy-statistics-estimation/releases)
[![GitHub stars](https://img.shields.io/github/stars/danielulisses/switch-energy-statistics-estimation.svg?style=for-the-badge)](https://github.com/danielulisses/switch-energy-statistics-estimation/stargazers)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)

A Home Assistant custom integration that provides energy consumption tracking and statistics for multi-gang switches (1-8 gangs).

## ✨ Features

- **Multi-Gang Support**: Track energy consumption for switches with 1 to 8 gangs
- **Flexible Power Configuration**: Set different power consumption values for each gang
- **Historical Data**: Track energy consumption over daily, weekly, and monthly periods
- **Home Assistant Energy Dashboard**: Compatible with HA Energy Dashboard
- **Real-time Monitoring**: Tracks switch state changes to calculate accurate energy consumption
- **Data Persistence**: Historical data is stored and survives Home Assistant restarts
- **Service Management**: Built-in services for data management and export

**Perfect for**: Smart switches, relay modules, multi-gang wall switches

## 🚀 Installation

### HACS Installation (Recommended)

1. **Install HACS** if you haven't already: [HACS Installation Guide](https://hacs.xyz/docs/setup/download)

2. **Add Custom Repository**:
   - Go to HACS → Integrations
   - Click the three dots menu (⋮) → Custom repositories
   - Add repository URL: `https://github.com/danielulisses/switch-energy-statistics-estimation`
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

```bash
# Download the latest release
wget https://github.com/danielulisses/switch-energy-statistics-estimation/releases/download/v1.x.x/switch_energy_statistics_estimation.zip

# Extract to custom_components directory
unzip switch_energy_statistics_estimation.zip -d /config/custom_components/

# Restart Home Assistant
```

## 📖 Documentation

For detailed documentation, configuration examples, and troubleshooting, see:

- [📖 Full Documentation](custom_components/switch_energy_statistics_estimation/README.md)
- [🛠️ Development Guide](DEVELOPMENT.md)
- [📝 Examples](custom_components/switch_energy_statistics_estimation/examples.md)

## 🔧 Development

This repository uses a comprehensive development workflow with automated formatting and quality checks.

### Quick Development Setup
```bash
# One-command setup
make setup

# View all available commands
make help

# Format and validate your code
make format lint

# Check if ready for commit
make commit-check
```

### Development Standards
- **Code Formatting**: Black (88 character line length)
- **Import Sorting**: isort (black profile)
- **YAML Linting**: yamllint with relaxed line length
- **Pre-commit Hooks**: Automated validation on commit

📖 **Detailed Development Guide**: [DEVELOPMENT.md](DEVELOPMENT.md)

## 💬 Support & Community

### 🐛 Issues & Bug Reports
Found a bug? Have a feature request?
[🔗 Open an Issue](https://github.com/danielulisses/switch-energy-statistics-estimation/issues/new)

### 💡 Feature Requests
We welcome suggestions for new features or improvements!
[💭 Suggest a Feature](https://github.com/danielulisses/switch-energy-statistics-estimation/discussions)

### ⭐ Show Support
If this integration is helpful, please:
- ⭐ **Star this repository**
- 🍴 **Share with the community**
- 💝 **Contribute improvements**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Made with ❤️ for the Home Assistant community**
