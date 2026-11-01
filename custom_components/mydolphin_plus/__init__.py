"""
This component provides support for MyDolphin Plus.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/mydolphin_plus/
"""

import logging
import sys

from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_UNIT_OF_MEASUREMENT,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_START,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from .common.clean_modes import LEGACY_CYCLE_TIME_KEYS
from .common.consts import (
    DATA_KEY_CYCLE_TIME,
    DATA_KEY_CYCLE_TIME_LEFT,
    DEFAULT_NAME,
    DOMAIN,
    INITIAL_TOKENS_KEY,
    PLATFORMS,
    STORAGE_DATA_ID_TOKEN,
    STORAGE_DATA_ID_TOKEN_EXPIRES_AT,
    STORAGE_DATA_MOTOR_UNIT_SERIAL,
    STORAGE_DATA_REFRESH_TOKEN,
    STORAGE_DATA_SERIAL_NUMBER,
)
from .managers.config_manager import ConfigManager
from .managers.coordinator import MyDolphinPlusCoordinator
from .models.exceptions import LoginError

_LOGGER = logging.getLogger(__name__)

# Units for sensors that older versions created without a suggested unit
SUGGESTED_TIME_UNITS = {
    slugify(DATA_KEY_CYCLE_TIME_LEFT): UnitOfTime.HOURS,
}


async def async_setup(_hass, _config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a MyDolphin Plus config entry."""
    initialized = False

    try:
        entry_config = dict(entry.data)
        initial_tokens = entry_config.pop(INITIAL_TOKENS_KEY, None)

        config_manager = ConfigManager(hass, entry)
        await config_manager.initialize(entry_config)

        if initial_tokens is not None:
            await config_manager.update_tokens(
                initial_tokens.get(STORAGE_DATA_ID_TOKEN),
                initial_tokens.get(STORAGE_DATA_REFRESH_TOKEN),
                initial_tokens.get(STORAGE_DATA_ID_TOKEN_EXPIRES_AT),
            )
            serial = initial_tokens.get(STORAGE_DATA_SERIAL_NUMBER)
            if serial:
                await config_manager.update_serial_number(serial)
            motor_unit_serial = initial_tokens.get(STORAGE_DATA_MOTOR_UNIT_SERIAL)
            if motor_unit_serial:
                await config_manager.update_motor_unit_serial(motor_unit_serial)

            hass.config_entries.async_update_entry(
                entry,
                data={CONF_USERNAME: entry_config.get(CONF_USERNAME)},
            )

        is_initialized = config_manager.is_initialized

        if is_initialized:
            _remove_old_cycle_time_entities(hass, entry)
            _set_suggested_time_units(hass, entry)

            coordinator = MyDolphinPlusCoordinator(hass, config_manager)

            hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

            if hass.is_running:
                await coordinator.initialize()
            else:
                hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_START, coordinator.on_home_assistant_start
                )

            _LOGGER.info("Finished loading integration")

        initialized = is_initialized

    except LoginError:
        _LOGGER.info(f"Failed to login {DEFAULT_NAME} API, cannot log integration")

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(
            f"Failed to load {DEFAULT_NAME}, error: {ex}, line: {line_number}"
        )

    return initialized


def _remove_old_cycle_time_entities(hass: HomeAssistant, entry: ConfigEntry):
    """
    Remove the Cycle Time sensor and the cycle time numbers for each mode.

    The Cycle Time number replaces them.
    """
    entity_registry = er.async_get(hass)
    cycle_time_key = slugify(DATA_KEY_CYCLE_TIME)

    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        is_old_sensor = (
            entity.domain == SENSOR_DOMAIN and entity.translation_key == cycle_time_key
        )
        is_old_preset = (
            entity.domain == NUMBER_DOMAIN
            and entity.translation_key in LEGACY_CYCLE_TIME_KEYS
        )

        if is_old_sensor or is_old_preset:
            _LOGGER.info(f"Removing old cycle time entity {entity.entity_id}")

            entity_registry.async_remove(entity.entity_id)


def _set_suggested_time_units(hass: HomeAssistant, entry: ConfigEntry):
    """
    Show Cycle Time Left in hours.

    New entities get this as their suggested unit. Home Assistant only
    applies a suggested unit when it first creates an entity, so set it here
    for entities made by older versions. A unit the user picked stays.
    """
    entity_registry = er.async_get(hass)

    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        unit = SUGGESTED_TIME_UNITS.get(entity.translation_key)
        sensor_options = entity.options.get(SENSOR_DOMAIN, {})

        if (
            entity.domain == SENSOR_DOMAIN
            and unit is not None
            and CONF_UNIT_OF_MEASUREMENT not in sensor_options
        ):
            _LOGGER.info(f"Showing {entity.entity_id} in {unit}")

            entity_registry.async_update_entity_options(
                entity.entity_id,
                SENSOR_DOMAIN,
                {**sensor_options, CONF_UNIT_OF_MEASUREMENT: unit},
            )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info(f"Unloading {DOMAIN} integration, Entry ID: {entry.entry_id}")

    entry_id = entry.entry_id
    domain_data = hass.data.get(DOMAIN, {})
    coordinator: MyDolphinPlusCoordinator | None = domain_data.get(entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        if coordinator is not None:
            await coordinator.terminate()

        domain_data.pop(entry_id, None)

        if not domain_data:
            hass.data.pop(DOMAIN, None)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Remove a config entry."""
    _LOGGER.info(f"Removing {DOMAIN} integration, Entry ID: {entry.entry_id}")

    entry_id = entry.entry_id
    config_manager = ConfigManager(hass, entry)

    await config_manager.remove(entry_id)
