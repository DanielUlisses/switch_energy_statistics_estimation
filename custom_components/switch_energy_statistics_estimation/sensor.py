"""Sensor platform for Switch Energy Statistics."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_GANG_POWER,
    CONF_NAME,
    CONF_SWITCH_ENTITY,
    DOMAIN,
    PERIOD_DAILY,
    PERIOD_MONTHLY,
    PERIOD_WEEKLY,
    STORAGE_KEY,
    STORAGE_VERSION,
    SUFFIX_ENERGY_DAILY,
    SUFFIX_ENERGY_MONTHLY,
    SUFFIX_ENERGY_WEEKLY,
    SUFFIX_POWER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Switch Energy Statistics sensors."""
    # gang_count = entry.data[CONF_GANG_COUNT]  # Kept for future use
    gang_powers = entry.data[CONF_GANG_POWER]
    name = entry.data[CONF_NAME]
    gang_entities = entry.data.get("gang_entities", {})

    # Backward compatibility: if no gang_entities, use the old switch_entity approach
    if not gang_entities and CONF_SWITCH_ENTITY in entry.data:
        switch_entity = entry.data[CONF_SWITCH_ENTITY]
        # Create fake gang entities (this won't work well,
        # but maintains some backward compatibility)
        gang_entities = {1: switch_entity}

    if not gang_entities:
        _LOGGER.error("No gang entities configured for entry %s", entry.entry_id)
        return

    # Create storage for historical data
    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")

    # Create sensors for each gang
    entities = []

    for gang, switch_entity in gang_entities.items():
        gang_power = gang_powers.get(gang, 10.0)

        # Get friendly name for the entity
        entity_friendly_name = get_entity_friendly_name(hass, switch_entity)

        # Create energy sensors for different periods
        entities.extend(
            [
                SwitchEnergyStatisticsSensor(
                    hass,
                    entry.entry_id,
                    switch_entity,
                    gang,
                    gang_power,
                    name,
                    entity_friendly_name,
                    PERIOD_DAILY,
                    store,
                ),
                SwitchEnergyStatisticsSensor(
                    hass,
                    entry.entry_id,
                    switch_entity,
                    gang,
                    gang_power,
                    name,
                    entity_friendly_name,
                    PERIOD_WEEKLY,
                    store,
                ),
                SwitchEnergyStatisticsSensor(
                    hass,
                    entry.entry_id,
                    switch_entity,
                    gang,
                    gang_power,
                    name,
                    entity_friendly_name,
                    PERIOD_MONTHLY,
                    store,
                ),
                # Current power sensor
                SwitchPowerSensor(
                    hass,
                    entry.entry_id,
                    switch_entity,
                    gang,
                    gang_power,
                    name,
                    entity_friendly_name,
                    store,
                ),
            ]
        )

    # Create summary sensors that aggregate all gangs
    if len(gang_entities) > 1:  # Only create summary if multiple gangs
        entities.extend(
            [
                SwitchSummaryEnergyStatisticsSensor(
                    hass,
                    entry.entry_id,
                    list(gang_entities.values()),
                    list(gang_powers.values()),
                    name,
                    PERIOD_DAILY,
                    store,
                ),
                SwitchSummaryEnergyStatisticsSensor(
                    hass,
                    entry.entry_id,
                    list(gang_entities.values()),
                    list(gang_powers.values()),
                    name,
                    PERIOD_WEEKLY,
                    store,
                ),
                SwitchSummaryEnergyStatisticsSensor(
                    hass,
                    entry.entry_id,
                    list(gang_entities.values()),
                    list(gang_powers.values()),
                    name,
                    PERIOD_MONTHLY,
                    store,
                ),
                # Summary power sensor
                SwitchSummaryPowerSensor(
                    hass,
                    entry.entry_id,
                    list(gang_entities.values()),
                    list(gang_powers.values()),
                    name,
                    store,
                ),
            ]
        )

    async_add_entities(entities, True)


