"""Services for Switch Energy Statistics."""

from __future__ import annotations

import logging
from datetime import datetime

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Service names
SERVICE_RESET_ENERGY = "reset_energy"
SERVICE_SET_ENERGY = "set_energy"
SERVICE_EXPORT_DATA = "export_data"

# Service schemas
RESET_ENERGY_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("period", default="daily"): vol.In(["daily", "weekly", "monthly"]),
    }
)

SET_ENERGY_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("energy"): vol.Coerce(float),
        vol.Optional("date"): cv.date,
    }
)

EXPORT_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("start_date"): cv.date,
        vol.Optional("end_date"): cv.date,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Switch Energy Statistics."""

    @callback
    async def reset_energy_service(call: ServiceCall) -> None:
        """Reset energy data for a sensor."""
        entity_id = call.data["entity_id"]
        period = call.data["period"]

        # Find the entity
        entity = hass.data.get("entity_registry", {}).get(entity_id)
        if not entity:
            _LOGGER.error("Entity %s not found", entity_id)
            return

        # Reset the energy value
        state = hass.states.get(entity_id)
        if state and hasattr(state, "entity"):
            if hasattr(state.entity, "_energy_value"):
                state.entity._energy_value = 0.0
                state.entity.async_write_ha_state()
                _LOGGER.info("Reset energy for %s (%s period)", entity_id, period)

    @callback
    async def set_energy_service(call: ServiceCall) -> None:
        """Set energy value for a specific date."""
        entity_id = call.data["entity_id"]
        energy = call.data["energy"]
        date = call.data.get("date", dt_util.utcnow().date())

        # Find the entity
        entity = hass.data.get("entity_registry", {}).get(entity_id)
        if not entity:
            _LOGGER.error("Entity %s not found", entity_id)
            return

        # Set energy value
        state = hass.states.get(entity_id)
        if state and hasattr(state, "entity"):
            if hasattr(state.entity, "_historical_data"):
                date_key = date.strftime("%Y-%m-%d")
                state.entity._historical_data[date_key] = energy
                await state.entity._save_historical_data()
                _LOGGER.info(
                    "Set energy for %s on %s to %s Wh", entity_id, date, energy
                )

    @callback
    async def export_data_service(call: ServiceCall) -> None:
        """Export historical energy data."""
        entity_id = call.data["entity_id"]
        start_date = call.data.get("start_date")
        end_date = call.data.get("end_date")

        # Find the entity
        entity = hass.data.get("entity_registry", {}).get(entity_id)
        if not entity:
            _LOGGER.error("Entity %s not found", entity_id)
            return

        # Export data
        state = hass.states.get(entity_id)
        if state and hasattr(state, "entity"):
            if hasattr(state.entity, "_historical_data"):
                data = state.entity._historical_data

                # Filter by date range if specified
                if start_date or end_date:
                    filtered_data = {}
                    for date_key, value in data.items():
                        try:
                            date_obj = datetime.strptime(date_key, "%Y-%m-%d").date()
                            if start_date and date_obj < start_date:
                                continue
                            if end_date and date_obj > end_date:
                                continue
                            filtered_data[date_key] = value
                        except ValueError:
                            # Handle weekly/monthly keys differently
                            filtered_data[date_key] = value
                    data = filtered_data

                # Fire event with data
                hass.bus.async_fire(
                    f"{DOMAIN}_data_export",
                    {
                        "entity_id": entity_id,
                        "data": data,
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None,
                    },
                )
                _LOGGER.info("Exported data for %s", entity_id)

    # Register services
    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_RESET_ENERGY,
        reset_energy_service,
        schema=RESET_ENERGY_SCHEMA,
    )

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SET_ENERGY,
        set_energy_service,
        schema=SET_ENERGY_SCHEMA,
    )

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_EXPORT_DATA,
        export_data_service,
        schema=EXPORT_DATA_SCHEMA,
    )
