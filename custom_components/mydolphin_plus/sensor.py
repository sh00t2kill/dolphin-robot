import logging

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ICON, ATTR_STATE, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import MyDolphinPlusBaseEntity, async_setup_entities
from .common.consts import ATTR_ATTRIBUTES, SIGNAL_DEVICE_NEW
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
            SensorEntityDescription,
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
        entity_description: SensorEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(entity_description, coordinator)

        self._attr_device_class = entity_description.device_class

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

        else:
            self._attr_native_value = None
