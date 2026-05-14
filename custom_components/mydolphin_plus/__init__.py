"""
This component provides support for MyDolphin Plus.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/mydolphin_plus/
"""

import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, EVENT_HOMEASSISTANT_START
from homeassistant.core import HomeAssistant

from .common.consts import (
    CONF_APP_ID,
    DEFAULT_APP_ID,
    DEFAULT_NAME,
    DOMAIN,
    INITIAL_TOKENS_KEY,
    PLATFORMS,
    STORAGE_DATA_ID_TOKEN,
    STORAGE_DATA_ID_TOKEN_EXPIRES_AT,
    STORAGE_DATA_MOTOR_UNIT_SERIAL,
    STORAGE_DATA_REFRESH_TOKEN,
    STORAGE_DATA_SERIAL_NUMBER,
    resolve_app_id,
)
from .managers.config_manager import ConfigManager
from .managers.coordinator import MyDolphinPlusCoordinator
from .models.exceptions import LoginError

_LOGGER = logging.getLogger(__name__)


async def async_setup(_hass, _config):
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate older config entries to include selected app metadata."""
    data = dict(entry.data)
    app_id = resolve_app_id(data.get(CONF_APP_ID))

    if data.get(CONF_APP_ID) != app_id or entry.version < 2:
        data[CONF_APP_ID] = app_id
        hass.config_entries.async_update_entry(entry, data=data, version=2)

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
                data={
                    CONF_APP_ID: resolve_app_id(
                        entry_config.get(CONF_APP_ID, DEFAULT_APP_ID)
                    ),
                    CONF_USERNAME: entry_config.get(CONF_USERNAME),
                },
            )

        is_initialized = config_manager.is_initialized

        if is_initialized:
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
