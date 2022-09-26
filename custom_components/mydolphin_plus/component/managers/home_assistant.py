"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/mydolphin_plus/
"""
from __future__ import annotations

import calendar
import logging
import sys

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
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

    async def async_stop_data_providers(self):
        self.event_manager.terminate()
        await self.api.terminate()

    async def async_update_data_providers(self):
        try:
            await self._api.async_update()

            data = self._api.data
            name = data.get("Robot Name")
            model = data.get("Product Name")

            self.device_manager.generate_device(name, model)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_update_data_providers, Error: {ex}, Line: {line_number}")

    def load_entities(self):
        data = self._api.data
        name = data.get("Robot Name")

        self._load_select_cleaning_mode(name, data)
        self._load_select_led_mode(name, data)
        self._load_remote(name, data)
        self._load_binary_sensor_status(name, data)
        self._load_binary_sensor_filter_status(name, data)
        self._load_sensor_connection_type(name, data)
        self._load_sensor_cleaning_time(name, data)
        self._load_sensor_cleaning_time_left(name, data)
        self._load_switch_power(name, data)
        self._load_switch_led_enabled(name, data)

        delay_settings = data.get("delay", {})
        self._load_binary_sensor_schedules(name, "delay", delay_settings)

        weekly_settings = data.get("weeklySettings", {})

        for day in list(calendar.day_name):
            day_data = weekly_settings.get(day, {})

            self._load_binary_sensor_schedules(name, day, day_data)

    def _load_select_cleaning_mode(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Cleaning Mode"

        try:
            state = STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            # for attr in BINARY_SENSOR_ATTRIBUTES:
            #    if attr in event_state:
            #        attributes[attr] = event_state.get(attr)

            entity = self.entity_manager.get(DOMAIN_SELECT, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_SELECT

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
                ex, f"Failed to load {DOMAIN_SELECT}: {entity_name}"
            )

    def _load_select_led_mode(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Led Mode"

        try:
            state = STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            # for attr in BINARY_SENSOR_ATTRIBUTES:
            #    if attr in event_state:
            #        attributes[attr] = event_state.get(attr)

            entity = self.entity_manager.get(DOMAIN_SELECT, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_SELECT

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
                ex, f"Failed to load {DOMAIN_SELECT}: {entity_name}"
            )

    def _load_remote(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Remote"

        try:
            state = STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            # for attr in BINARY_SENSOR_ATTRIBUTES:
            #    if attr in event_state:
            #        attributes[attr] = event_state.get(attr)

            entity = self.entity_manager.get(DOMAIN_REMOTE, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_REMOTE

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
                ex, f"Failed to load {DOMAIN_REMOTE}: {entity_name}"
            )

    def _load_binary_sensor_status(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Status"

        try:
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

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_BINARY_SENSOR
                entity.binary_sensor_device_class = BinarySensorDeviceClass.CONNECTIVITY

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
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_binary_sensor_schedules(
            self,
            device: str,
            day: str,
            data: dict
    ):
        entity_name = f"{device} Schedule {day}"

        try:
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

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_BINARY_SENSOR
                entity.binary_sensor_device_class = BinarySensorDeviceClass.OCCUPANCY

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
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_binary_sensor_filter_status(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Filter Status"

        try:
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

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_BINARY_SENSOR
                entity.binary_sensor_device_class = BinarySensorDeviceClass.OCCUPANCY

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
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_sensor_connection_type(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Connection Type"

        try:
            state = STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            # for attr in BINARY_SENSOR_ATTRIBUTES:
            #    if attr in event_state:
            #        attributes[attr] = event_state.get(attr)

            entity = self.entity_manager.get(DOMAIN_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_SENSOR
                entity.sensor_device_class = SensorDeviceClass.POWER
                entity.sensor_state_class = SensorStateClass.MEASUREMENT

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
                ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}"
            )

    def _load_sensor_cleaning_time(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Cleaning Time"

        try:
            state = STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            # for attr in BINARY_SENSOR_ATTRIBUTES:
            #    if attr in event_state:
            #        attributes[attr] = event_state.get(attr)

            entity = self.entity_manager.get(DOMAIN_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_SENSOR
                entity.sensor_device_class = SensorDeviceClass.DURATION
                entity.sensor_state_class = SensorStateClass.MEASUREMENT

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
                ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}"
            )

    def _load_sensor_cleaning_time_left(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Filter Status"

        try:
            state = STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            # for attr in BINARY_SENSOR_ATTRIBUTES:
            #    if attr in event_state:
            #        attributes[attr] = event_state.get(attr)

            entity = self.entity_manager.get(DOMAIN_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_SENSOR
                entity.sensor_device_class = SensorDeviceClass.DURATION
                entity.sensor_state_class = SensorStateClass.MEASUREMENT

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
                ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}"
            )

    def _load_switch_power(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Power"

        try:
            state = STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            # for attr in BINARY_SENSOR_ATTRIBUTES:
            #    if attr in event_state:
            #        attributes[attr] = event_state.get(attr)

            entity = self.entity_manager.get(DOMAIN_SWITCH, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_SWITCH

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
                ex, f"Failed to load {DOMAIN_SWITCH}: {entity_name}"
            )

    def _load_switch_led_enabled(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Led"

        try:
            state = STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            # for attr in BINARY_SENSOR_ATTRIBUTES:
            #    if attr in event_state:
            #        attributes[attr] = event_state.get(attr)

            entity = self.entity_manager.get(DOMAIN_SWITCH, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_SWITCH

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
                ex, f"Failed to load {DOMAIN_SWITCH}: {entity_name}"
            )

    async def set_cleaning_mode(self, cleaning_mode):
        await self.api.set_cleaning_mode(cleaning_mode)

    async def set_delay(self,
                        enabled: bool | None = False,
                        mode: str | None = "all",
                        hours: int | None = 255,
                        minutes: int | None = 255):
        await self.api.set_delay(enabled, mode, hours, minutes)

    async def set_schedule(self,
                           day: str,
                           enabled: bool | None = False,
                           mode: str | None = "all",
                           hours: int | None = 255,
                           minutes: int | None = 255):
        await self.api.set_schedule(day, enabled, mode, hours, minutes)

    async def set_led_mode(self, mode: int):
        await self.api.set_led_mode(mode)

    async def set_led_intensity(self, intensity: int):
        await self.api.set_led_intensity(intensity)

    async def set_led_enabled(self, is_enabled: bool):
        await self.api.set_led_enabled(is_enabled)

    async def drive(self, direction: str):
        await self.api.drive(direction)

    async def set_power_state(self, is_on: bool):
        await self.api.set_power_state(is_on)

    @staticmethod
    def log_exception(ex, message):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"{message}, Error: {str(ex)}, Line: {line_number}")
