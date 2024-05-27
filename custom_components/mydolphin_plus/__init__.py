"""
This component provides support for MyDolphin Plus.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/mydolphin_plus/
"""
import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START
from homeassistant.core import HomeAssistant

from .common.consts import DEFAULT_NAME, DOMAIN, PLATFORMS
from .managers.config_manager import ConfigManager
from .managers.coordinator import MyDolphinPlusCoordinator
from .managers.password_manager import PasswordManager
from .models.exceptions import LoginError

_LOGGER = logging.getLogger(__name__)


async def async_setup(_hass, _config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Shinobi Video component."""
    initialized = False

    try:
        entry_config = {key: entry.data[key] for key in entry.data}

        await PasswordManager.decrypt(hass, entry_config, entry.entry_id)

        config_manager = ConfigManager(hass, entry)
        await config_manager.initialize(entry_config)

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

    coordinator: MyDolphinPlusCoordinator = hass.data[DOMAIN][entry_id]

    await coordinator.terminate()

    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, platform)

    del hass.data[DOMAIN][entry_id]

    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info(f"Removing {DOMAIN} integration, Entry ID: {entry.entry_id}")

    entry_id = entry.entry_id

    coordinator: MyDolphinPlusCoordinator = hass.data[DOMAIN][entry_id]

    await coordinator.config_manager.remove(entry_id)

    result = await async_unload_entry(hass, entry)

    return result
