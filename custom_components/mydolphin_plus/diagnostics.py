"""Diagnostics support for Tuya."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er

from . import get_ha
from .component.managers.home_assistant import MyDolphinPlusHomeAssistantManager
from .configuration.helpers.const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Starting diagnostic tool")

    manager = get_ha(hass, entry.entry_id)

    return _async_get_diagnostics(hass, manager)


@callback
def _async_get_diagnostics(
    hass: HomeAssistant,
    manager: MyDolphinPlusHomeAssistantManager,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Getting diagnostic information")

    api_data = manager.api.data
    ws_data = manager.ws.data
    config_data = manager.config_data.to_dict()

    data = {}

    for api_data_key in api_data:
        data[api_data_key] = api_data[api_data_key]

    for ws_data_key in ws_data:
        data[ws_data_key] = ws_data[ws_data_key]

    for config_data_key in config_data:
        data[config_data_key] = config_data[config_data_key]

    if CONF_PASSWORD in data:
        data.pop(CONF_PASSWORD)

    result = _async_device_as_dict(hass, data, manager)

    return result


@callback
def _async_device_as_dict(
    hass: HomeAssistant, data: dict, manager: MyDolphinPlusHomeAssistantManager
) -> dict[str, Any]:
    """Represent a Shinobi monitor as a dictionary."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    ha_device = device_registry.async_get_device(
        identifiers={(DOMAIN, manager.robot_name)}
    )

    result = {"debug": data}

    if ha_device:
        result["home_assistant"] = {
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

    return result
