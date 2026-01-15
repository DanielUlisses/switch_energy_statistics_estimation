"""Config flow for Switch Energy Statistics."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    CONF_GANG_COUNT,
    CONF_GANG_POWER,
    CONF_NAME,
    DEFAULT_GANG_POWER,
    DEFAULT_NAME,
    DOMAIN,
    MAX_GANG_COUNT,
    MIN_GANG_COUNT,
)

_LOGGER = logging.getLogger(__name__)


async def get_switch_entities(hass: HomeAssistant) -> list[str]:
    """Get all available switch entities."""
    switch_entities = []

    # Get entities from states (includes all active entities)
    for state in hass.states.async_all():
        entity_id = state.entity_id
        if entity_id.startswith(("switch.", "light.")):
            # Exclude certain entity types that aren't real switches
            if not any(
                exclude in entity_id
                for exclude in [
                    "_linkquality",
                    "_update_available",
                    "_update_state",
                    "_battery",
                    "_signal_strength",
                    "_voltage",
                    "_power",
                    "_energy",
                    "_current",
                    "_temperature",
                    "_humidity",
                ]
            ):
                switch_entities.append(entity_id)

    # Also get from entity registry for disabled entities
    entity_registry = async_get_entity_registry(hass)
    for entity in entity_registry.entities.values():
        if (
            entity.domain in ("switch", "light")
            and entity.entity_id not in switch_entities
            and not any(
                exclude in entity.entity_id
                for exclude in [
                    "_linkquality",
                    "_update_available",
                    "_update_state",
                    "_battery",
                    "_signal_strength",
                    "_voltage",
                    "_power",
                    "_energy",
                    "_current",
                    "_temperature",
                    "_humidity",
                ]
            )
        ):
            switch_entities.append(entity.entity_id)

    return sorted(switch_entities)


class SwitchEnergyStatisticsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Switch Energy Statistics."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._gang_count = None
        self._name = None
        self._gang_entities = {}
        self._gang_powers = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            gang_count = int(user_input[CONF_GANG_COUNT])
            name = user_input[CONF_NAME]

            # Store data for next step
            self._gang_count = gang_count
            self._name = name

            # Move to gang entity selection step
            return await self.async_step_gang_entities()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_GANG_COUNT, default=1): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_GANG_COUNT,
                        max=MAX_GANG_COUNT,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_gang_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle gang entity selection."""
        errors = {}

        if user_input is not None:
            # Validate all selected entities exist
            available_entities = await get_switch_entities(self.hass)
            current_states = [
                state.entity_id
                for state in self.hass.states.async_all()
                if state.entity_id.startswith(("switch.", "light."))
            ]
            all_entities = list(set(available_entities + current_states))

            gang_entities = {}
            for gang in range(1, self._gang_count + 1):
                entity_key = f"gang_{gang}_entity"
                selected_entity = user_input.get(entity_key)

                if not selected_entity:
                    errors[entity_key] = "required"
                elif selected_entity not in all_entities:
                    errors[entity_key] = "invalid_switch_entity"
                else:
                    gang_entities[gang] = selected_entity

            if not errors:
                # Store gang entities for next step
                self._gang_entities = gang_entities
                # Move to power configuration step
                return await self.async_step_gang_config()

        # Get available switch entities
        switch_entities = await get_switch_entities(self.hass)

        if not switch_entities:
            return self.async_abort(reason="no_switch_entities")

        # Create schema for gang entity selection
        gang_schema = {}
        for gang in range(1, self._gang_count + 1):
            entity_key = f"gang_{gang}_entity"
            gang_schema[vol.Required(entity_key)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=switch_entities,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )

        data_schema = vol.Schema(gang_schema)

        return self.async_show_form(
            step_id="gang_entities",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "gang_count": str(self._gang_count),
            },
        )

    async def async_step_gang_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle gang power configuration."""
        errors = {}

        if user_input is not None:
            # Store gang power configurations
            self._gang_powers = {}
            for gang in range(1, self._gang_count + 1):
                power_key = f"gang_{gang}_power"
                self._gang_powers[gang] = user_input.get(power_key, DEFAULT_GANG_POWER)

            # Create the entry
            return self.async_create_entry(
                title=self._name,
                data={
                    CONF_GANG_COUNT: self._gang_count,
                    CONF_NAME: self._name,
                    CONF_GANG_POWER: self._gang_powers,
                    "gang_entities": self._gang_entities,
                    # Store individual gang entities
                },
            )

        # Create schema for gang power configuration
        gang_schema = {}
        for gang in range(1, self._gang_count + 1):
            power_key = f"gang_{gang}_power"
            gang_schema[vol.Required(power_key, default=DEFAULT_GANG_POWER)] = (
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=1000.0,
                        step=0.1,
                        unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )
            )

        data_schema = vol.Schema(gang_schema)

        return self.async_show_form(
            step_id="gang_config",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "gang_count": str(self._gang_count),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return SwitchEnergyStatisticsOptionsFlow(config_entry)


class SwitchEnergyStatisticsOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Switch Energy Statistics."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update gang power values
            updated_gang_powers = {}
            gang_count = int(self._config_entry.data[CONF_GANG_COUNT])

            for gang in range(1, gang_count + 1):
                power_key = f"gang_{gang}_power"
                if power_key in user_input:
                    updated_gang_powers[gang] = user_input[power_key]

            # Update the config entry data
            new_data = dict(self._config_entry.data)
            new_data[CONF_GANG_POWER] = updated_gang_powers

            self.hass.config_entries.async_update_entry(
                self._config_entry, data=new_data
            )

            return self.async_create_entry(title="", data={})

        gang_count = int(self._config_entry.data[CONF_GANG_COUNT])
        current_gang_powers = self._config_entry.data.get(CONF_GANG_POWER, {})
        gang_entities = self._config_entry.data.get("gang_entities", {})

        # Create schema for gang power configuration with entity names
        gang_schema = {}
        for gang in range(1, gang_count + 1):
            power_key = f"gang_{gang}_power"
            current_power = current_gang_powers.get(gang, DEFAULT_GANG_POWER)

            gang_schema[vol.Required(power_key, default=current_power)] = (
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=1000.0,
                        step=0.1,
                        unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(gang_schema),
            description_placeholders={
                "gang_entities": ", ".join(
                    f"Gang {gang}: {self._get_entity_friendly_name(entity_id)}"
                    for gang, entity_id in gang_entities.items()
                ),
            },
        )

    def _get_entity_friendly_name(self, entity_id: str) -> str:
        """Get friendly name for an entity."""
        if not entity_id or entity_id.startswith("gang_"):
            return entity_id

        # Try to get from entity registry first
        entity_registry = async_get_entity_registry(self.hass)
        if entity_entry := entity_registry.async_get(entity_id):
            if entity_entry.name:
                return entity_entry.name

        # Fall back to state friendly name
        if state := self.hass.states.get(entity_id):
            return state.attributes.get(
                "friendly_name", entity_id.split(".")[-1].replace("_", " ").title()
            )

        # Final fallback
        return entity_id.split(".")[-1].replace("_", " ").title()
