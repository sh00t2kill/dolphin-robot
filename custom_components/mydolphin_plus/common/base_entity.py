import logging
import sys
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from ..managers.config_manager import ConfigManager
from ..managers.coordinator import MyDolphinPlusCoordinator
from .consts import ATTR_ACTIONS, DATA_ROBOT_FAMILY, DOMAIN
from .entity_descriptions import MyDolphinPlusEntityDescription, get_entity_descriptions
from .robot_family import RobotFamily

_LOGGER = logging.getLogger(__name__)


def async_setup_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    platform: Platform,
    entity_type: type,
    async_add_entities,
):
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]

        robot_family_str = coordinator.api_data.get(DATA_ROBOT_FAMILY)
        robot_family = RobotFamily.from_string(robot_family_str)

        entity_descriptions = get_entity_descriptions(platform, robot_family)

        entities = [
            entity_type(entity_description, coordinator)
            for entity_description in entity_descriptions
        ]

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
        entity_description: MyDolphinPlusEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(coordinator)

        device_info = coordinator.get_device()
        identifiers = device_info.get("identifiers")
        serial_number = list(identifiers)[0][1]

        entity_name = coordinator.config_manager.get_entity_name(
            entity_description, device_info
        )

        slugify_name = slugify(entity_name)

        unique_id = slugify(
            f"{entity_description.platform}_{serial_number}_{slugify_name}"
        )

        self.entity_description = entity_description
        self._local_entity_description = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

        self._data = {}

    @property
    def _local_coordinator(self) -> MyDolphinPlusCoordinator:
        return self.coordinator

    @property
    def config_manager(self) -> ConfigManager:
        return self._local_coordinator.config_manager

    @property
    def robot_name(self) -> str:
        robot_name = self._local_coordinator.robot_name

        return robot_name

    @property
    def data(self) -> dict | None:
        return self._data

    async def async_execute_device_action(self, key: str, *kwargs: Any):
        async_device_action = self._local_coordinator.get_device_action(
            self.entity_description, key
        )

        await async_device_action(self.entity_description, *kwargs)

        await self.coordinator.async_request_refresh()

    def update_component(self, data):
        pass

    def get_translation(self, key) -> str | None:
        data = self.config_manager.get_translation(
            self._local_entity_description.platform, self.entity_description.key, key
        )

        return data

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        try:
            new_data = self._local_coordinator.get_data(self.entity_description)

            if self._data != new_data:
                data_for_log = {
                    key: new_data[key] for key in new_data if key != ATTR_ACTIONS
                }

                _LOGGER.debug(f"Data for {self.unique_id}: {data_for_log}")

                self.update_component(new_data)

                self._data = new_data

                self.async_write_ha_state()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to update {self.unique_id}, Error: {ex}, Line: {line_number}"
            )
