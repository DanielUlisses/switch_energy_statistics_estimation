"""Constants for the Switch Energy Statistics component."""

from __future__ import annotations

DOMAIN = "switch_energy_statistics"
NAME = "Switch Energy Statistics Estimation"
VERSION = "1.0.0"

# Platforms
PLATFORMS = ["sensor"]

# Configuration keys
CONF_SWITCH_ENTITY = "switch_entity"  # Legacy - kept for backward compatibility
CONF_GANG_COUNT = "gang_count"
CONF_GANG_POWER = "gang_power"
CONF_GANG_ENTITIES = "gang_entities"
CONF_NAME = "name"

# Default values
DEFAULT_NAME = "Switch Energy Statistics"
DEFAULT_GANG_POWER = 10.0  # Default 10W per gang
MIN_GANG_COUNT = 1
MAX_GANG_COUNT = 8

# Entity suffixes
SUFFIX_ENERGY_DAILY = "energy_daily"
SUFFIX_ENERGY_WEEKLY = "energy_weekly"
SUFFIX_ENERGY_MONTHLY = "energy_monthly"
SUFFIX_POWER = "power"
SUFFIX_STATUS = "status"

# Time periods
PERIOD_DAILY = "daily"
PERIOD_WEEKLY = "weekly"
PERIOD_MONTHLY = "monthly"

# Update intervals
UPDATE_INTERVAL = 60  # seconds

# Storage keys
STORAGE_KEY = f"{DOMAIN}_storage"
STORAGE_VERSION = 1
