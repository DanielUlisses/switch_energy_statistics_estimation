"""Energy accounting shared by all sensors of one config entry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, STATE_ON
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    ALL_PERIODS,
    CONF_BRIGHTNESS_SCALING,
    CONF_GANG_COUNT,
    CONF_GANG_ENTITIES,
    CONF_GANG_POWER,
    CONF_GANG_QUANTITY,
    CONF_NAME,
    CONF_SWITCH_ENTITY,
    DEFAULT_GANG_POWER,
    DEFAULT_GANG_QUANTITY,
    DEFAULT_NAME,
    DOMAIN,
    HISTORY_LIMITS,
    PERIOD_DAILY,
    PERIOD_LIFETIME,
    PERIOD_MONTHLY,
    PERIOD_WEEKLY,
    RESET_PERIODS,
    SAVE_DELAY,
    STORAGE_KEY,
    STORAGE_MINOR_VERSION,
    STORAGE_VERSION,
    SUFFIX_ENERGY_DAILY,
    SUFFIX_ENERGY_LIFETIME,
    SUFFIX_ENERGY_MONTHLY,
    SUFFIX_ENERGY_WEEKLY,
    SUFFIX_POWER,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PERIOD_SUFFIX = {
    PERIOD_DAILY: SUFFIX_ENERGY_DAILY,
    PERIOD_WEEKLY: SUFFIX_ENERGY_WEEKLY,
    PERIOD_MONTHLY: SUFFIX_ENERGY_MONTHLY,
    PERIOD_LIFETIME: SUFFIX_ENERGY_LIFETIME,
}
TOTAL_SCOPE = "total"


# --------------------------------------------------------------------------
# Config entry data
# --------------------------------------------------------------------------


def _gang_key(raw: Any) -> str | None:
    """Return a gang key as a string number ("1"), whatever shape it was stored in."""
    if isinstance(raw, int):
        return str(raw)
    if match := re.search(r"\d+", str(raw)):
        return str(int(match.group()))
    return None


def _per_gang(raw: Any, gangs: list[str], default: float, cast: type) -> dict[str, Any]:
    """Normalise a per-gang value stored as a dict (int or str keys) or one number."""
    values: dict[str, Any] = {}
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if (gang := _gang_key(key)) is not None:
                try:
                    values[gang] = cast(value)
                except (TypeError, ValueError):
                    continue
    elif isinstance(raw, (int, float)) and not isinstance(raw, bool):
        values = dict.fromkeys(gangs, cast(raw))
    return {gang: values.get(gang, cast(default)) for gang in gangs}


def normalize_entry_data(data: Mapping[str, Any], title: str | None = None) -> dict[str, Any]:
    """Return entry data in the current (1.2) shape.

    Accepts every shape older versions wrote: ``gang_entities`` with int or str
    keys (or a list), the legacy single ``switch_entity``, and ``gang_power`` as a
    per-gang dict or a single number.
    """
    raw_entities = data.get(CONF_GANG_ENTITIES)
    entities: dict[str, str] = {}
    if isinstance(raw_entities, Mapping):
        for key, entity_id in raw_entities.items():
            if entity_id and (gang := _gang_key(key)) is not None:
                entities[gang] = str(entity_id)
    elif isinstance(raw_entities, (list, tuple)):
        entities = {
            str(index): str(entity_id)
            for index, entity_id in enumerate(raw_entities, start=1)
            if entity_id
        }
    if not entities and data.get(CONF_SWITCH_ENTITY):
        entities = {"1": str(data[CONF_SWITCH_ENTITY])}
    entities = dict(sorted(entities.items(), key=lambda item: int(item[0])))
    gangs = list(entities)

    return {
        CONF_NAME: data.get(CONF_NAME) or title or DEFAULT_NAME,
        CONF_GANG_COUNT: len(gangs),
        CONF_GANG_ENTITIES: entities,
        CONF_GANG_POWER: _per_gang(
            data.get(CONF_GANG_POWER), gangs, DEFAULT_GANG_POWER, float
        ),
        CONF_GANG_QUANTITY: _per_gang(
            data.get(CONF_GANG_QUANTITY), gangs, DEFAULT_GANG_QUANTITY, int
        ),
        CONF_BRIGHTNESS_SCALING: bool(data.get(CONF_BRIGHTNESS_SCALING, False)),
    }


# --------------------------------------------------------------------------
# Periods
# --------------------------------------------------------------------------


def period_key(period: str, when: date) -> str | None:
    """Return the history key of the period containing ``when`` (local date)."""
    day = when.date() if isinstance(when, datetime) else when
    if period == PERIOD_DAILY:
        return day.isoformat()
    if period == PERIOD_WEEKLY:
        iso_year, iso_week, _ = day.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if period == PERIOD_MONTHLY:
        return day.strftime("%Y-%m")
    return None


def period_start(period: str, key: str) -> date | None:
    """Return the first day of the period named by ``key``, or None if unparsable."""
    try:
        if period == PERIOD_DAILY:
            return date.fromisoformat(key)
        if period == PERIOD_WEEKLY:
            year, week = key.split("-W")
            return date.fromisocalendar(int(year), int(week), 1)
        if period == PERIOD_MONTHLY:
            return datetime.strptime(key, "%Y-%m").date()
    except ValueError:
        return None
    return None


def relabel_weekly_history(history: Mapping[str, Any]) -> dict[str, float]:
    """Relabel pre-1.2 weekly keys (``%Y-W%U`` of the Monday) to ISO weeks.

    Values are kept; keys that do not parse are kept as they are.
    """
    relabelled: dict[str, float] = {}
    for key, value in history.items():
        try:
            monday = datetime.strptime(f"{key}-1", "%Y-W%U-%w").date()
            new_key = period_key(PERIOD_WEEKLY, monday)
        except ValueError:
            new_key = key
        try:
            relabelled[new_key] = relabelled.get(new_key, 0.0) + float(value)
        except (TypeError, ValueError):
            relabelled[key] = value
    return relabelled


# --------------------------------------------------------------------------
# Unique IDs (must stay stable: existing entities are registered with them)
# --------------------------------------------------------------------------


def energy_unique_id(entry_id: str, scope: str, period: str) -> str:
    """Return the unique_id of an energy sensor (scope: switch entity or 'total')."""
    return f"{DOMAIN}_{entry_id}_{scope}_{PERIOD_SUFFIX[period]}"


def power_unique_id(entry_id: str, scope: str) -> str:
    """Return the unique_id of a power sensor (scope: switch entity or 'total')."""
    return f"{DOMAIN}_{entry_id}_{scope}_{SUFFIX_POWER}"


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------


class SwitchEnergyStore(Store[dict[str, Any]]):
    """Store with migrations for the per-entry history file."""

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict
    ) -> dict[str, Any]:
        """Migrate stored data."""
        data = dict(old_data or {})
        if old_major_version == 1 and old_minor_version < 2:
            for key, history in data.items():
                if key.endswith(f"_{PERIOD_WEEKLY}") and isinstance(history, dict):
                    data[key] = relabel_weekly_history(history)
        return data


def entry_store(hass: HomeAssistant, entry_id: str) -> SwitchEnergyStore:
    """Return the store holding one entry's history."""
    return SwitchEnergyStore(
        hass,
        STORAGE_VERSION,
        f"{STORAGE_KEY}_{entry_id}",
        minor_version=STORAGE_MINOR_VERSION,
    )


