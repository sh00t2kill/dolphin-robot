from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass

from ...core.helpers.const import *
from ...core.helpers.enums import EntityStatus
from .select_description import SelectDescription


class EntityData:
    id: str | None
    name: str | None
    state: str | None
    attributes: dict
    icon: str | None
    device_name: str | None
    status: EntityStatus
    sensor_device_class: SensorDeviceClass | None
    sensor_state_class: SensorDeviceClass | None
    binary_sensor_device_class: BinarySensorDeviceClass | None
    details: dict
    disabled: bool
    domain: str | None
    entry_id: str
    entity_description: SelectDescription | None
    action: Any
    icon_set: dict | None
    default_icon: str | None

    def __init__(self, entry_id: str):
        self.id = None
        self.name = None
        self.state = None
        self.attributes = {}
        self.icon = None
        self.device_name = None
        self.status = EntityStatus.CREATED
        self.sensor_state_class = None
        self.sensor_device_class = None
        self.binary_sensor_device_class = None
        self.details = {}
        self.disabled = False
        self.domain = None
        self.entry_id = entry_id
        self.entity_description = None
        self.action = None
        self.default_icon = None

    @property
    def unique_id(self):
        unique_id = f"{DOMAIN}-{self.domain}-{self.name}"

        return unique_id

    def set_created_or_updated(self, was_created):
        self.status = EntityStatus.CREATED if was_created else EntityStatus.UPDATED

    def __repr__(self):
        obj = {
            ENTITY_ID: self.id,
            ENTITY_UNIQUE_ID: self.unique_id,
            ENTITY_NAME: self.name,
            ENTITY_STATE: self.state,
            ENTITY_ATTRIBUTES: self.attributes,
            ENTITY_ICON: self.icon,
            ENTITY_DEVICE_NAME: self.device_name,
            ENTITY_STATUS: self.status,
            ENTITY_SENSOR_DEVICE_CLASS: self.sensor_device_class,
            ENTITY_SENSOR_STATE_CLASS: self.sensor_state_class,
            ENTITY_BINARY_SENSOR_DEVICE_CLASS: self.binary_sensor_device_class,
            ENTITY_MONITOR_DETAILS: self.details,
            ENTITY_DISABLED: self.disabled,
            ENTITY_DOMAIN: self.domain,
            ENTITY_CONFIG_ENTRY_ID: self.entry_id
        }

        to_string = f"{obj}"

        return to_string
