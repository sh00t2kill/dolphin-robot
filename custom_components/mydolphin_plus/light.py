"""
Support for light.
"""
import logging

from .core.components.light import CoreLight
from .core.helpers.setup_base_entry import async_setup_base_entry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the entity."""
    await async_setup_base_entry(
        hass, config_entry, async_add_devices, CoreLight.get_domain(), CoreLight.get_component
    )


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"Unload entry for {CoreLight.get_domain()} domain: {config_entry}")

    return True


async def async_remove_entry(hass, entry) -> None:
    _LOGGER.info(f"Remove entry for {CoreLight.get_domain()} entry: {entry}")
