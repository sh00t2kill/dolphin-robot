from abc import ABC
import logging
import sys

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_STATE, Platform
from homeassistant.core import HomeAssistant

from .common.base_entity import MyDolphinPlusBaseEntity, async_setup_entities
from .common.consts import ACTION_ENTITY_SELECT_OPTION, ATTR_ATTRIBUTES
from .managers.coordinator import MyDolphinPlusCoordinator

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = Platform.SELECT


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_entities(
        hass,
        entry,
        CURRENT_DOMAIN,
        SelectEntityDescription,
        MyDolphinPlusSelectEntity,
        async_add_entities,
    )


class MyDolphinPlusSelectEntity(MyDolphinPlusBaseEntity, SelectEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: SelectEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(entity_description, coordinator, CURRENT_DOMAIN)

        self.entity_description = entity_description

        self._attr_current_option = entity_description.options[0]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.async_execute_device_action(ACTION_ENTITY_SELECT_OPTION, option)

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        try:
            device_data = self.get_data()

            if device_data is not None:
                state = device_data.get(ATTR_STATE)
                attributes = device_data.get(ATTR_ATTRIBUTES)

                self._attr_current_option = state
                self._attr_extra_state_attributes = attributes

            else:
                self._attr_current_option = self.entity_description.options[0]

            self.async_write_ha_state()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to update {self.unique_id}, Error: {ex}, Line: {line_number}"
            )
