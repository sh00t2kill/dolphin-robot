from __future__ import annotations

import logging
import sys
from typing import Any, Callable

from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ...core.helpers.const import *
from ...core.helpers.enums import EntityStatus
from ...core.models.entity_data import EntityData

_LOGGER = logging.getLogger(__name__)


class DomainData:
    name: str
    async_add_devices: AddEntitiesCallback
    initializer: Callable[[HomeAssistant, EntityData], Any]
    entities: dict[str, EntityData]

    def __init__(
            self,
            name,
            async_add_devices: AddEntitiesCallback,
            initializer: Callable[[HomeAssistant, EntityData], Any]
    ):
        self.name = name
        self.async_add_devices = async_add_devices
        self.initializer = initializer
        self.entities = {}

    def get_entity(self, name) -> EntityData | None:
        entity = self.entities.get(name)

        return entity

    def set_entity(
            self,
            entity: EntityData,
            destructors: list[bool] = None
    ):
        try:
            if destructors is not None and True in destructors:
                if entity.status == EntityStatus.CREATED:
                    entity = None

                else:
                    entity.status = EntityStatus.DELETED

            if entity is not None:
                self.entities[entity.name] = entity

                if entity.status != EntityStatus.READY:
                    _LOGGER.debug(f"{entity.name} ({entity.domain}) {entity.status}, state: {entity.state}")

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to set entity, Entity: {entity}, Error: {str(ex)}, Line: {line_number}")

    def delete_entity(self, name):
        if name in self.entities:
            del self.entities[name]

    def __repr__(self):
        obj = {
            CONF_NAME: self.name
        }

        to_string = f"{obj}"

        return to_string
