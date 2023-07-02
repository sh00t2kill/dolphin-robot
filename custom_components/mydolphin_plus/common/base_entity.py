import logging
import sys
from typing import Any

from slugify import slugify

from custom_components.mydolphin_plus import DOMAIN, MyDolphinPlusCoordinator
from custom_components.mydolphin_plus.common.entity_descriptions import (
    ENTITY_DESCRIPTIONS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    platform: Platform,
    entity_description_type: type,
    entity_type: type,
    async_add_entities,
):
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]

        entities = []

        for entity_description in ENTITY_DESCRIPTIONS:
            if isinstance(entity_description, entity_description_type):
                entity = entity_type(entity_description, coordinator)

                entities.append(entity)

        _LOGGER.debug(f"Setting up {platform} entities: {entities}")

        async_add_entities(entities, True)

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(
            f"Failed to initialize {platform}, Error: {ex}, Line: {line_number}"
        )


class MyDolphinPlusBaseEntity(CoordinatorEntity):
    def __init__(
        self,
        entity_description: EntityDescription,
        coordinator: MyDolphinPlusCoordinator,
        platform: Platform,
    ):
        super().__init__(coordinator)

        device_info = coordinator.get_device()
        device_name = device_info.get("name")
        identifiers = device_info.get("identifiers")
        serial_number = list(identifiers)[0][1]

        entity_name = device_name

        if entity_description.name is not None and len(entity_description.name) > 0:
            entity_name = f"{entity_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        unique_id = slugify(f"{platform}_{serial_number}_{slugify_name}")

        self.entity_description = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

    @property
    def _local_coordinator(self) -> MyDolphinPlusCoordinator:
        return self.coordinator

    async def async_execute_device_action(self, key: str, *kwargs: Any):
        async_device_action = self._local_coordinator.get_device_action(
            self.entity_description, key
        )

        await async_device_action(*kwargs)

    def get_data(self) -> dict | None:
        device_data = self._local_coordinator.get_data(self.entity_description)

        _LOGGER.debug(f"Data for {self.unique_id}: {device_data}")

        return device_data
