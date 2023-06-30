from abc import ABC
import logging
import sys
from typing import Any

from homeassistant.components.vacuum import VacuumEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_STATE, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import (
    ACTION_ENTITY_LOCATE,
    ACTION_ENTITY_PAUSE,
    ACTION_ENTITY_RETURN_TO_BASE,
    ACTION_ENTITY_SEND_COMMAND,
    ACTION_ENTITY_SET_FAN_SPEED,
    ACTION_ENTITY_START,
    ACTION_ENTITY_STOP,
    ACTION_ENTITY_TOGGLE,
    ACTION_ENTITY_TURN_OFF,
    ACTION_ENTITY_TURN_ON,
    ATTR_ATTRIBUTES,
    DOMAIN,
    SIGNAL_MY_DOLPHIN_PLUS_DEVICE_NEW,
)
from .common.entity_descriptions import (
    ENTITY_DESCRIPTIONS,
    MyDolphinPlusVacuumEntityDescription,
)
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
                if isinstance(entity_description, MyDolphinPlusVacuumEntityDescription):
                    entity = MyDolphinPlusLightEntity(entity_description, coordinator)

                    entities.append(entity)

            _LOGGER.debug(f"Setting up {Platform.VACUUM} entities: {entities}")

            async_add_entities(entities, True)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize {Platform.VACUUM}, Error: {ex}, Line: {line_number}"
            )

    """Set up the binary sensor platform."""
    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_MY_DOLPHIN_PLUS_DEVICE_NEW, _async_device_new
        )
    )


class MyDolphinPlusLightEntity(CoordinatorEntity, VacuumEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: MyDolphinPlusVacuumEntityDescription,
        coordinator: MyDolphinPlusCoordinator,
    ):
        super().__init__(coordinator)

        device_info = coordinator.get_device()
        device_name = device_info.get("name")
        identifiers = device_info.get("identifiers")
        serial_number = list(identifiers)[0][1]

        entity_name = f"{device_name} {entity_description.name}"

        slugify_name = slugify(entity_name)

        unique_id = slugify(f"{Platform.VACUUM}_{serial_number}_{slugify_name}")

        self.entity_description = entity_description

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

        self._attr_supported_features = entity_description.features
        self._attr_fan_speed_list = entity_description.fan_speed_list

    @property
    def _local_coordinator(self) -> MyDolphinPlusCoordinator:
        return self.coordinator

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the vacuum cleaner to return to the dock."""
        async_return_to_base = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_RETURN_TO_BASE
        )

        await async_return_to_base()

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        async_set_fan_speed = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_SET_FAN_SPEED
        )

        await async_set_fan_speed(fan_speed)

    async def async_start(self, **kwargs: Any) -> None:
        async_start = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_START
        )

        await async_start(self.state)

    async def async_stop(self, **kwargs: Any) -> None:
        async_stop = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_STOP
        )

        await async_stop(self.state)

    async def async_pause(self, **kwargs: Any) -> None:
        async_pause = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_PAUSE
        )

        await async_pause(self.state)

    async def async_turn_on(self, **kwargs: Any) -> None:
        async_turn_on = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_TURN_ON
        )

        await async_turn_on(self.state)

    async def async_turn_off(self, **kwargs: Any) -> None:
        async_turn_off = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_TURN_OFF
        )

        await async_turn_off(self.state)

    async def async_toggle(self, **kwargs: Any) -> None:
        async_toggle = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_TOGGLE
        )

        await async_toggle(self.state)

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send a command to a vacuum cleaner."""
        async_send_command = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_SEND_COMMAND
        )

        await async_send_command(command, params)

    async def async_locate(self, **kwargs: Any) -> None:
        """Locate the vacuum cleaner."""
        async_locate = self._local_coordinator.get_device_action(
            self.entity_description, ACTION_ENTITY_LOCATE
        )

        await async_locate()

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        device_data = self._local_coordinator.get_data(self.entity_description)
        state = device_data.get(ATTR_STATE)
        attributes = device_data.get(ATTR_ATTRIBUTES)

        self._attr_state = state
        self._attr_extra_state_attributes = attributes

        self.async_write_ha_state()
