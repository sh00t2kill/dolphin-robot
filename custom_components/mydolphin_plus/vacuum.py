from abc import ABC
import logging
from typing import Any

from homeassistant.components.vacuum import (
    SERVICE_LOCATE,
    SERVICE_PAUSE,
    SERVICE_RETURN_TO_BASE,
    SERVICE_SEND_COMMAND,
    SERVICE_SET_FAN_SPEED,
    SERVICE_START,
    StateVacuumEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_MODE, ATTR_STATE, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.icon import icon_for_battery_level

from .common.base_entity import MyDolphinPlusBaseEntity, async_setup_entities
from .common.consts import ATTR_ATTRIBUTES, SIGNAL_DEVICE_NEW
from .common.entity_descriptions import MyDolphinPlusVacuumEntityDescription
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
            Platform.VACUUM,
            MyDolphinPlusLightEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class MyDolphinPlusLightEntity(MyDolphinPlusBaseEntity, StateVacuumEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: MyDolphinPlusVacuumEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(entity_description, coordinator)

        self._attr_supported_features = entity_description.features
        self._attr_fan_speed_list = entity_description.fan_speed_list
        self._attr_battery_level = 100

    @property
    def battery_icon(self) -> str:
        """Return the battery icon for the vacuum cleaner."""
        return icon_for_battery_level(battery_level=self.battery_level, charging=True)

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the vacuum cleaner to return to the dock."""
        await self.async_execute_device_action(SERVICE_RETURN_TO_BASE)

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        await self.async_execute_device_action(SERVICE_SET_FAN_SPEED, fan_speed)

    async def async_start(self) -> None:
        await self.async_execute_device_action(SERVICE_START, self.state)

    async def async_pause(self, **kwargs: Any) -> None:
        await self.async_execute_device_action(SERVICE_PAUSE, self.state)

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send a command to a vacuum cleaner."""
        await self.async_execute_device_action(SERVICE_SEND_COMMAND, command, params)

    async def async_locate(self, **kwargs: Any) -> None:
        """Locate the vacuum cleaner."""
        await self.async_execute_device_action(SERVICE_LOCATE)

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            state = data.get(ATTR_STATE)
            attributes = data.get(ATTR_ATTRIBUTES)

            fan_speed = attributes.get(ATTR_MODE)

            self._attr_state = state
            self._attr_extra_state_attributes = attributes
            self._attr_fan_speed = fan_speed

        else:
            self._attr_state = None
