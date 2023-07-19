import logging
from typing import Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ICON, ATTR_NAME, ATTR_STATE, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import MyDolphinPlusBaseEntity, async_setup_entities
from .common.consts import (
    ATTR_ATTRIBUTES,
    ATTR_ERROR_DESCRIPTIONS,
    ATTR_INSTRUCTIONS,
    DATA_KEY_PWS_ERROR,
    DATA_KEY_ROBOT_ERROR,
    DATA_ROBOT_NAME,
    ERROR_CLEAN_CODES,
    EVENT_ERROR,
    SIGNAL_DEVICE_NEW,
    TRANSLATION_KEY_ERROR_INSTRUCTIONS,
)
from .common.entity_descriptions import MyDolphinPlusSensorEntityDescription
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
            Platform.SENSOR,
            MyDolphinPlusSensorEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class MyDolphinPlusSensorEntity(MyDolphinPlusBaseEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: MyDolphinPlusSensorEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(entity_description, coordinator)

        self._attr_device_class = entity_description.device_class

        self._notify_handlers: dict[str, Callable] = {
            DATA_KEY_ROBOT_ERROR: self._notify_error,
            DATA_KEY_PWS_ERROR: self._notify_error,
        }

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            state = data.get(ATTR_STATE)
            attributes = data.get(ATTR_ATTRIBUTES)
            icon = data.get(ATTR_ICON)

            self._attr_native_value = state
            self._attr_extra_state_attributes = attributes

            if icon is not None:
                self._attr_icon = icon

            handler = self._notify_handlers.get(self.entity_description.name)

            if handler is not None:
                handler()

        else:
            self._attr_native_value = None

    def _notify_error(self):
        state = self._attr_native_value

        if state not in ERROR_CLEAN_CODES:
            attribute_key = f"{TRANSLATION_KEY_ERROR_INSTRUCTIONS}.{state}"

            event_data = {
                ATTR_NAME: self.entity_description.name,
                DATA_ROBOT_NAME: self.robot_name,
                ATTR_STATE: state,
                ATTR_ERROR_DESCRIPTIONS: self.get_translation(CONF_NAME),
                ATTR_INSTRUCTIONS: self.get_translation(attribute_key),
            }

            self.hass.bus.fire(EVENT_ERROR, event_data)
