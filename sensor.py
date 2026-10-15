"""Sensor platform for Switch Energy Statistics."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util.unit_conversion import EnergyConverter

from .const import ALL_PERIODS, DOMAIN, NAME, PERIOD_DAILY, PERIOD_LIFETIME, VERSION
from .tracker import (
    TOTAL_SCOPE,
    Gang,
    SwitchEnergyTracker,
    energy_unique_id,
    power_unique_id,
)

_LOGGER = logging.getLogger(__name__)

RECENT_HISTORY = 7  # periods shown in the historical_data attribute


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Switch Energy Statistics sensors."""
    tracker: SwitchEnergyTracker = entry.runtime_data

    # Remove sensors of gangs that were removed by a reconfigure.
    registry = er.async_get(hass)
    expected = tracker.expected_unique_ids()
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if reg_entry.domain == "sensor" and reg_entry.unique_id not in expected:
            _LOGGER.info("Removing %s: its gang is no longer configured", reg_entry.entity_id)
            registry.async_remove(reg_entry.entity_id)

    entities: list[SensorEntity] = []
    for gang in tracker.gangs:
        entities.extend(
            SwitchEnergyStatisticsSensor(tracker, entry, gang, period)
            for period in ALL_PERIODS
        )
        entities.append(SwitchPowerSensor(tracker, entry, gang))

    if tracker.has_total:
        entities.extend(
            SwitchEnergyStatisticsSensor(tracker, entry, None, period)
            for period in ALL_PERIODS
        )
        entities.append(SwitchPowerSensor(tracker, entry, None))

    async_add_entities(entities)


class _SwitchEnergyBaseSensor(SensorEntity):
    """Common behaviour: device, naming, tracker updates."""

    _attr_should_poll = False

    def __init__(
        self, tracker: SwitchEnergyTracker, entry: ConfigEntry, gang: Gang | None
    ) -> None:
        self._tracker = tracker
        self._gang = gang
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=tracker.name,
            manufacturer=NAME,
            model="Estimated consumption",
            sw_version=VERSION,
        )

    @property
    def _scope(self) -> str:
        return self._gang.key if self._gang else TOTAL_SCOPE

    @property
    def _uid_scope(self) -> str:
        return self._gang.entity_id if self._gang else TOTAL_SCOPE

    @property
    def _label(self) -> str:
        """Return the name prefix: '<name> <load>' or '<name> Total'."""
        load = self._gang.friendly_name if self._gang else "Total"
        return f"{self._tracker.name} {load}"

    async def async_added_to_hass(self) -> None:
        """Follow tracker updates."""
        await super().async_added_to_hass()
        self.async_on_remove(self._tracker.async_add_listener(self.async_write_ha_state))

    def _gang_attributes(self) -> dict[str, Any]:
        tracker = self._tracker
        if self._gang:
            gang = self._gang
            attrs = {
                "switch_entity": gang.entity_id,
                "gang_number": gang.number,
                "gang_power": gang.nominal_power,
                "load_power": gang.load_power,
                "load_count": gang.quantity,
                "is_on": gang.is_on,
            }
            if gang.brightness_factor is not None:
                attrs["brightness_factor"] = round(gang.brightness_factor, 3)
            return attrs
        return {
            "switch_entities": [gang.entity_id for gang in tracker.gangs],
            "gang_powers": [gang.nominal_power for gang in tracker.gangs],
            "gang_states": {gang.entity_id: gang.is_on for gang in tracker.gangs},
            "total_gangs": len(tracker.gangs),
            "gangs_on": sum(1 for gang in tracker.gangs if gang.is_on),
        }


class SwitchEnergyStatisticsSensor(_SwitchEnergyBaseSensor, RestoreEntity):
    """Estimated energy of a gang (or of all gangs) over a period."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _unrecorded_attributes = frozenset({"historical_data", "last_changed"})

    def __init__(
        self,
        tracker: SwitchEnergyTracker,
        entry: ConfigEntry,
        gang: Gang | None,
        period: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(tracker, entry, gang)
        self._period = period
        self._counter = tracker.counter(self._scope, period)
        self._attr_unique_id = energy_unique_id(entry.entry_id, self._uid_scope, period)
        if period == PERIOD_LIFETIME:
            # Never resets: the sensor to add to the Energy dashboard.
            self._attr_name = f"{self._label} Energy"
            self._attr_suggested_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
            self._attr_suggested_display_precision = 3
        else:
            self._attr_name = f"{self._label} Energy {period.title()}"
            self._attr_suggested_display_precision = 2

    async def async_added_to_hass(self) -> None:
        """Seed the tracker from the restored state on the first run."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        value = 0.0
        if last_state is not None and last_state.state not in (
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            try:
                # The state is in the display unit, which may be kWh.
                value = EnergyConverter.convert(
                    float(last_state.state),
                    last_state.attributes.get(
                        "unit_of_measurement", UnitOfEnergy.WATT_HOUR
                    ),
                    UnitOfEnergy.WATT_HOUR,
                )
            except (ValueError, HomeAssistantError):
                value = 0.0
        last_updated = last_state.last_updated if last_state else None
        if last_updated is not None:
            self._tracker.async_seed(self._counter.counter_id, value, last_updated)

    @property
    def native_value(self) -> float:
        """Return the energy in Wh."""
        return round(self._counter.value, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = self._gang_attributes()
        attrs["period"] = self._period
        if self._gang and self._gang.last_changed:
            attrs["last_changed"] = self._gang.last_changed.isoformat()
        if self._period == PERIOD_DAILY:
            yesterday = self._tracker.yesterday(self._counter)
            attrs["yesterday"] = round(yesterday, 2) if yesterday is not None else None
        if self._period != PERIOD_LIFETIME:
            history = self._tracker.history(self._counter)
            attrs["historical_data"] = {
                key: round(value, 2)
                for key, value in list(history.items())[-RECENT_HISTORY:]
            }
        return attrs


class SwitchPowerSensor(_SwitchEnergyBaseSensor):
    """Estimated current power of a gang (or of all gangs)."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_suggested_display_precision = 1

    def __init__(
        self, tracker: SwitchEnergyTracker, entry: ConfigEntry, gang: Gang | None
    ) -> None:
        """Initialize the sensor."""
        super().__init__(tracker, entry, gang)
        self._attr_unique_id = power_unique_id(entry.entry_id, self._uid_scope)
        self._attr_name = f"{self._label} Power"

    @property
    def native_value(self) -> float:
        """Return the current power in W."""
        if self._gang:
            return round(self._gang.power, 2)
        return round(self._tracker.total_power, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return self._gang_attributes()
