from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from ...core.helpers.const import *
from ...core.helpers.enums import EntityStatus


class EntityData:
    id: str
    name: str
    state: str
    attributes: dict
    icon: str
    device_name: str
    status: EntityStatus
    binary_sensor_device_class: BinarySensorDeviceClass | None
    details: dict
    disabled: bool
    domain: str
    entry_id: str

    def __init__(self, entry_id: str):
        self.id = ""
        self.name = ""
        self.state = ""
        self.attributes = {}
        self.icon = ""
        self.device_name = ""
        self.status = EntityStatus.CREATED
        self.binary_sensor_device_class = None
        self.details = {}
        self.disabled = False
        self.domain = ""
        self.entry_id = entry_id

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
            ENTITY_BINARY_SENSOR_DEVICE_CLASS: self.binary_sensor_device_class,
            ENTITY_MONITOR_DETAILS: self.details,
            ENTITY_DISABLED: self.disabled,
            ENTITY_DOMAIN: self.domain,
            ENTITY_CONFIG_ENTRY_ID: self.entry_id
        }

        to_string = f"{obj}"

        return to_string
