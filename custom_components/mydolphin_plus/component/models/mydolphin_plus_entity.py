from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

from ...component.helpers import get_ha
from ...core.models.base_entity import BaseEntity
from ...core.models.entity_data import EntityData

_LOGGER = logging.getLogger(__name__)


class MyDolphinPlusEntity(BaseEntity):
    """Representation a binary sensor that is updated by MyDolphin Plus."""

    def initialize(
        self,
        hass: HomeAssistant,
        entity: EntityData,
        current_domain: str,
    ):
        super().initialize(hass, entity, current_domain)

        self.ha = get_ha(self.hass, self.entry_id)
