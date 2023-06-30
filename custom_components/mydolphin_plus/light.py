from abc import ABC
import logging
import sys
from typing import Any

from homeassistant.components.light import LightEntity, LightEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import (
    ACTION_ENTITY_TURN_OFF,
    ACTION_ENTITY_TURN_ON,
    ATTR_ATTRIBUTES,
    ATTR_IS_ON,
    DOMAIN,
    SIGNAL_MY_DOLPHIN_PLUS_DEVICE_NEW,
)
from .common.entity_descriptions import ENTITY_DESCRIPTIONS
from .managers.coordinator import MyDolphinPlusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    @callback
    def _async_device_new(serial_number):
        try:
            coordinator = hass.data[DOMAIN][entry.entry_id]

            device_data = coordinator.get_device()
            identifiers = device_data.get("identifiers")
            coordinator_serial_number = list(identifiers)[0][1]

            if coordinator_serial_number != serial_number:
                return

            entities = []

            for entity_description in ENTITY_DESCRIPTIONS:
                if isinstance(entity_description, LightEntityDescription):
                    entity = MyDolphinPlusLightEntity(entity_description, coordinator)

                    entities.append(entity)

            _LOGGER.debug(f"Setting up {Platform.LIGHT} entities: {entities}")

            async_add_entities(entities, True)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize {Platform.LIGHT}, Error: {ex}, Line: {line_number}"
            )

    """Set up the binary sensor platform."""
    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_MY_DOLPHIN_PLUS_DEVICE_NEW, _async_device_new
        )
    )


class MyDolphinPlusLightEntity(CoordinatorEntity, LightEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: LightEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(coordinator)

        super().__init__(coordinator)

        device_info = coordinator.get_device()
        device_name = device_info.get("name")
        identifiers = device_info.get("identifiers")
        serial_number = list(identifiers)[0][1]

        entity_name = f"{device_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        unique_id = slugify(f"{Platform.LIGHT}_{serial_number}_{slugify_name}")

        self.entity_description = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

    @property
    def _local_coordinator(self) -> MyDolphinPlusCoordinator:
        return self.coordinator

    async def async_turn_on(self, **kwargs: Any) -> None:
        async_turn_on = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_TURN_ON
        )

        await async_turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        async_turn_off = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_TURN_OFF
        )

        await async_turn_off()

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        device_data = self._local_coordinator.get_data(self.entity_description)
        is_on = device_data.get(ATTR_IS_ON)
        attributes = device_data.get(ATTR_ATTRIBUTES)

        self._attr_is_on = is_on
        self._attr_extra_state_attributes = attributes

        self.async_write_ha_state()
