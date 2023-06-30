from abc import ABC
import logging
import sys

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_STATE, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import (
    ACTION_ENTITY_SELECT_OPTION,
    ATTR_ATTRIBUTES,
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
                if isinstance(entity_description, SelectEntityDescription):
                    entity = MyDolphinPlusSelectEntity(entity_description, coordinator)

                    entities.append(entity)

            _LOGGER.debug(f"Setting up {Platform.SELECT} entities: {entities}")

            async_add_entities(entities, True)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize {Platform.SELECT}, Error: {ex}, Line: {line_number}"
            )

    """Set up the binary sensor platform."""
    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_MY_DOLPHIN_PLUS_DEVICE_NEW, _async_device_new
        )
    )


class MyDolphinPlusSelectEntity(CoordinatorEntity, SelectEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: SelectEntityDescription,
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

        unique_id = slugify(f"{Platform.BINARY_SENSOR}_{serial_number}_{slugify_name}")

        self.entity_description = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id
        self._attr_current_option = entity_description.options[0]

    @property
    def _local_coordinator(self) -> MyDolphinPlusCoordinator:
        return self.coordinator

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        async_select_option = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_SELECT_OPTION
        )

        await async_select_option(option)

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        device_data = self._local_coordinator.get_data(self.entity_description)
        state = device_data.get(ATTR_STATE)
        attributes = device_data.get(ATTR_ATTRIBUTES)

        self._attr_current_option = state
        self._attr_extra_state_attributes = attributes

        self.async_write_ha_state()
