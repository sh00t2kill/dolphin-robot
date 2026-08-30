from abc import ABC
import logging

from homeassistant.components.button import SERVICE_PRESS, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import MyDolphinPlusBaseEntity, async_setup_entities
from .common.consts import ATTR_ATTRIBUTES, SIGNAL_DEVICE_NEW
from .common.entity_descriptions import MyDolphinPlusButtonEntityDescription
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
            Platform.BUTTON,
            MyDolphinPlusButtonEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class MyDolphinPlusButtonEntity(MyDolphinPlusBaseEntity, ButtonEntity, ABC):
    """Representation of a button."""

    def __init__(
        self,
        entity_description: MyDolphinPlusButtonEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(entity_description, coordinator)

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.async_execute_device_action(SERVICE_PRESS)

    def update_component(self, data):
        """Fetch new state parameters for the button."""
        if data is not None:
            attributes = data.get(ATTR_ATTRIBUTES)

            self._attr_extra_state_attributes = attributes
