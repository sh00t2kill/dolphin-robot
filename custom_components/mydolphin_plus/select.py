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
    select = MyDolphinPlusSelect(entity.name)
    select.initialize(hass, entity, CURRENT_DOMAIN)

    return select


@dataclass
class BaseSelectDescription(SelectEntityDescription):
    """A class that describes select entities."""

    options: tuple = ()

@dataclass
class CleaningModeSelectDescription(BaseSelectDescription):
    """A class that describes select entities."""

    options: tuple = ()

@dataclass
class LedModeSelectDescription(BaseSelectDescription):
    """A class that describes select entities."""

    options: tuple = ()


SELECTOR_TYPES = {
    ATTR_CLEANING_MODE: CleaningModeSelectDescription(
        key=ATTR_CLEANING_MODE,
        name=ATTR_CLEANING_MODE,
        icon=CLEANING_MODE_ICON_DEFAULT,
        device_class=f"{DOMAIN}__{ATTR_CLEANING_MODE}",
        options=tuple(ICON_CLEANING_MODES.keys()),
        entity_category=EntityCategory.CONFIG,
    ),
    ATTR_LED_MODE: LedModeSelectDescription(
        key=ATTR_LED_MODE,
        name=ATTR_LED_MODE,
        icon=LED_MODE_ICON_DEFAULT,
        device_class=f"{DOMAIN}__{ATTR_LED_MODE}",
        options=tuple(ICON_LED_MODES.keys()),
        entity_category=EntityCategory.CONFIG,
    ),
}


class MyDolphinPlusSelect(SelectEntity, MyDolphinPlusEntity, ABC):
    def __init__(self, entity_name: str):
        super().__init__()

        is_led_mode = entity_name.endswith("Led Mode")

        selector_type = ATTR_LED_MODE if is_led_mode else ATTR_CLEANING_MODE
        self._icon_set = ICON_LED_MODES if is_led_mode else ICON_CLEANING_MODES
        self._action = self.ha.set_led_mode if is_led_mode else self.ha.set_cleaning_mode

        self.entity_description: BaseSelectDescription = SELECTOR_TYPES[selector_type]
        self._attr_options = list(self.entity_description.options)

    @property
    def current_option(self) -> str:
        """Return current lamp mode."""
        return self.entity.state

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        icon = self._icon_set.get(self.entity.state, "mdi:cctv")

        return icon

    async def async_select_option(self, option: str) -> None:
        """Select monitor mode."""
        await self._action(option)
