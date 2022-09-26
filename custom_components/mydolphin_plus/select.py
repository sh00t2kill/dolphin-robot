"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://github.com/sh00t2kill/dolphin-robot
"""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .component.helpers.const import *
from .component.models.mydolphin_plus_entity import MyDolphinPlusEntity
from .core.models.base_entity import async_setup_base_entry
from .core.models.entity_data import EntityData
from .core.models.select_description import SelectDescription

DEPENDENCIES = [DOMAIN]

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = DOMAIN_SELECT


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the SELECT component."""
    await async_setup_base_entry(
        hass, config_entry, async_add_devices, CURRENT_DOMAIN, get_select
    )


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"Unload entry for {CURRENT_DOMAIN} domain: {config_entry}")

    return True


def get_select(hass: HomeAssistant, entity: EntityData):
    select = MyDolphinPlusSelect(entity.entity_description)
    select.initialize(hass, entity, CURRENT_DOMAIN)

    return select


class MyDolphinPlusSelect(SelectEntity, MyDolphinPlusEntity, ABC):
    def __init__(self, entity_description: SelectDescription):
        super().__init__()

        self.entity_description = entity_description
        self._attr_options = list(entity_description.options)

    @property
    def current_option(self) -> str:
        """Return current lamp mode."""
        return str(self.entity.state)

    async def async_select_option(self, option: str) -> None:
        """Select monitor mode."""
        await self.entity.action(option)
