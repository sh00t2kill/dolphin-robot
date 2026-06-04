from abc import ABC
import logging
from typing import Any

from homeassistant.components.vacuum import (
    SERVICE_LOCATE,
    SERVICE_PAUSE,
    SERVICE_RETURN_TO_BASE,
    SERVICE_SET_FAN_SPEED,
    SERVICE_START,
    StateVacuumEntity,
    VacuumActivity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_MODE, ATTR_STATE, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

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
            MyDolphinPlusVacuumEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class MyDolphinPlusVacuumEntity(MyDolphinPlusBaseEntity, StateVacuumEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: MyDolphinPlusVacuumEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(entity_description, coordinator)

        self._attr_supported_features = entity_description.features
        self._attr_fan_speed_list = entity_description.fan_speed_list

        # Battery level is now handled by a dedicated battery sensor
        self._attr_activity = VacuumActivity.DOCKED

    @property
    def activity(self) -> VacuumActivity | None:
        """Return the current activity of the vacuum."""
        return self._attr_activity

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the vacuum cleaner to return to the dock."""
        await self.async_execute_device_action(SERVICE_RETURN_TO_BASE)

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        await self.async_execute_device_action(SERVICE_SET_FAN_SPEED, fan_speed)

    async def async_start(self) -> None:
        await self.async_execute_device_action(SERVICE_START, self.activity)

    async def async_pause(self, **kwargs: Any) -> None:
        await self.async_execute_device_action(SERVICE_PAUSE, self.activity)

    async def async_locate(self, **kwargs: Any) -> None:
        """Locate the vacuum cleaner."""
        await self.async_execute_device_action(SERVICE_LOCATE)

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            state = data.get(ATTR_STATE)
            attributes = data.get(ATTR_ATTRIBUTES)

            fan_speed = attributes.get(ATTR_MODE)

            # State is already a VacuumActivity enum from SystemDetails
            if isinstance(state, VacuumActivity):
                self._attr_activity = state
            else:
                # Fallback for string states (shouldn't happen with current implementation)
                self._attr_activity = VacuumActivity.DOCKED

            self._attr_extra_state_attributes = attributes
            self._attr_fan_speed = fan_speed

        else:
            self._attr_activity = VacuumActivity.DOCKED
