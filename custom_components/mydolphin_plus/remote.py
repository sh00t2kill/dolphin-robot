from collections.abc import Iterable
import logging

from homeassistant.components.remote import SERVICE_SEND_COMMAND, RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import SERVICE_TURN_OFF, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import MyDolphinPlusBaseEntity, async_setup_entities
from .common.consts import ATTR_ATTRIBUTES, ATTR_IS_ON, SIGNAL_DEVICE_NEW
from .common.entity_descriptions import MyDolphinPlusRemoteEntityDescription
from .common.joystick_direction import JoystickDirection
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
            Platform.NUMBER,
            MyDolphinPlusRemoteEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class MyDolphinPlusRemoteEntity(MyDolphinPlusBaseEntity, RemoteEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: MyDolphinPlusRemoteEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(entity_description, coordinator)

        self._attr_activity_list = entity_description.activity_list
        self._attr_supported_features = entity_description.features

    async def async_turn_on(self, activity: str = None, **kwargs):
        """Send the power on command."""

        if activity is None:
            activity = JoystickDirection.STOP

        await self.async_execute_device_action(SERVICE_SEND_COMMAND, activity)

    async def async_turn_off(self, activity: str = None, **kwargs):
        """Send the power on command."""
        await self.async_execute_device_action(SERVICE_TURN_OFF)

    async def async_send_command(self, command: Iterable[str], **kwargs):
        """Send commands to a device."""
        for command_item in command:
            await self.async_execute_device_action(SERVICE_SEND_COMMAND, command_item)

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            is_on = data.get(ATTR_IS_ON)
            attributes = data.get(ATTR_ATTRIBUTES)

            self._attr_is_on = is_on
            self._attr_extra_state_attributes = attributes

        else:
            self._attr_is_on = None
            self._attr_extra_state_attributes = {}
