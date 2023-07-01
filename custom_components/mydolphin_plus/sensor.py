import logging
import sys

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ICON, ATTR_STATE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import ATTR_ATTRIBUTES, DOMAIN
from .common.entity_descriptions import ENTITY_DESCRIPTIONS
from .managers.coordinator import MyDolphinPlusCoordinator

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = Platform.SENSOR


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]

        entities = []

        for entity_description in ENTITY_DESCRIPTIONS:
            if isinstance(entity_description, SensorEntityDescription):
                entity = MyDolphinPlusSensorEntity(entity_description, coordinator)

                entities.append(entity)

        _LOGGER.debug(f"Setting up {CURRENT_DOMAIN} entities: {entities}")

        async_add_entities(entities, True)

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(
            f"Failed to initialize {CURRENT_DOMAIN}, Error: {ex}, Line: {line_number}"
        )


class MyDolphinPlusSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: SensorEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(coordinator)

        device_info = coordinator.get_device()
        device_name = device_info.get("name")
        identifiers = device_info.get("identifiers")
        serial_number = list(identifiers)[0][1]

        entity_name = f"{device_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        unique_id = slugify(f"{CURRENT_DOMAIN}_{serial_number}_{slugify_name}")

        self.entity_description = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id
        self._attr_device_class = entity_description.device_class

    @property
    def _local_coordinator(self) -> MyDolphinPlusCoordinator:
        return self.coordinator

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        try:
            device_data = self._local_coordinator.get_data(self.entity_description)
            if device_data is not None:
                _LOGGER.debug(f"Data for {self.unique_id}: {device_data}")

                state = device_data.get(ATTR_STATE)
                attributes = device_data.get(ATTR_ATTRIBUTES)
                icon = device_data.get(ATTR_ICON)

                self._attr_native_value = state
                self._attr_extra_state_attributes = attributes

                if icon is not None:
                    self._attr_icon = icon

            self.async_write_ha_state()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to update {self.unique_id}, Error: {ex}, Line: {line_number}"
            )