def get_entity_friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    """Get friendly name for an entity."""
    if not entity_id:
        return "Unknown"

    # Try to get from entity registry first
    from homeassistant.helpers.entity_registry import (
        async_get as async_get_entity_registry,
    )

    entity_registry = async_get_entity_registry(hass)
    if entity_entry := entity_registry.async_get(entity_id):
        if entity_entry.name:
            return entity_entry.name

    # Fall back to state friendly name
    if state := hass.states.get(entity_id):
        return state.attributes.get(
            "friendly_name", entity_id.split(".")[-1].replace("_", " ").title()
        )

    # Final fallback
    return entity_id.split(".")[-1].replace("_", " ").title()


class SwitchEnergyStatisticsSensor(RestoreEntity, SensorEntity):
    """Sensor for tracking switch energy consumption."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        switch_entity: str,
        gang: int,
        gang_power: float,
        name: str,
        entity_friendly_name: str,
        period: str,
        store: Store,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry_id = entry_id
        self._switch_entity = switch_entity
        self._gang = gang
        self._gang_power = gang_power
        self._base_name = name
        self._entity_friendly_name = entity_friendly_name
        self._period = period
        self._store = store

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
        self._attr_suggested_display_precision = 2

        # Track switch state changes
        self._last_state = None
        self._last_changed = None
        self._energy_value = 0.0
        self._is_on = False

        # Historical data
        self._historical_data = {}

        # Set up unique ID and entity ID
        period_suffix = {
            PERIOD_DAILY: SUFFIX_ENERGY_DAILY,
            PERIOD_WEEKLY: SUFFIX_ENERGY_WEEKLY,
            PERIOD_MONTHLY: SUFFIX_ENERGY_MONTHLY,
        }[period]

        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{switch_entity}_{period_suffix}"
        self._attr_name = f"{name} {entity_friendly_name} Energy {period.title()}"

        # Setup state change tracking
        self._unsubscribe_state_listener = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Restore previous state
        if (last_state := await self.async_get_last_state()) is not None:
            self._energy_value = (
                float(last_state.state)
                if last_state.state not in ("unknown", "unavailable")
                else 0.0
            )

        # Load historical data
        await self._load_historical_data()

        # Start tracking switch state changes
        self._unsubscribe_state_listener = async_track_state_change_event(
            self.hass,
            [self._switch_entity],
            self._handle_switch_state_change,
        )

        # Initialize current state
        switch_state = self.hass.states.get(self._switch_entity)
        if switch_state:
            self._is_on = switch_state.state == STATE_ON
            self._last_changed = dt_util.utcnow()  # Set initial timestamp
            _LOGGER.debug(
                "Gang %d: Initial state: %s", self._gang, "ON" if self._is_on else "OFF"
            )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        if self._unsubscribe_state_listener:
            self._unsubscribe_state_listener()
        await self._save_historical_data()

    async def _load_historical_data(self) -> None:
        """Load historical data from storage."""
        try:
            data = await self._store.async_load()
            if data:
                self._historical_data = data.get(
                    f"gang_{self._gang}_{self._period}", {}
                )
        except Exception as ex:
            _LOGGER.error("Error loading historical data: %s", ex)
            self._historical_data = {}

    async def _save_historical_data(self) -> None:
        """Save historical data to storage."""
        try:
            data = await self._store.async_load() or {}
            data[f"gang_{self._gang}_{self._period}"] = self._historical_data
            await self._store.async_save(data)
        except Exception as ex:
            _LOGGER.error("Error saving historical data: %s", ex)

    @callback
    async def _handle_switch_state_change(self, event) -> None:
        """Handle switch state change."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        await self._update_from_switch_state(new_state.state)
        self.async_write_ha_state()

    async def _update_from_switch_state(self, state: str) -> None:
        """Update energy calculation from switch state."""
        now = dt_util.utcnow()

        # Calculate energy since last update (only if switch was ON)
        if self._last_changed and self._is_on:
            time_diff_hours = (
                now - self._last_changed
            ).total_seconds() / 3600  # Convert to hours
            energy_consumed_wh = self._gang_power * time_diff_hours  # Wh = W × hours

            if energy_consumed_wh > 0:
                self._energy_value += energy_consumed_wh
                _LOGGER.debug(
                    (
                        "Gang %d: Switch was ON for %.3f hours, "
                        "consumed %.3f Wh (%.1f W), total: %.3f Wh"
                    ),
                    self._gang,
                    time_diff_hours,
                    energy_consumed_wh,
                    self._gang_power,
                    self._energy_value,
                )

                # Update historical data
                await self._update_historical_data(energy_consumed_wh, now)

        # Update current state
        previous_state = self._is_on
        self._is_on = state == STATE_ON
        self._last_state = state
        self._last_changed = now

        # Log state changes
        if previous_state != self._is_on:
            _LOGGER.debug(
                "Gang %d: State changed from %s to %s",
                self._gang,
                "ON" if previous_state else "OFF",
                "ON" if self._is_on else "OFF",
            )

        # Reset energy for new period if needed
        await self._check_period_reset(now)

    async def _update_historical_data(self, energy: float, timestamp: datetime) -> None:
        """Update historical data with new energy consumption."""
        date_key = self._get_date_key(timestamp)
        if date_key not in self._historical_data:
            self._historical_data[date_key] = 0.0
        self._historical_data[date_key] += energy

    def _get_date_key(self, timestamp: datetime) -> str:
        """Get the date key for historical data based on period."""
        if self._period == PERIOD_DAILY:
            return timestamp.strftime("%Y-%m-%d")
        if self._period == PERIOD_WEEKLY:
            # Get Monday of the week
            monday = timestamp - timedelta(days=timestamp.weekday())
            return monday.strftime("%Y-W%U")
        if self._period == PERIOD_MONTHLY:
            return timestamp.strftime("%Y-%m")
        return timestamp.strftime("%Y-%m-%d")

    async def _check_period_reset(self, now: datetime) -> None:
        """Check if we need to reset energy for new period."""
        current_key = self._get_date_key(now)

        # If we don't have a record for current period, reset energy
        if current_key not in self._historical_data:
            # Save current energy to historical data first
            if self._energy_value > 0:
                self._historical_data[current_key] = self._energy_value
            self._energy_value = 0.0

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return round(self._energy_value, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {
            "switch_entity": self._switch_entity,
            "gang_number": self._gang,
            "gang_power": self._gang_power,
            "period": self._period,
            "is_on": self._is_on,
            "last_changed": (
                self._last_changed.isoformat() if self._last_changed else None
            ),
        }

        # Add recent historical data
        if self._historical_data:
            recent_data = dict(
                list(self._historical_data.items())[-7:]
            )  # Last 7 periods
            attrs["historical_data"] = recent_data

        return attrs


class SwitchPowerSensor(RestoreEntity, SensorEntity):
    """Sensor for current power consumption of a switch gang."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        switch_entity: str,
        gang: int,
        gang_power: float,
        name: str,
        entity_friendly_name: str,
        store: Store,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry_id = entry_id
        self._switch_entity = switch_entity
        self._gang = gang
        self._gang_power = gang_power
        self._base_name = name
        self._entity_friendly_name = entity_friendly_name
        self._store = store

        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_suggested_display_precision = 1

        self._is_on = False

        # Set up unique ID and entity ID
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{switch_entity}_{SUFFIX_POWER}"
        self._attr_name = f"{name} {entity_friendly_name} Power"

        # Setup state change tracking
        self._unsubscribe_state_listener = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Start tracking switch state changes
        self._unsubscribe_state_listener = async_track_state_change_event(
            self.hass,
            [self._switch_entity],
            self._handle_switch_state_change,
        )

        # Initialize current state
        switch_state = self.hass.states.get(self._switch_entity)
        if switch_state:
            self._is_on = switch_state.state == STATE_ON

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        if self._unsubscribe_state_listener:
            self._unsubscribe_state_listener()

    @callback
    async def _handle_switch_state_change(self, event) -> None:
        """Handle switch state change."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        self._is_on = new_state.state == STATE_ON
        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        """Return the current power consumption."""
        return self._gang_power if self._is_on else 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "switch_entity": self._switch_entity,
            "gang_number": self._gang,
            "gang_power": self._gang_power,
            "is_on": self._is_on,
        }


