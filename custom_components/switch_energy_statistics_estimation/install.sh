#!/bin/bash

# Switch Energy Statistics HACS Setup Script
# This script helps set up the repository for HACS installation

set -e

echo "Switch Energy Statistics HACS Setup"
echo "===================================="

echo "This integration is designed to be installed via HACS (Home Assistant Community Store)."
echo ""
echo "HACS Installation (Recommended):"
echo "1. Ensure HACS is installed in your Home Assistant"
echo "2. Go to HACS → Integrations"
echo "3. Click the three dots menu → Custom repositories"
echo "4. Add this repository URL as an Integration:"
echo "   https://github.com/danielulisses/zigbee-devices"
echo "5. Search for 'Switch Energy Statistics Estimation'"
echo "6. Install and restart Home Assistant"
echo ""
echo "Manual Installation:"
echo "If you prefer manual installation, run: $0 manual <path_to_homeassistant_config>"
echo ""

# Check if manual installation is requested
if [ "$1" = "manual" ]; then
    if [ -z "$2" ]; then
        echo "Usage for manual install: $0 manual <path_to_homeassistant_config>"
        echo "Example: $0 manual /home/homeassistant/.homeassistant"
        echo "         $0 manual /config (for Home Assistant OS/Docker)"
        exit 1
    fi
    HA_CONFIG_DIR="$2"
else
    echo "Use HACS for easy installation and automatic updates!"
    exit 0
fi

HA_CONFIG_DIR="$1"
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
TARGET_DIR="$CUSTOM_COMPONENTS_DIR/switch_energy_statistics"
SOURCE_DIR="$(dirname "$0")"

# Verify Home Assistant config directory
if [ ! -f "$HA_CONFIG_DIR/configuration.yaml" ]; then
    echo "Error: $HA_CONFIG_DIR doesn't appear to be a Home Assistant config directory"
    echo "       (configuration.yaml not found)"
    exit 1
fi

echo "Home Assistant config directory: $HA_CONFIG_DIR"
echo "Source directory: $SOURCE_DIR"

# Create custom_components directory if it doesn't exist
if [ ! -d "$CUSTOM_COMPONENTS_DIR" ]; then
    echo "Creating custom_components directory..."
    mkdir -p "$CUSTOM_COMPONENTS_DIR"
fi

# Remove existing installation if it exists
if [ -d "$TARGET_DIR" ]; then
    echo "Removing existing installation..."
    rm -rf "$TARGET_DIR"
fi

# Create target directory
echo "Creating component directory..."
mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/translations"

# Copy files
echo "Copying component files..."
cp "$SOURCE_DIR/__init__.py" "$TARGET_DIR/"
cp "$SOURCE_DIR/manifest.json" "$TARGET_DIR/"
cp "$SOURCE_DIR/const.py" "$TARGET_DIR/"
cp "$SOURCE_DIR/config_flow.py" "$TARGET_DIR/"
cp "$SOURCE_DIR/sensor.py" "$TARGET_DIR/"
cp "$SOURCE_DIR/services.py" "$TARGET_DIR/"
cp "$SOURCE_DIR/services.yaml" "$TARGET_DIR/"
cp "$SOURCE_DIR/translations/en.json" "$TARGET_DIR/translations/"

# Set appropriate permissions
echo "Setting file permissions..."
chmod -R 644 "$TARGET_DIR"/*
find "$TARGET_DIR" -type d -exec chmod 755 {} \;

echo ""
echo "Manual installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Push this repository to GitHub (if not already done)"
echo "2. Restart Home Assistant"
echo "3. Go to Settings → Devices & Services → Integrations"
echo "4. Click 'Add Integration'"
echo "5. Search for 'Switch Energy Statistics Estimation'"
echo "6. Follow the configuration wizard"
echo ""
echo "For HACS installation (recommended for updates):"
echo "1. Add https://github.com/danielulisses/zigbee-devices as custom repo in HACS"
echo "2. Install 'Switch Energy Statistics Estimation' from HACS"
echo ""
echo "For help and examples, see:"
echo "- README.md"
echo "- examples.md"
echo ""
echo "Installed files:"
find "$TARGET_DIR" -type f | sed "s|^|  |"
