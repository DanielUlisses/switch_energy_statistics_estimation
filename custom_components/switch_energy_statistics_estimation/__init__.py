"""Switch Energy Statistics Estimation for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_GANG_ENTITIES,
    CONFIG_MINOR_VERSION,
    CONFIG_VERSION,
    DOMAIN,
    PLATFORMS,
)
from .services import async_setup_services
from .tracker import SwitchEnergyTracker, entry_store, normalize_entry_data

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(
    hass: HomeAssistant, config: ConfigType
) -> bool:  # pylint: disable=unused-argument
    """Set up the Switch Energy Statistics components."""
    # Set up services
    await async_setup_services(hass)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate an old config entry to the current data shape."""
    if entry.version > CONFIG_VERSION:
        _LOGGER.error(
            "Cannot downgrade %s from version %s.%s",
            entry.title,
            entry.version,
            entry.minor_version,
        )
        return False

    if entry.version == 1 and entry.minor_version < 2:
        # 1.2: str gang keys, per-gang load count, brightness flag, legacy
        # switch_entity folded into gang_entities, gang_power always a dict.
        new_data = normalize_entry_data(entry.data, entry.title)
        if not new_data[CONF_GANG_ENTITIES]:
            _LOGGER.error("%s has no switch entities to migrate", entry.title)
            return False
        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            version=CONFIG_VERSION,
            minor_version=CONFIG_MINOR_VERSION,
        )
        _LOGGER.info(
            "Migrated %s to version %s.%s",
            entry.title,
            CONFIG_VERSION,
            CONFIG_MINOR_VERSION,
        )
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: SwitchEnergyConfigEntry
) -> bool:
    """Set up Switch Energy Statistics from a config entry."""
    tracker = SwitchEnergyTracker(hass, entry)
    await tracker.async_load()
    entry.runtime_data = tracker

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    tracker.async_start()
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SwitchEnergyConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_stop()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete the entry's history file when the entry is deleted."""
    await entry_store(hass, entry.entry_id).async_remove()
