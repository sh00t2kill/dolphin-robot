"""
Support for camera.
"""
from __future__ import annotations

import logging

from .core.components.camera import CoreCamera
from .core.helpers.setup_base_entry import async_setup_base_entry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the camera."""
    await async_setup_base_entry(
        hass, config_entry, async_add_devices, CoreCamera.get_domain(), CoreCamera.get_component
    )


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"Unload entry for {CoreCamera.get_domain()} domain: {config_entry}")

    return True


async def async_remove_entry(hass, entry) -> None:
    _LOGGER.info(f"Remove entry for {CoreCamera.get_domain()} entry: {entry}")
