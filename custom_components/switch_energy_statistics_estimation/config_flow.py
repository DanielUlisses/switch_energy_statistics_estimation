"""Config flow for Switch Energy Statistics."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BRIGHTNESS_SCALING,
    CONF_ENTITIES,
    CONF_GANG_COUNT,
    CONF_GANG_ENTITIES,
    CONF_GANG_POWER,
    CONF_GANG_QUANTITY,
    CONF_NAME,
    CONFIG_MINOR_VERSION,
    CONFIG_VERSION,
    DEFAULT_GANG_POWER,
    DEFAULT_GANG_QUANTITY,
    DOMAIN,
    MAX_GANG_COUNT,
    MAX_GANG_POWER,
    MAX_GANG_QUANTITY,
    MIN_GANG_POWER,
    SUPPORTED_DOMAINS,
)
from .tracker import friendly_name, normalize_entry_data

_LOGGER = logging.getLogger(__name__)

POWER_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=MIN_GANG_POWER,
        max=MAX_GANG_POWER,
        step=0.1,
        unit_of_measurement="W",
        mode=selector.NumberSelectorMode.BOX,
    )
)
QUANTITY_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=1, max=MAX_GANG_QUANTITY, step=1, mode=selector.NumberSelectorMode.BOX
    )
)
ENTITIES_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        filter=selector.EntityFilterSelectorConfig(domain=SUPPORTED_DOMAINS),
        multiple=True,
        reorder=True,
    )
)


def _load_schema(
    gangs: dict[str, str],
    powers: dict[str, float],
    quantities: dict[str, int],
    brightness_scaling: bool,
) -> vol.Schema:
    """Return the watts / load count form for the given gangs."""
    schema: dict[Any, Any] = {}
    for gang in gangs:
        schema[
            vol.Required(
                f"gang_{gang}_power", default=powers.get(gang, DEFAULT_GANG_POWER)
            )
        ] = POWER_SELECTOR
        schema[
            vol.Required(
                f"gang_{gang}_quantity",
                default=quantities.get(gang, DEFAULT_GANG_QUANTITY),
            )
        ] = QUANTITY_SELECTOR
    schema[vol.Required(CONF_BRIGHTNESS_SCALING, default=brightness_scaling)] = (
        selector.BooleanSelector()
    )
    return vol.Schema(schema)


def _read_loads(
    gangs: dict[str, str], user_input: dict[str, Any]
) -> tuple[dict[str, float], dict[str, int]]:
    """Read watts and load counts from the load form."""
    powers = {
        gang: float(user_input.get(f"gang_{gang}_power", DEFAULT_GANG_POWER))
        for gang in gangs
    }
    quantities = {
        gang: int(user_input.get(f"gang_{gang}_quantity", DEFAULT_GANG_QUANTITY))
        for gang in gangs
    }
    return powers, quantities


class SwitchEnergyStatisticsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Switch Energy Statistics."""

    VERSION = CONFIG_VERSION
    MINOR_VERSION = CONFIG_MINOR_VERSION

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._name: str = ""
        self._gangs: dict[str, str] = {}
        self._powers: dict[str, float] = {}
        self._quantities: dict[str, int] = {}
        self._brightness_scaling = False

    # -- helpers -------------------------------------------------------------

    def _validate_entities(
        self, entities: list[str], exclude_entry_id: str | None = None
    ) -> str | None:
        """Return an error key, or None if the selection is valid."""
        if not entities:
            return "no_entities"
        if len(entities) > MAX_GANG_COUNT:
            return "too_many_entities"
        if len(set(entities)) != len(entities):
            return "duplicate_entity"
        if any(entity.split(".")[0] not in SUPPORTED_DOMAINS for entity in entities):
            return "invalid_switch_entity"
        for entry in self._async_current_entries(include_ignore=False):
            if entry.entry_id == exclude_entry_id:
                continue
            attached = normalize_entry_data(entry.data, entry.title)[CONF_GANG_ENTITIES]
            if set(entities) & set(attached.values()):
                return "entity_already_configured"
        return None

    def _entry_data(self) -> dict[str, Any]:
        return {
            CONF_NAME: self._name,
            CONF_GANG_COUNT: len(self._gangs),
            CONF_GANG_ENTITIES: self._gangs,
            CONF_GANG_POWER: self._powers,
            CONF_GANG_QUANTITY: self._quantities,
            CONF_BRIGHTNESS_SCALING: self._brightness_scaling,
        }

    def _gangs_description(self) -> str:
        return "\n".join(
            f"Gang {gang}: {friendly_name(self.hass, entity_id)} ({entity_id})"
            for gang, entity_id in self._gangs.items()
        )

    # -- steps ---------------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Pick the name and the switched entities (one per gang, in order)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            entities = list(user_input.get(CONF_ENTITIES, []))
            if error := self._validate_entities(entities):
                errors[CONF_ENTITIES] = error
            else:
                self._gangs = {str(i): entity for i, entity in enumerate(entities, 1)}
                self._name = (user_input.get(CONF_NAME) or "").strip() or friendly_name(
                    self.hass, entities[0]
                )
                return await self.async_step_gang_config()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME): selector.TextSelector(),
                    vol.Required(CONF_ENTITIES): ENTITIES_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_gang_config(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Set watts per load and number of loads for each gang."""
        if user_input is not None:
            self._powers, self._quantities = _read_loads(self._gangs, user_input)
            self._brightness_scaling = bool(user_input.get(CONF_BRIGHTNESS_SCALING))
            if self.source == config_entries.SOURCE_RECONFIGURE:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    title=self._name,
                    data=self._entry_data(),
                )
            return self.async_create_entry(title=self._name, data=self._entry_data())

        return self.async_show_form(
            step_id="gang_config",
            data_schema=_load_schema(
                self._gangs, self._powers, self._quantities, self._brightness_scaling
            ),
            description_placeholders={"gangs": self._gangs_description()},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Change the name or add, replace or remove gangs."""
        entry = self._get_reconfigure_entry()
        current = normalize_entry_data(entry.data, entry.title)
        errors: dict[str, str] = {}

        if user_input is not None:
            entities = list(user_input.get(CONF_ENTITIES, []))
            if error := self._validate_entities(entities, entry.entry_id):
                errors[CONF_ENTITIES] = error
            else:
                # Kept entities keep their gang number (and so their history);
                # new ones take a number no current gang uses, so they never
                # inherit a removed gang's watts or history.
                by_entity = {e: g for g, e in current[CONF_GANG_ENTITIES].items()}
                gangs = {by_entity[e]: e for e in entities if e in by_entity}
                free = (
                    str(n)
                    for n in range(1, MAX_GANG_COUNT * 2 + 1)
                    if str(n) not in current[CONF_GANG_ENTITIES]
                )
                for entity in entities:
                    if entity not in by_entity:
                        gangs[next(free)] = entity
                self._gangs = dict(sorted(gangs.items(), key=lambda item: int(item[0])))
                self._name = (user_input.get(CONF_NAME) or "").strip() or current[
                    CONF_NAME
                ]
                self._powers = {
                    g: current[CONF_GANG_POWER].get(g, DEFAULT_GANG_POWER)
                    for g in self._gangs
                    if g in current[CONF_GANG_ENTITIES]
                }
                self._quantities = {
                    g: current[CONF_GANG_QUANTITY].get(g, DEFAULT_GANG_QUANTITY)
                    for g in self._gangs
                    if g in current[CONF_GANG_ENTITIES]
                }
                self._brightness_scaling = current[CONF_BRIGHTNESS_SCALING]
                return await self.async_step_gang_config()

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME, default=current[CONF_NAME]
                    ): selector.TextSelector(),
                    vol.Required(
                        CONF_ENTITIES,
                        default=list(current[CONF_GANG_ENTITIES].values()),
                    ): ENTITIES_SELECTOR,
                }
            ),
            errors=errors,
        )

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Create an entry from the attach service."""
        entities = list(import_data[CONF_ENTITIES])
        if error := self._validate_entities(entities):
            return self.async_abort(reason=error)
        self._gangs = {str(i): entity for i, entity in enumerate(entities, 1)}
        self._name = import_data.get(CONF_NAME) or friendly_name(self.hass, entities[0])
        self._powers = dict.fromkeys(self._gangs, float(import_data[CONF_GANG_POWER]))
        self._quantities = dict.fromkeys(
            self._gangs, int(import_data.get(CONF_GANG_QUANTITY, DEFAULT_GANG_QUANTITY))
        )
        self._brightness_scaling = bool(import_data.get(CONF_BRIGHTNESS_SCALING, False))
        return self.async_create_entry(title=self._name, data=self._entry_data())

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SwitchEnergyStatisticsOptionsFlow:
        """Create the options flow."""
        return SwitchEnergyStatisticsOptionsFlow()


class SwitchEnergyStatisticsOptionsFlow(config_entries.OptionsFlow):
    """Change watts, load counts and brightness scaling."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        entry = self.config_entry
        current = normalize_entry_data(entry.data, entry.title)
        gangs = current[CONF_GANG_ENTITIES]

        if user_input is not None:
            powers, quantities = _read_loads(gangs, user_input)
            new_data = {
                **current,
                CONF_GANG_POWER: powers,
                CONF_GANG_QUANTITY: quantities,
                CONF_BRIGHTNESS_SCALING: bool(user_input.get(CONF_BRIGHTNESS_SCALING)),
            }
            # The settings live in entry.data (read by the sensors), so reload
            # explicitly: OptionsFlowWithReload only reloads on options changes.
            if self.hass.config_entries.async_update_entry(entry, data=new_data):
                self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="init",
            data_schema=_load_schema(
                gangs,
                current[CONF_GANG_POWER],
                current[CONF_GANG_QUANTITY],
                current[CONF_BRIGHTNESS_SCALING],
            ),
            description_placeholders={
                "gangs": "\n".join(
                    f"Gang {gang}: {friendly_name(self.hass, entity_id)} ({entity_id})"
                    for gang, entity_id in gangs.items()
                )
            },
        )
