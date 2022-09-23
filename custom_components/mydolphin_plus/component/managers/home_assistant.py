"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/mydolphin_plus/
"""
from __future__ import annotations

import asyncio
import datetime
import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ...component.api.mydolphin_plus_api import MyDolphinPlusAPI
from ...component.helpers.const import *
from ...component.helpers.enums import ConnectivityStatus
from ...component.managers.event_manager import MyDolphinPlusEventManager
from ...configuration.managers.configuration_manager import (
    ConfigurationManager,
    async_get_configuration_manager,
)
from ...configuration.models.config_data import ConfigData
from ...core.managers.home_assistant import HomeAssistantManager

_LOGGER = logging.getLogger(__name__)


class MyDolphinPlusHomeAssistantManager(HomeAssistantManager):
    def __init__(self, hass: HomeAssistant):
        super().__init__(hass, SCAN_INTERVAL, HEARTBEAT_INTERVAL_SECONDS)

        self._api: MyDolphinPlusAPI | None = None
        self._config_manager: ConfigurationManager | None = None

        self._event_manager = MyDolphinPlusEventManager(self._hass, super().update)

    @property
    def api(self) -> MyDolphinPlusAPI:
        return self._api

    @property
    def event_manager(self) -> MyDolphinPlusEventManager:
        return self._event_manager

    @property
    def config_data(self) -> ConfigData:
        return self._config_manager.get(self.entry_id)

    async def async_send_heartbeat(self):
        """ Must be implemented to be able to send heartbeat to API """
        # await self._ws.async_send_heartbeat()

    async def async_component_initialize(self, entry: ConfigEntry):
        try:
            self._config_manager = async_get_configuration_manager(self._hass)
            await self._config_manager.load(entry)

            await self.event_manager.initialize()

            self._api = MyDolphinPlusAPI(self._hass, self.config_data)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_component_initialize, error: {ex}, line: {line_number}")

    async def async_initialize_data_providers(self, entry: ConfigEntry | None = None):
        await self.api.initialize(self.config_data)

        if self.api.status == ConnectivityStatus.Connected:
            print(self.api.status)
            # ws_version = await self.api.get_socket_io_version()

    async def async_stop_data_providers(self):
        self.event_manager.terminate()
        await self.api.terminate()
        # await self.ws.terminate()

    async def async_update_data_providers(self):
        try:
            await self._api.async_update()

            self.device_manager.generate_device(f"{self.entry_title}", "System")
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_update_data_providers, Error: {ex}, Line: {line_number}")

    def load_entities(self):
        ## TODO Create Entities
        _LOGGER.debug("Loading entities")
        #entity_name = f"{self.entry_title} {monitor.name}"
        _LOGGER.debug("{self.api.payload}")

    def _load_binary_sensor_entity(
            self,
            sensor_type: BinarySensorDeviceClass,
            device: str
    ):
        try:
            entity_name = f"{self.entry_title} REPLACE {sensor_type.capitalize()}"

            state = STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            # for attr in BINARY_SENSOR_ATTRIBUTES:
            #    if attr in event_state:
            #        attributes[attr] = event_state.get(attr)

            entity = self.entity_manager.get(DOMAIN_BINARY_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = "ID of Entity"
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.binary_sensor_device_class = sensor_type
                entity.domain = DOMAIN_BINARY_SENSOR

            data = {
                "state": (entity.state, str(state)),
                "attributes": (entity.attributes, attributes),
                "device_name": (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity.state = state
                entity.attributes = attributes
                entity.device_name = device

                entity.set_created_or_updated(created)

            self.entity_manager.set(entity)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load binary sensor"
            )

    @staticmethod
    def log_exception(ex, message):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"{message}, Error: {str(ex)}, Line: {line_number}")
