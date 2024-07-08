"""Diagnostics support for MyDolphin."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .common.consts import DOMAIN, TO_REDACT
from .managers.coordinator import MyDolphinPlusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Starting diagnostic tool")

    coordinator = hass.data[DOMAIN][entry.entry_id]

    return _async_get_diagnostics(hass, coordinator, entry)


@callback
def _async_get_diagnostics(
    hass: HomeAssistant, coordinator: MyDolphinPlusCoordinator, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Getting diagnostic information")

    device_data = coordinator.get_device()
    identifiers = device_data.get("identifiers")
    debug_data = coordinator.get_device_debug_data()

    data = async_redact_data(debug_data, TO_REDACT)

    data["disabled_by"] = entry.disabled_by
    data["disabled_polling"] = entry.pref_disable_polling

    _LOGGER.debug("Getting diagnostic information for all devices")

    data.update(device=_async_device_as_dict(hass, identifiers))

    return data


@callback
def _async_device_as_dict(hass: HomeAssistant, identifiers) -> dict[str, Any]:
    """Represent a Shinobi monitor as a dictionary."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    ha_device = device_registry.async_get_device(identifiers=identifiers)
    data = {}

    if ha_device:
        data["home_assistant"] = {
            "name": ha_device.name,
            "name_by_user": ha_device.name_by_user,
            "disabled": ha_device.disabled,
            "disabled_by": ha_device.disabled_by,
            "entities": [],
        }

        ha_entities = er.async_entries_for_device(
            entity_registry,
            device_id=ha_device.id,
            include_disabled_entities=True,
        )

        for entity_entry in ha_entities:
            state = hass.states.get(entity_entry.entity_id)
            state_dict = None
            if state:
                state_dict = dict(state.as_dict())

                # The context doesn't provide useful information in this case.
                state_dict.pop("context", None)

            data["home_assistant"]["entities"].append(
                {
                    "disabled": entity_entry.disabled,
                    "disabled_by": entity_entry.disabled_by,
                    "entity_category": entity_entry.entity_category,
                    "device_class": entity_entry.device_class,
                    "original_device_class": entity_entry.original_device_class,
                    "icon": entity_entry.icon,
                    "original_icon": entity_entry.original_icon,
                    "unit_of_measurement": entity_entry.unit_of_measurement,
                    "state": state_dict,
                }
            )

    return data
