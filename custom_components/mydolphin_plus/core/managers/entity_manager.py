from __future__ import annotations

import logging
import sys

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntryDisabler

from ...core.helpers.const import *
from ...core.helpers.enums import EntityStatus
from ...core.models.domain_data import DomainData
from ...core.models.entity_data import EntityData

_LOGGER = logging.getLogger(__name__)


class EntityManager:
    """ Entity Manager is agnostic to component - PLEASE DON'T CHANGE """

    hass: HomeAssistant
    domain_component_manager: dict[str, DomainData]

    def __init__(self, hass, ha):
        self.hass: HomeAssistant = hass
        self._ha = ha
        self.domain_component_manager: dict[str, DomainData] = {}

    @property
    def entity_registry(self) -> EntityRegistry:
        return self._ha.entity_registry

    @property
    def available_domains(self):
        return self.domain_component_manager.keys()

    def set_domain_data(self, domain_data: DomainData):
        self.domain_component_manager[domain_data.name] = domain_data

    def get_domain_data(self, domain: str) -> DomainData | None:
        domain_data = self.domain_component_manager.get(domain)

        return domain_data

    def update(self):
        self.hass.async_create_task(self._async_update())

    async def _handle_created_entities(self, entity_id, entity: EntityData, domain_component):
        entity_item = self.entity_registry.async_get(entity_id)

        if entity_item is not None:
            if entity.disabled:
                _LOGGER.info(f"Disabling entity, Data: {entity}")

                self.entity_registry.async_update_entity(entity_id,
                                                         disabled_by=RegistryEntryDisabler.INTEGRATION)

            else:
                entity.disabled = entity_item.disabled

        entity_component = domain_component(self.hass, entity)

        if entity_id is not None:
            entity_component.entity_id = entity_id
            state = self.hass.states.get(entity_id)

            if state is not None:
                restored = state.attributes.get("restored", False)

                if restored:
                    _LOGGER.info(f"Restored {entity_id} ({entity.name})")

        entity.status = EntityStatus.READY

        return entity_component

    async def _async_update(self):
        _LOGGER.debug("Starting to update entities")

        last_handled_domain = None

        try:
            for domain in self.domain_component_manager:
                last_handled_domain = domain
                domain_data = self.domain_component_manager.get(domain)
                entities_to_add = []
                entities_to_delete = {}

                if domain_data is None:
                    _LOGGER.error(f"Failed to get domain manager for {domain}")

                for name in domain_data.entities:
                    entity = domain_data.entities.get(name)

                    entity_id = self.entity_registry.async_get_entity_id(
                        domain, DOMAIN, entity.unique_id
                    )

                    if entity.status == EntityStatus.CREATED:
                        entity_component = await self._handle_created_entities(entity_id,
                                                                               entity,
                                                                               domain_data.initializer)

                        if entity_component is not None:
                            entities_to_add.append(entity_component)

                    elif entity.status == EntityStatus.DELETED:
                        entities_to_delete[entity_id] = entity

                entities_count = len(entities_to_add)

                if entities_count > 0:
                    domain_data.async_add_devices(entities_to_add)

                    _LOGGER.info(f"{entities_count} {domain} components created")

                deleted_count = len(entities_to_delete.keys())
                if deleted_count > 0:
                    for entity_id in entities_to_delete:
                        entity = entities_to_delete[entity_id]

                        entity_item = self.entity_registry.async_get(entity_id)

                        if entity_item is not None:
                            _LOGGER.info(f"Removed {entity_id} ({entity.name})")

                            self.entity_registry.async_remove(entity_id)

                        domain_data.delete_entity(entity.name)

                    _LOGGER.info(f"{deleted_count} {domain} components deleted")

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to update, "
                f"Last handled domain: {last_handled_domain}, "
                f"Error: {str(ex)}, "
                f"Line: {line_number}"
            )

    @staticmethod
    def compare_data(entity: EntityData, data: dict[str, tuple]) -> bool:
        modified = False
        msgs = []

        for data_key in data:
            original, latest = data[data_key]

            if original != latest:
                msgs.append(f"{data_key} changed from {original} to {latest}")
                modified = True

        if modified:
            full_message = " | ".join(msgs)

            _LOGGER.debug(f"{entity.name} | {entity.domain} | {full_message}")

        return modified

    @staticmethod
    def get_empty_entity(entry_id: str) -> EntityData:
        data = EntityData(entry_id)

        return data

    def get(self, domain: str, name: str) -> EntityData | None:
        domain_data = self.get_domain_data(domain)

        entity = domain_data.get_entity(name)

        return entity

    def set(self, entity: EntityData, destructors: list[bool] = None):
        domain_data = self.get_domain_data(entity.domain)

        entity = domain_data.set_entity(entity, destructors)

        return entity
