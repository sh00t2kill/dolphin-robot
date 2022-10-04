"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://github.com/sh00t2kill/dolphin-robot
"""
from __future__ import annotations

from abc import ABC
import logging
import time
from typing import Any

from homeassistant.components.vacuum import StateVacuumEntity, VacuumEntityFeature
from homeassistant.core import HomeAssistant

from .component.helpers.const import *
from .component.models.mydolphin_plus_entity import MyDolphinPlusEntity
from .core.models.base_entity import async_setup_base_entry
from .core.models.entity_data import EntityData

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]

CURRENT_DOMAIN = DOMAIN_VACUUM

VACUUM_FEATURES = VacuumEntityFeature.STATE | \
                  VacuumEntityFeature.FAN_SPEED | \
                  VacuumEntityFeature.RETURN_HOME | \
                  VacuumEntityFeature.SEND_COMMAND | \
                  VacuumEntityFeature.TURN_ON | \
                  VacuumEntityFeature.TURN_OFF


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the Switch component."""
    await async_setup_base_entry(
        hass, config_entry, async_add_devices, CURRENT_DOMAIN, get_component
    )


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"Unload entry for {CURRENT_DOMAIN} domain: {config_entry}")

    return True


def get_component(hass: HomeAssistant, entity: EntityData):
    switch = MyDolphinPlusVacuum()
    switch.initialize(hass, entity, CURRENT_DOMAIN)

    return switch


class MyDolphinPlusVacuum(StateVacuumEntity, MyDolphinPlusEntity, ABC):
    """Class for a Shinobi Video switch."""

    def __init__(self):
        super().__init__()

        self._attr_supported_features = VACUUM_FEATURES
        self._attr_fan_speed_list = list(CLEANING_MODES.values())

    @property
    def state(self) -> str | None:
        """Return the status of the vacuum cleaner."""
        return self.entity.state

    @property
    def fan_speed(self) -> str | None:
        """Return the fan speed of the vacuum cleaner."""
        return self.ha.get_fan_speed()

    def return_to_base(self, **kwargs: Any) -> None:
        """Set the vacuum cleaner to return to the dock."""
        self.ha.pickup()

    def set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        for key in CLEANING_MODES:
            value = CLEANING_MODES[key]

            if value == fan_speed:
                self.ha.set_cleaning_mode(key)

    def locate(self, **kwargs: Any) -> None:
        self.ha.set_led_enabled(True)
        time.sleep(2)
        self.ha.set_led_enabled(False)


    async def async_turn_on(self, **kwargs: Any) -> None:
        self.ha.set_power_state(True)

    async def async_start(self, **kwargs: Any) -> None:
        self.ha.set_power_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.ha.set_power_state(False)

    async def async_stop(self, **kwargs: Any) -> None:
        self.ha.set_power_state(False)

    async def async_pause(self, **kwargs: Any) -> None:
        self.ha.set_power_state(False)

    async def async_toggle(self, **kwargs: Any) -> None:
        is_on = self.entity.state == PWS_STATE_ON

        self.ha.set_power_state(not is_on)

    def send_command(
            self,
            command: str,
            params: dict[str, Any] | list[Any] | None = None,
            **kwargs: Any,
    ) -> None:
        """Send a command to a vacuum cleaner."""
        self.ha.send_command(command, params)
