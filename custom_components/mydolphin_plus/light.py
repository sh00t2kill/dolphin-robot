from abc import ABC
import logging
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import MyDolphinPlusBaseEntity, async_setup_entities
from .common.consts import (
    ACTION_ENTITY_TURN_OFF,
    ACTION_ENTITY_TURN_ON,
    ATTR_ATTRIBUTES,
    ATTR_IS_ON,
    SIGNAL_DEVICE_NEW,
)
from .common.entity_descriptions import MyDolphinPlusLightEntityDescription
from .managers.coordinator import MyDolphinPlusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    @callback
    def _async_device_new(entry_id: str):
        if entry.entry_id != entry_id:
            return

        async_setup_entities(
            hass,
            entry,
            Platform.LIGHT,
            MyDolphinPlusLightEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class MyDolphinPlusLightEntity(MyDolphinPlusBaseEntity, LightEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: MyDolphinPlusLightEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(entity_description, coordinator)

        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_execute_device_action(ACTION_ENTITY_TURN_ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_execute_device_action(ACTION_ENTITY_TURN_OFF)

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            is_on = data.get(ATTR_IS_ON)
            attributes = data.get(ATTR_ATTRIBUTES)

            self._attr_is_on = is_on
            self._attr_extra_state_attributes = attributes

        else:
            self._attr_is_on = None