class SwitchSummaryEnergyStatisticsSensor(RestoreEntity, SensorEntity):
    """Summary sensor for tracking total energy consumption across all gangs."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        switch_entities: list[str],
        gang_powers: list[float],
        name: str,
        period: str,
        store: Store,
    ) -> None:
        """Initialize the summary sensor."""
        self.hass = hass
        self._entry_id = entry_id
        self._switch_entities = switch_entities
        self._gang_powers = gang_powers
        self._base_name = name
        self._period = period
        self._store = store

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
        self._attr_suggested_display_precision = 2

        # Track switch state changes
        self._last_states = {}
        self._last_changed = {}
        self._energy_value = 0.0
        self._gang_states = {}

        # Historical data
        self._historical_data = {}

        # Set up unique ID and entity ID
        period_suffix = {
            PERIOD_DAILY: SUFFIX_ENERGY_DAILY,
            PERIOD_WEEKLY: SUFFIX_ENERGY_WEEKLY,
            PERIOD_MONTHLY: SUFFIX_ENERGY_MONTHLY,
        }[period]

        self._attr_unique_id = f"{DOMAIN}_{entry_id}_total_{period_suffix}"
        self._attr_name = f"{name} Total Energy {period.title()}"

        # Setup state change tracking
        self._unsubscribe_state_listeners = []

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Restore previous state
        if (last_state := await self.async_get_last_state()) is not None:
            self._energy_value = (
                float(last_state.state)
                if last_state.state not in ("unknown", "unavailable")
                else 0.0
            )

        # Load historical data
        await self._load_historical_data()

        # Start tracking all switch entities state changes
        for switch_entity in self._switch_entities:
            listener = async_track_state_change_event(
                self.hass,
                [switch_entity],
                self._handle_switch_state_change,
            )
            self._unsubscribe_state_listeners.append(listener)

        # Initialize current states
        now = dt_util.utcnow()
        for switch_entity in self._switch_entities:
            switch_state = self.hass.states.get(switch_entity)
            if switch_state:
                self._gang_states[switch_entity] = switch_state.state == STATE_ON
                self._last_changed[switch_entity] = now

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        for listener in self._unsubscribe_state_listeners:
            listener()
        await self._save_historical_data()

    async def _load_historical_data(self) -> None:
        """Load historical data from storage."""
        try:
            data = await self._store.async_load()
            if data:
                self._historical_data = data.get(f"total_{self._period}", {})
        except Exception as ex:
            _LOGGER.error("Error loading historical data: %s", ex)
            self._historical_data = {}

    async def _save_historical_data(self) -> None:
        """Save historical data to storage."""
        try:
            data = await self._store.async_load() or {}
            data[f"total_{self._period}"] = self._historical_data
            await self._store.async_save(data)
        except Exception as ex:
            _LOGGER.error("Error saving historical data: %s", ex)

    @callback
    async def _handle_switch_state_change(self, event) -> None:
        """Handle switch state change."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        switch_entity = new_state.entity_id
        await self._update_from_switch_state(switch_entity, new_state.state)
        self.async_write_ha_state()

    async def _update_from_switch_state(self, switch_entity: str, state: str) -> None:
        """Update energy calculation from switch state."""
        now = dt_util.utcnow()

        # Find the index of this switch entity
        try:
            entity_index = self._switch_entities.index(switch_entity)
            gang_power = self._gang_powers[entity_index]
        except (ValueError, IndexError):
            _LOGGER.warning(
                "Switch entity %s not found in configuration", switch_entity
            )
            return

        # Calculate energy since last update (only if switch was ON)
        if (
            switch_entity in self._last_changed
            and switch_entity in self._gang_states
            and self._gang_states[switch_entity]
        ):
            time_diff_hours = (
                now - self._last_changed[switch_entity]
            ).total_seconds() / 3600
            energy_consumed_wh = gang_power * time_diff_hours

            if energy_consumed_wh > 0:
                self._energy_value += energy_consumed_wh
                _LOGGER.debug(
                    (
                        "Summary %s: Gang was ON for %.3f hours, "
                        "consumed %.3f Wh (%.1f W), total: %.3f Wh"
                    ),
                    switch_entity,
                    time_diff_hours,
                    energy_consumed_wh,
                    gang_power,
                    self._energy_value,
                )

                # Update historical data
                await self._update_historical_data(energy_consumed_wh, now)

        # Update current state
        previous_state = self._gang_states.get(switch_entity, False)
        self._gang_states[switch_entity] = state == STATE_ON
        self._last_changed[switch_entity] = now

        # Log state changes
        if previous_state != self._gang_states[switch_entity]:
            _LOGGER.debug(
                "Summary %s: State changed from %s to %s",
                switch_entity,
                "ON" if previous_state else "OFF",
                "ON" if self._gang_states[switch_entity] else "OFF",
            )

        # Reset energy for new period if needed
        await self._check_period_reset(now)

    async def _update_historical_data(self, energy: float, timestamp: datetime) -> None:
        """Update historical data with new energy consumption."""
        date_key = self._get_date_key(timestamp)
        if date_key not in self._historical_data:
            self._historical_data[date_key] = 0.0
        self._historical_data[date_key] += energy

    def _get_date_key(self, timestamp: datetime) -> str:
        """Get the date key for historical data based on period."""
        if self._period == PERIOD_DAILY:
            return timestamp.strftime("%Y-%m-%d")
        if self._period == PERIOD_WEEKLY:
            monday = timestamp - timedelta(days=timestamp.weekday())
            return monday.strftime("%Y-W%U")
        if self._period == PERIOD_MONTHLY:
            return timestamp.strftime("%Y-%m")
        return timestamp.strftime("%Y-%m-%d")

    async def _check_period_reset(self, now: datetime) -> None:
        """Check if we need to reset energy for new period."""
        current_key = self._get_date_key(now)

        if current_key not in self._historical_data:
            if self._energy_value > 0:
                self._historical_data[current_key] = self._energy_value
            self._energy_value = 0.0

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return round(self._energy_value, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {
            "switch_entities": self._switch_entities,
            "gang_powers": self._gang_powers,
            "period": self._period,
            "gang_states": {
                entity: self._gang_states.get(entity, False)
                for entity in self._switch_entities
            },
            "total_gangs": len(self._switch_entities),
        }

        # Add recent historical data
        if self._historical_data:
            recent_data = dict(list(self._historical_data.items())[-7:])
            attrs["historical_data"] = recent_data

        return attrs


class SwitchSummaryPowerSensor(RestoreEntity, SensorEntity):
    """Summary sensor for current total power consumption across all gangs."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        switch_entities: list[str],
        gang_powers: list[float],
        name: str,
        store: Store,
    ) -> None:
        """Initialize the summary sensor."""
        self.hass = hass
        self._entry_id = entry_id
        self._switch_entities = switch_entities
        self._gang_powers = gang_powers
        self._base_name = name
        self._store = store

        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_suggested_display_precision = 1

        self._gang_states = {}

        # Set up unique ID and entity ID
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_total_{SUFFIX_POWER}"
        self._attr_name = f"{name} Total Power"

        # Setup state change tracking
        self._unsubscribe_state_listeners = []

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Start tracking all switch entities state changes
        for switch_entity in self._switch_entities:
            listener = async_track_state_change_event(
                self.hass,
                [switch_entity],
                self._handle_switch_state_change,
            )
            self._unsubscribe_state_listeners.append(listener)

        # Initialize current states
        for switch_entity in self._switch_entities:
            switch_state = self.hass.states.get(switch_entity)
            if switch_state:
                self._gang_states[switch_entity] = switch_state.state == STATE_ON

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        for listener in self._unsubscribe_state_listeners:
            listener()

    @callback
    async def _handle_switch_state_change(self, event) -> None:
        """Handle switch state change."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        switch_entity = new_state.entity_id
        self._gang_states[switch_entity] = new_state.state == STATE_ON
        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        """Return the current total power consumption."""
        total_power = 0.0
        for i, switch_entity in enumerate(self._switch_entities):
            if self._gang_states.get(switch_entity, False):
                try:
                    total_power += self._gang_powers[i]
                except IndexError:
                    pass
        return total_power

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "switch_entities": self._switch_entities,
            "gang_powers": self._gang_powers,
            "gang_states": {
                entity: self._gang_states.get(entity, False)
                for entity in self._switch_entities
            },
            "total_gangs": len(self._switch_entities),
            "gangs_on": sum(1 for state in self._gang_states.values() if state),
        }
