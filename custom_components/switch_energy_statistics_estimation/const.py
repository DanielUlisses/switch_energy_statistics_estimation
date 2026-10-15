"""Constants for the Switch Energy Statistics component."""

from __future__ import annotations

DOMAIN = "switch_energy_statistics"
NAME = "Switch Energy Statistics Estimation"
VERSION = "2.2.0"

# Platforms
PLATFORMS = ["sensor"]

# Config entry schema version (bump MINOR for additive, backwards-compatible changes)
CONFIG_VERSION = 1
CONFIG_MINOR_VERSION = 2

# Configuration keys
CONF_SWITCH_ENTITY = "switch_entity"  # Legacy single-entity key, migrated away
CONF_GANG_COUNT = "gang_count"
CONF_GANG_POWER = "gang_power"  # {gang: watts per load}
CONF_GANG_QUANTITY = "gang_quantity"  # {gang: number of loads}
CONF_GANG_ENTITIES = "gang_entities"  # {gang: entity_id}
CONF_BRIGHTNESS_SCALING = "brightness_scaling"
CONF_NAME = "name"
CONF_ENTITIES = "entities"

# Default values
DEFAULT_NAME = "Switch Energy Statistics"
DEFAULT_GANG_POWER = 10.0  # Default 10W per load
DEFAULT_GANG_QUANTITY = 1
MAX_GANG_COUNT = 8
MIN_GANG_POWER = 0.1
MAX_GANG_POWER = 5000.0
MAX_GANG_QUANTITY = 100

# Entity domains whose on/off state drives a load
SUPPORTED_DOMAINS = ["switch", "light", "fan", "input_boolean"]

# Entity suffixes (part of the unique_id: never change them)
SUFFIX_ENERGY_DAILY = "energy_daily"
SUFFIX_ENERGY_WEEKLY = "energy_weekly"
SUFFIX_ENERGY_MONTHLY = "energy_monthly"
SUFFIX_ENERGY_LIFETIME = "energy_total"
SUFFIX_POWER = "power"

# Time periods
PERIOD_DAILY = "daily"
PERIOD_WEEKLY = "weekly"
PERIOD_MONTHLY = "monthly"
PERIOD_LIFETIME = "lifetime"
RESET_PERIODS = (PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY)
ALL_PERIODS = (*RESET_PERIODS, PERIOD_LIFETIME)

# How many closed periods of history to keep
HISTORY_LIMITS = {PERIOD_DAILY: 400, PERIOD_WEEKLY: 104, PERIOD_MONTHLY: 36}

# Update intervals
UPDATE_INTERVAL = 60  # seconds between energy accruals while a load is on
SAVE_DELAY = 30  # seconds to batch storage writes

# Storage keys
STORAGE_KEY = f"{DOMAIN}_storage"
STORAGE_VERSION = 1
STORAGE_MINOR_VERSION = 2  # 1.2: weekly keys relabelled to ISO weeks
