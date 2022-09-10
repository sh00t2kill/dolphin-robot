"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/mydolphin_plus/
"""
from __future__ import annotations

import datetime
import logging
import sys

from cryptography.fernet import InvalidToken

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_registry import EntityRegistry, async_get
from homeassistant.helpers.event import async_track_time_interval

from ...core.helpers.const import *
from ...core.managers.device_manager import DeviceManager
from ...core.managers.entity_manager import EntityManager
from ...core.managers.storage_manager import StorageManager

_LOGGER = logging.getLogger(__name__)


class HomeAssistantManager:
    def __init__(self,
                 hass: HomeAssistant,
                 scan_interval: datetime.timedelta,
                 heartbeat_interval: datetime.timedelta | None = None
                 ):

        self._hass = hass

        self._is_initialized = False
        self._is_updating = False
        self._scan_interval = scan_interval
        self._heartbeat_interval = heartbeat_interval

        self._entity_registry = None

        self._entry: ConfigEntry | None = None

        self._storage_manager = StorageManager(self._hass)
        self._entity_manager = EntityManager(self._hass, self)
        self._device_manager = DeviceManager(self._hass, self)

        self._entity_registry = async_get(self._hass)

        self._async_track_time_handlers = []
        self._last_heartbeat = None

        def _send_heartbeat(internal_now):
            self._last_heartbeat = internal_now

            self._hass.async_create_task(self.async_send_heartbeat())

        self._send_heartbeat = _send_heartbeat

    @property
    def entity_manager(self) -> EntityManager:
        return self._entity_manager

    @property
    def device_manager(self) -> DeviceManager:
        return self._device_manager

    @property
    def entity_registry(self) -> EntityRegistry:
        return self._entity_registry

    @property
    def storage_manager(self) -> StorageManager:
        return self._storage_manager

    @property
    def entry_id(self) -> str:
        return self._entry.entry_id

    @property
    def entry_title(self) -> str:
        return self._entry.title

    async def async_component_initialize(self, entry: ConfigEntry):
        """ Component initialization """
        pass

    async def async_send_heartbeat(self):
        """ Must be implemented to be able to send heartbeat to API """
        pass

    async def async_initialize_data_providers(self, entry: ConfigEntry | None = None):
        """ Must be implemented to be able to send heartbeat to API """
        pass

    async def async_stop_data_providers(self):
        """ Must be implemented to be able to send heartbeat to API """
        pass

    async def async_update_data_providers(self):
        """ Must be implemented to be able to send heartbeat to API """
        pass

    def load_entities(self):
        """ Must be implemented to be able to send heartbeat to API """
        pass

    async def async_init(self, entry: ConfigEntry):
        try:
            self._entry = entry

            await self.async_component_initialize(entry)

            self._hass.loop.create_task(self._async_load_platforms())

        except InvalidToken:
            error_message = "Encryption key got corrupted, please remove the integration and re-add it"

            _LOGGER.error(error_message)

            data = await self._storage_manager.async_load_from_store()
            data.key = None

            await self._storage_manager.async_save_to_store(data)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_init, error: {ex}, line: {line_number}")

    async def _async_load_platforms(self):
        load = self._hass.config_entries.async_forward_entry_setup

        for domain in PLATFORMS:
            await load(self._entry, domain)

        self._is_initialized = True

        await self.async_update_entry()

    def _update_entities(self, now):
        self._hass.async_create_task(self.async_update(now))

    async def async_update_entry(self, entry: ConfigEntry | None = None):
        entry_changed = entry is not None

        if entry_changed:
            self._entry = entry

            _LOGGER.info(f"Handling ConfigEntry load: {entry.as_dict()}")

        else:
            entry = self._entry

            remove_async_track_time = async_track_time_interval(
                self._hass, self._update_entities, self._scan_interval
            )

            self._async_track_time_handlers.append(remove_async_track_time)

            if self._heartbeat_interval is not None:
                remove_async_heartbeat_track_time = async_track_time_interval(
                    self._hass, self._send_heartbeat, self._heartbeat_interval
                )

                self._async_track_time_handlers.append(remove_async_heartbeat_track_time)

            _LOGGER.info(f"Handling ConfigEntry change: {entry.as_dict()}")

        await self.async_initialize_data_providers(entry)

    async def async_unload(self):
        _LOGGER.info(f"HA was stopped")

        for handler in self._async_track_time_handlers:
            if handler is not None:
                handler()

        self._async_track_time_handlers.clear()

        await self.async_stop_data_providers()

    async def async_remove(self, entry: ConfigEntry):
        _LOGGER.info(f"Removing current integration - {entry.title}")

        await self.async_unload()

        unload = self._hass.config_entries.async_forward_entry_unload

        for domain in PLATFORMS:
            await unload(entry, domain)

        await self._device_manager.async_remove()

        _LOGGER.info(f"Current integration ({entry.title}) removed")

    def update(self):
        self.load_entities()

        self.entity_manager.update()

        self._hass.async_create_task(self.dispatch_all())

    async def async_update(self, event_time):
        if not self._is_initialized:
            _LOGGER.info(f"NOT INITIALIZED - Failed updating @{event_time}")
            return

        try:
            if self._is_updating:
                _LOGGER.debug(f"Skip updating @{event_time}")
                return

            _LOGGER.debug(f"Updating @{event_time}")

            self._is_updating = True

            await self.async_update_data_providers()

            self.update()
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_update, Error: {ex}, Line: {line_number}")

        self._is_updating = False

    async def delete_entity(self, domain, name):
        try:
            available_domains = self.entity_manager.available_domains
            domain_data = self.entity_manager.get_domain_data(domain)

            entity = domain_data.get_entity(name)
            device_name = entity.device_name
            unique_id = entity.unique_id

            domain_data.delete_entity(name)

            device_in_use = False

            for domain_name in available_domains:
                if domain_name != domain:
                    domain_data = self.entity_manager.get_domain_data(domain_name)

                    if device_name in domain_data.entities:
                        device_in_use = True
                        break

            entity_id = self.entity_registry.async_get_entity_id(
                domain, DOMAIN, unique_id
            )
            self.entity_registry.async_remove(entity_id)

            if not device_in_use:
                await self.device_manager.delete_device(device_name)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to delete_entity, Error: {ex}, Line: {line_number}")

    async def dispatch_all(self):
        if not self._is_initialized:
            _LOGGER.info("NOT INITIALIZED - Failed discovering components")
            return

        for domain in PLATFORMS:
            signal = PLATFORMS.get(domain)

            async_dispatcher_send(self._hass, signal)
