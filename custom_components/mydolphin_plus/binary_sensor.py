import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ICON, Platform
from homeassistant.core import HomeAssistant

from .common.base_entity import MyDolphinPlusBaseEntity, async_setup_entities
from .common.consts import ATTR_ATTRIBUTES, ATTR_IS_ON
from .common.entity_descriptions import MyDolphinPlusDailyBinarySensorEntityDescription
from .managers.coordinator import MyDolphinPlusCoordinator

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = Platform.SENSOR


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_entities(
        hass,
        entry,
        CURRENT_DOMAIN,
        BinarySensorEntityDescription,
        MyDolphinPlusBinarySensorEntity,
        async_add_entities,
    )


class MyDolphinPlusBinarySensorEntity(MyDolphinPlusBaseEntity, BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: BinarySensorEntityDescription
        | MyDolphinPlusDailyBinarySensorEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(entity_description, coordinator, CURRENT_DOMAIN)

        self._attr_device_class = entity_description.device_class

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            is_on = data.get(ATTR_IS_ON)
            attributes = data.get(ATTR_ATTRIBUTES)
            icon = data.get(ATTR_ICON)

            self._attr_is_on = is_on
            self._attr_extra_state_attributes = attributes

            if icon is not None:
                self._attr_icon = icon

        else:
            self._attr_is_on = None
