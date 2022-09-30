from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import EntityDescription

from ...core.helpers.const import *
from ...core.helpers.enums import EntityStatus


class EntityData:
    state: str | bool | None
    attributes: dict
    device_name: str | None
    status: EntityStatus
    disabled: bool
    domain: str | None
    entry_id: str
    entity_description: EntityDescription
    action: Any

    def __init__(self, entry_id: str, entity_description: EntityDescription):
        self.entry_id = entry_id
        self.entity_description = entity_description
        self.state = None
        self.attributes = {}
        self.device_name = None
        self.status = EntityStatus.CREATED
        self.disabled = False
        self.domain = None
        self.action = None

    @property
    def name(self):
        return self.entity_description.name

    @property
    def unique_id(self):
        unique_id = f"{DOMAIN}-{self.domain}-{self.name}"

        return unique_id

    def set_created_or_updated(self, was_created):
        self.status = EntityStatus.CREATED if was_created else EntityStatus.UPDATED

    def __repr__(self):
        obj = {
            ENTITY_UNIQUE_ID: self.unique_id,
            ENTITY_NAME: self.name,
            ENTITY_STATE: self.state,
            ENTITY_ATTRIBUTES: self.attributes,
            ENTITY_DEVICE_NAME: self.device_name,
            ENTITY_STATUS: self.status,
            ENTITY_DISABLED: self.disabled,
            ENTITY_DOMAIN: self.domain,
            ENTITY_CONFIG_ENTRY_ID: self.entry_id
        }

        to_string = f"{obj}"

        return to_string
