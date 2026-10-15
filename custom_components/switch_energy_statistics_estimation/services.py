"""Services for Switch Energy Statistics."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.service import async_register_admin_service

from .const import (
    ALL_PERIODS,
    CONF_BRIGHTNESS_SCALING,
    CONF_ENTITIES,
    CONF_GANG_POWER,
    CONF_GANG_QUANTITY,
    CONF_NAME,
    DEFAULT_GANG_QUANTITY,
    DOMAIN,
    MAX_GANG_POWER,
    MAX_GANG_QUANTITY,
    MIN_GANG_POWER,
    NAME,
)
from .tracker import Counter, SwitchEnergyTracker, period_start

_LOGGER = logging.getLogger(__name__)

# Service names
SERVICE_RESET_ENERGY = "reset_energy"
SERVICE_SET_ENERGY = "set_energy"
SERVICE_EXPORT_DATA = "export_data"
SERVICE_ATTACH = "attach"

# Service schemas
RESET_ENERGY_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("period"): vol.In(ALL_PERIODS),
    }
)

SET_ENERGY_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("energy"): vol.All(vol.Coerce(float), vol.Range(min=0)),
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

ATTACH_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_ids,
        vol.Required("power"): vol.All(
            vol.Coerce(float), vol.Range(min=MIN_GANG_POWER, max=MAX_GANG_POWER)
        ),
        vol.Optional("quantity", default=DEFAULT_GANG_QUANTITY): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=MAX_GANG_QUANTITY)
        ),
        vol.Optional("name"): cv.string,
        vol.Optional("brightness_scaling", default=False): cv.boolean,
    }
)


def _resolve(
    hass: HomeAssistant, entity_id: str
) -> tuple[SwitchEnergyTracker, Counter]:
    """Return the tracker and counter behind one of this integration's energy sensors."""
    reg_entry = er.async_get(hass).async_get(entity_id)
    if (
        reg_entry is None
        or reg_entry.platform != DOMAIN
        or not reg_entry.config_entry_id
    ):
        raise ServiceValidationError(f"{entity_id} is not a {NAME} sensor")
    entry = hass.config_entries.async_get_entry(reg_entry.config_entry_id)
    if entry is None or entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(f"The entry of {entity_id} is not loaded")
    tracker: SwitchEnergyTracker = entry.runtime_data
    counter = tracker.counter_for_unique_id(reg_entry.unique_id)
    if counter is None:
        raise ServiceValidationError(f"{entity_id} is not an energy sensor of {NAME}")
    return tracker, counter


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Switch Energy Statistics."""

    async def reset_energy_service(call: ServiceCall) -> None:
        """Reset the current period of a sensor (or of a sibling period)."""
        tracker, counter = _resolve(hass, call.data["entity_id"])
        if period := call.data.get("period"):
            counter = tracker.sibling(counter, period)
        tracker.async_reset(counter)
        _LOGGER.info("Reset %s (%s)", call.data["entity_id"], counter.counter_id)

    async def set_energy_service(call: ServiceCall) -> None:
        """Set the energy of the period containing a date."""
        tracker, counter = _resolve(hass, call.data["entity_id"])
        key = tracker.async_set(counter, call.data["energy"], call.data.get("date"))
        _LOGGER.info(
            "Set %s %s to %s Wh",
            call.data["entity_id"],
            key or "lifetime",
            call.data["energy"],
        )

    async def export_data_service(call: ServiceCall) -> ServiceResponse:
        """Export a sensor's history as an event and a response."""
        entity_id = call.data["entity_id"]
        start_date = call.data.get("start_date")
        end_date = call.data.get("end_date")
        tracker, counter = _resolve(hass, entity_id)

        data = {}
        for key, value in tracker.history(counter).items():
            start = period_start(counter.period, key)
            if start is not None and (
                (start_date and start < start_date) or (end_date and start > end_date)
            ):
                continue
            data[key] = round(value, 3)

        payload = {
            "entity_id": entity_id,
            "period": counter.period,
            "data": data,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
        hass.bus.async_fire(f"{DOMAIN}_data_export", payload)
        return payload

    async def attach_service(call: ServiceCall) -> ServiceResponse:
        """Create an entry for one or more switched entities."""
        import_data = {
            CONF_ENTITIES: call.data["entity_id"],
            CONF_GANG_POWER: call.data["power"],
            CONF_GANG_QUANTITY: call.data["quantity"],
            CONF_BRIGHTNESS_SCALING: call.data["brightness_scaling"],
        }
        if name := call.data.get("name"):
            import_data[CONF_NAME] = name
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=import_data
        )
        if result["type"] is not FlowResultType.CREATE_ENTRY:
            raise ServiceValidationError(
                f"Could not attach {', '.join(call.data['entity_id'])}: "
                f"{result.get('reason', result['type'])}"
            )
        entry = result["result"]
        return {"entry_id": entry.entry_id, "title": entry.title}

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_RESET_ENERGY,
        reset_energy_service,
        schema=RESET_ENERGY_SCHEMA,
    )
    async_register_admin_service(
        hass, DOMAIN, SERVICE_SET_ENERGY, set_energy_service, schema=SET_ENERGY_SCHEMA
    )
    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_EXPORT_DATA,
        export_data_service,
        schema=EXPORT_DATA_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_ATTACH,
        attach_service,
        schema=ATTACH_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
