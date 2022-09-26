"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://github.com/sh00t2kill/dolphin-robot
"""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant

from .component.helpers.const import *
from .component.models.mydolphin_plus_entity import MyDolphinPlusEntity
from .core.models.base_entity import async_setup_base_entry
from .core.models.entity_data import EntityData

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = DOMAIN_SENSOR


def get_sensor(hass: HomeAssistant, entity: EntityData):
    sensor = MyDolphinPlusSensor()
    sensor.initialize(hass, entity, CURRENT_DOMAIN)

    return sensor


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up EdgeOS based off an entry."""
    await async_setup_base_entry(
        hass, entry, async_add_entities, CURRENT_DOMAIN, get_sensor
    )


async def async_unload_entry(hass, config_entry):
    _LOGGER.info(f"async_unload_entry {CURRENT_DOMAIN}: {config_entry}")

    return True


class MyDolphinPlusSensor(SensorEntity, MyDolphinPlusEntity):
    """Representation a binary sensor that is updated by EdgeOS."""

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.entity.state

    async def async_added_to_hass_local(self):
        _LOGGER.info(f"Added new {self.name}")

    @property
    def device_class(self) -> SensorDeviceClass | str | None:
        """Return the class of this sensor."""
        return self.entity.sensor_device_class

    @property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the class of this sensor."""
        return self.entity.sensor_state_class
