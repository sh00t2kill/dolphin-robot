"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://github.com/sh00t2kill/dolphin-robot
"""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .component.helpers.const import *
from .component.models.mydolphin_plus_entity import MyDolphinPlusEntity
from .core.models.base_entity import async_setup_base_entry
from .core.models.entity_data import EntityData

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]

CURRENT_DOMAIN = DOMAIN_SWITCH


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the Switch component."""
    await async_setup_base_entry(
        hass, config_entry, async_add_devices, CURRENT_DOMAIN, get_switch
    )


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"Unload entry for {CURRENT_DOMAIN} domain: {config_entry}")

    return True


def get_switch(hass: HomeAssistant, entity: EntityData):
    switch = MyDolphinPlusSwitch()
    switch.initialize(hass, entity, CURRENT_DOMAIN)

    return switch


class MyDolphinPlusSwitch(SwitchEntity, MyDolphinPlusEntity):
    """Class for a Shinobi Video switch."""

    @property
    def is_on(self) -> bool | None:
        """Return the boolean response if the node is on."""
        return self.entity.state

    def turn_on(self, **kwargs):
        """Turn device on."""
        self.set_mode(True)

    def turn_off(self, **kwargs):
        """Turn device off."""
        self.set_mode(False)

    def set_mode(self, enabled: bool):
        self.entity.action(enabled)

    async def async_setup(self):
        pass