# --------------------------------------------------------------------------
# Tracker
# --------------------------------------------------------------------------


@dataclass
class Gang:
    """One switched load (or group of identical loads)."""

    key: str
    entity_id: str
    load_power: float
    quantity: int
    friendly_name: str
    is_on: bool = False
    power: float = 0.0
    brightness_factor: float | None = None
    last_changed: datetime | None = None

    @property
    def number(self) -> int:
        """Return the gang number."""
        return int(self.key)

    @property
    def nominal_power(self) -> float:
        """Return the power with every load on at full power."""
        return self.load_power * self.quantity


@dataclass
class Counter:
    """Energy accumulated for one gang (or the total) over one period."""

    counter_id: str
    period: str
    value: float
    period_key: str | None
    seeded: bool


def friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    """Return a readable name for an entity."""
    fallback = entity_id.split(".")[-1].replace("_", " ").title()
    if (entity_entry := er.async_get(hass).async_get(entity_id)) and entity_entry.name:
        return entity_entry.name
    if state := hass.states.get(entity_id):
        return state.attributes.get("friendly_name", fallback)
    return fallback


class SwitchEnergyTracker:
    """Accrues estimated energy for every gang of a config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise from the (already migrated) entry data."""
        self.hass = hass
        self.entry_id = entry.entry_id
        data = normalize_entry_data(entry.data, entry.title)
        self.name: str = data[CONF_NAME]
        self.brightness_scaling: bool = data[CONF_BRIGHTNESS_SCALING]
        self.gangs: list[Gang] = [
            Gang(
                key=key,
                entity_id=entity_id,
                load_power=data[CONF_GANG_POWER][key],
                quantity=data[CONF_GANG_QUANTITY][key],
                friendly_name=friendly_name(hass, entity_id),
            )
            for key, entity_id in data[CONF_GANG_ENTITIES].items()
        ]
        self.has_total = len(self.gangs) > 1

        self._store = entry_store(hass, entry.entry_id)
        self._counters: dict[str, Counter] = {}
        self._history: dict[str, dict[str, float]] = {}
        self._extra: dict[str, Any] = {}
        self._listeners: list[CALLBACK_TYPE] = []
        self._unsubs: list[CALLBACK_TYPE] = []
        self._stop_unsub: CALLBACK_TYPE | None = None
        self._last_accrual: datetime | None = None

    # -- identifiers -------------------------------------------------------

    @staticmethod
    def counter_id(scope: str, period: str) -> str:
        """Return a counter id; scope is a gang key or 'total'.

        These ids double as the storage keys used since 1.0 (gang_1_daily,
        total_weekly, ...).
        """
        prefix = TOTAL_SCOPE if scope == TOTAL_SCOPE else f"gang_{scope}"
        return f"{prefix}_{period}"

    def _scopes(self) -> list[tuple[str, str]]:
        """Return (counter scope, unique_id scope) pairs."""
        scopes = [(gang.key, gang.entity_id) for gang in self.gangs]
        if self.has_total:
            scopes.append((TOTAL_SCOPE, TOTAL_SCOPE))
        return scopes

    def counter_for_unique_id(self, unique_id: str) -> Counter | None:
        """Return the counter behind an energy sensor's unique_id."""
        for scope, uid_scope in self._scopes():
            for period in ALL_PERIODS:
                if energy_unique_id(self.entry_id, uid_scope, period) == unique_id:
                    return self._counters.get(self.counter_id(scope, period))
        return None

    def expected_unique_ids(self) -> set[str]:
        """Return the unique_ids of every sensor this entry creates."""
        unique_ids = set()
        for _scope, uid_scope in self._scopes():
            unique_ids.add(power_unique_id(self.entry_id, uid_scope))
            for period in ALL_PERIODS:
                unique_ids.add(energy_unique_id(self.entry_id, uid_scope, period))
        return unique_ids

    # -- lifecycle ---------------------------------------------------------

    async def async_load(self) -> None:
        """Load counters and history from storage."""
        stored = await self._store.async_load() or {}
        saved_counters = stored.get("counters", {})
        today = dt_util.now()
        known: set[str] = {"counters"}

        for scope, _uid_scope in self._scopes():
            for period in ALL_PERIODS:
                cid = self.counter_id(scope, period)
                known.add(cid)
                if period != PERIOD_LIFETIME:
                    history = stored.get(cid)
                    self._history[cid] = (
                        dict(history) if isinstance(history, dict) else {}
                    )
                saved = saved_counters.get(cid)
                if isinstance(saved, dict) and "value" in saved:
                    self._counters[cid] = Counter(
                        cid, period, float(saved["value"]), saved.get("period"), True
                    )
                else:
                    # First run with this counter: the sensor seeds it from its
                    # restored state (see async_seed).
                    self._counters[cid] = Counter(
                        cid, period, 0.0, period_key(period, today), False
                    )

        # Keep history of gangs no longer configured: never drop stored data.
        self._extra = {key: value for key, value in stored.items() if key not in known}
        self._rollover(today)

    @callback
    def async_start(self) -> None:
        """Read current states and start tracking."""
        now = dt_util.utcnow()
        self._last_accrual = now
        for gang in self.gangs:
            self._apply_state(gang, self.hass.states.get(gang.entity_id), now)

        self._unsubs.extend(
            [
                async_track_state_change_event(
                    self.hass,
                    [gang.entity_id for gang in self.gangs],
                    self._handle_state_event,
                ),
                async_track_time_interval(
                    self.hass,
                    self._handle_tick,
                    timedelta(seconds=UPDATE_INTERVAL),
                    name=f"{DOMAIN} accrual {self.entry_id}",
                    cancel_on_shutdown=True,
                ),
                # Close the day (and week/month) at local midnight.
                async_track_time_change(
                    self.hass, self._handle_tick, hour=0, minute=0, second=0
                ),
            ]
        )
        self._stop_unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, self._handle_stop
        )
        self._notify()

    async def async_stop(self) -> None:
        """Stop tracking and write everything to storage."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._stop_unsub is not None:
            self._stop_unsub()
            self._stop_unsub = None
        self._accrue(dt_util.utcnow())
        await self._store.async_save(self._data_to_save())

    @callback
    def async_add_listener(self, update: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Register a sensor update callback."""
        self._listeners.append(update)

        def remove() -> None:
            self._listeners.remove(update)

        return remove

    # -- event handlers ----------------------------------------------------

    @callback
    def _handle_state_event(self, event: Event) -> None:
        """Accrue up to now with the old power, then apply the new state."""
        now = dt_util.utcnow()
        self._accrue(now)
        self._rollover(dt_util.as_local(now))
        entity_id = event.data["entity_id"]
        for gang in self.gangs:
            if gang.entity_id == entity_id:
                self._apply_state(gang, event.data.get("new_state"), now)
        self._notify()

    @callback
    def _handle_tick(self, _now: datetime) -> None:
        """Accrue periodically while a load is on, and roll periods over."""
        accrued = self._accrue(dt_util.utcnow())
        rolled = self._rollover(dt_util.now())
        if accrued or rolled:
            self._notify()

    @callback
    def _handle_stop(self, _event: Event) -> None:
        """Accrue on shutdown; the delayed save is flushed on final write."""
        self._stop_unsub = None
        self._accrue(dt_util.utcnow())
        self._schedule_save()

    # -- accounting --------------------------------------------------------

    def _apply_state(self, gang: Gang, state: State | None, now: datetime) -> None:
        """Set a gang's on/off state and effective power."""
        is_on = state is not None and state.state == STATE_ON
        factor: float | None = None
        if (
            is_on
            and self.brightness_scaling
            and gang.entity_id.startswith("light.")
            and isinstance(brightness := state.attributes.get("brightness"), (int, float))
        ):
            factor = max(0.0, min(255.0, float(brightness))) / 255.0
        if is_on != gang.is_on or gang.last_changed is None:
            gang.last_changed = state.last_changed if state is not None else now
        gang.is_on = is_on
        gang.brightness_factor = factor
        gang.power = gang.nominal_power * (1.0 if factor is None else factor) if is_on else 0.0

    def _accrue(self, now: datetime) -> bool:
        """Add the energy used since the last accrual. Return True if any."""
        if self._last_accrual is None:
            self._last_accrual = now
            return False
        hours = (now - self._last_accrual).total_seconds() / 3600
        self._last_accrual = now
        if hours <= 0:
            return False

        total = 0.0
        for gang in self.gangs:
            if gang.power <= 0:
                continue
            energy = gang.power * hours
            total += energy
            for period in ALL_PERIODS:
                self._add(self.counter_id(gang.key, period), energy)
        if total <= 0:
            return False
        if self.has_total:
            for period in ALL_PERIODS:
                self._add(self.counter_id(TOTAL_SCOPE, period), total)
        self._schedule_save()
        return True

    def _add(self, cid: str, energy: float) -> None:
        counter = self._counters[cid]
        counter.value += energy
        if counter.period_key is not None:
            self._history[cid][counter.period_key] = counter.value

    def _rollover(self, now_local: datetime) -> bool:
        """Start a new period on counters whose period has ended."""
        rolled = False
        for counter in self._counters.values():
            if counter.period not in RESET_PERIODS:
                continue
            current = period_key(counter.period, now_local)
            if counter.period_key == current:
                continue
            history = self._history[counter.counter_id]
            if counter.period_key is not None and counter.value > 0:
                history[counter.period_key] = counter.value
            _LOGGER.debug(
                "%s %s: closing %s at %.3f Wh, starting %s",
                self.name,
                counter.counter_id,
                counter.period_key,
                counter.value,
                current,
            )
            # Normally 0; a value set_energy stored ahead for this period is kept.
            counter.value = float(history.get(current, 0.0))
            counter.period_key = current
            counter.seeded = True  # a restored value belongs to the old period
            for key in sorted(history)[: -HISTORY_LIMITS[counter.period]]:
                del history[key]
            rolled = True
        if rolled:
            self._schedule_save()
        return rolled

    @callback
    def async_seed(self, cid: str, value: float, last_updated: datetime) -> None:
        """Seed a counter with a sensor's restored state on its first run."""
        counter = self._counters[cid]
        if counter.seeded:
            return
        counter.seeded = True
        if counter.period_key is None or counter.period_key == period_key(
            counter.period, dt_util.as_local(last_updated)
        ):
            counter.value += value  # else it belongs to a period that has ended
        if counter.period_key is not None:
            # The sensor's state wins over pre-1.2 history for the current period.
            self._history[cid][counter.period_key] = counter.value
        self._schedule_save()

    # -- service operations -------------------------------------------------

    @callback
    def async_reset(self, counter: Counter) -> None:
        """Reset a counter's current period to zero."""
        self._accrue(dt_util.utcnow())
        counter.value = 0.0
        if counter.period_key is not None:
            self._history[counter.counter_id][counter.period_key] = 0.0
        self._schedule_save()
        self._notify()

    @callback
    def async_set(self, counter: Counter, energy: float, day: date | None) -> str | None:
        """Set the energy of the period containing ``day`` (default: current)."""
        self._accrue(dt_util.utcnow())
        if counter.period_key is None:
            counter.value = energy
            key = None
        else:
            key = period_key(counter.period, day) if day else counter.period_key
            self._history[counter.counter_id][key] = energy
            if key == counter.period_key:
                counter.value = energy
        self._schedule_save()
        self._notify()
        return key

    def history(self, counter: Counter) -> dict[str, float]:
        """Return a counter's history, oldest first."""
        history = self._history.get(counter.counter_id, {})
        return {key: history[key] for key in sorted(history)}

    # -- persistence ---------------------------------------------------------

    def _data_to_save(self) -> dict[str, Any]:
        data: dict[str, Any] = dict(self._extra)
        data.update(self._history)
        data["counters"] = {
            cid: {"value": counter.value, "period": counter.period_key}
            for cid, counter in self._counters.items()
        }
        return data

    def _schedule_save(self) -> None:
        self._store.async_delay_save(self._data_to_save, SAVE_DELAY)

    @callback
    def _notify(self) -> None:
        for update in list(self._listeners):
            update()

    # -- read access for sensors -------------------------------------------

    def counter(self, scope: str, period: str) -> Counter:
        """Return a counter."""
        return self._counters[self.counter_id(scope, period)]

    def sibling(self, counter: Counter, period: str) -> Counter:
        """Return the counter of the same gang (or total) for another period."""
        scope_prefix = counter.counter_id.rsplit("_", 1)[0]
        return self._counters[f"{scope_prefix}_{period}"]

    def yesterday(self, counter: Counter) -> float | None:
        """Return the energy of the previous day (daily counters only)."""
        if counter.period != PERIOD_DAILY:
            return None
        key = period_key(PERIOD_DAILY, dt_util.now() - timedelta(days=1))
        return self._history.get(counter.counter_id, {}).get(key)

    @property
    def total_power(self) -> float:
        """Return the summed power of all gangs."""
        return sum(gang.power for gang in self.gangs)
