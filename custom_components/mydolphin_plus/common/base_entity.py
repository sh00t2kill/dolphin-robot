import logging
import sys
from typing import Any

from custom_components.mydolphin_plus import DOMAIN, MyDolphinPlusCoordinator
from custom_components.mydolphin_plus.common.entity_descriptions import (
    ENTITY_DESCRIPTIONS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)


def async_setup_entities(
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
    ):
        super().__init__(coordinator)

        device_info = coordinator.get_device()
        identifiers = device_info.get("identifiers")
        serial_number = list(identifiers)[0][1]

        platform = self.platform.domain

        entity_name = coordinator.config_manager.get_entity_name(
            platform, entity_description, device_info
        )

        if entity_description.name is not None and len(entity_description.name) > 0:
            entity_name = f"{entity_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        unique_id = slugify(f"{platform}_{serial_number}_{slugify_name}")

        self.entity_description = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

        self._data = {}

    @property
    def _local_coordinator(self) -> MyDolphinPlusCoordinator:
        return self.coordinator

    @property
    def data(self) -> dict | None:
        return self._data

    async def async_execute_device_action(self, key: str, *kwargs: Any):
        async_device_action = self._local_coordinator.get_device_action(
            self.entity_description, key
        )

        await async_device_action(*kwargs)

        await self.coordinator.async_request_refresh()

    def update_component(self, data):
        pass

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        try:
            new_data = self._local_coordinator.get_data(self.entity_description)

            if self._data != new_data:
                _LOGGER.debug(f"Data for {self.unique_id}: {new_data}")

                self.update_component(new_data)

                self._data = new_data

                self.async_write_ha_state()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to update {self.unique_id}, Error: {ex}, Line: {line_number}"
            )
