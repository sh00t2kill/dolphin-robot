"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/mydolphin_plus/
"""
from __future__ import annotations

import datetime
import logging
import sys

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, EntityDescription

from ...component.api.mydolphin_plus_api import MyDolphinPlusAPI
from ...component.helpers.const import *
from ...configuration.managers.configuration_manager import (
    ConfigurationManager,
    async_get_configuration_manager,
)
from ...configuration.models.config_data import ConfigData
from ...core.managers.home_assistant import HomeAssistantManager
from ...core.models.select_description import SelectDescription
from ..helpers.common import get_cleaning_mode_name, get_date_time_from_timestamp
from ..helpers.enums import ConnectivityStatus

_LOGGER = logging.getLogger(__name__)


class MyDolphinPlusHomeAssistantManager(HomeAssistantManager):
    def __init__(self, hass: HomeAssistant):
        super().__init__(hass, SCAN_INTERVAL, HEARTBEAT_INTERVAL_SECONDS)

        self._api: MyDolphinPlusAPI | None = None
        self._config_manager: ConfigurationManager | None = None

    @property
    def api(self) -> MyDolphinPlusAPI:
        return self._api

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

            self._api = MyDolphinPlusAPI(self._hass, self.config_data, super().update)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_component_initialize, error: {ex}, line: {line_number}")

    async def async_initialize_data_providers(self, entry: ConfigEntry | None = None):
        await self.api.initialize(self.config_data)

        if self.api.status == ConnectivityStatus.Connected:
            await self.async_update(datetime.datetime.now())

    async def async_stop_data_providers(self):
        await self.api.terminate()

    async def async_update_data_providers(self):
        try:
            await self._api.async_update()

            self.device_manager.generate_device(self.api.data)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_update_data_providers, Error: {ex}, Line: {line_number}")

    def load_entities(self):
        data = self._api.data
        name = data.get("Robot Name")

        if name is None:
            return

        # Main Entity
        self._load_vacuum(name, data)

        # LED Settings
        self._load_select_led_mode(name, data)
        self._load_light_led_enabled(name, data)

        # Sensors
        self._load_binary_sensor_filter_status(name, data)
        self._load_sensor_cleaning_time(name, data)
        self._load_sensor_cleaning_time_left(name, data)
        self._load_sensor_broker_status(name)

        # Scheduling Sensors
        features = data.get("featureEn", {})
        self._load_binary_sensor_weekly_timer(name, features)
        delay_settings = data.get("delay", {})
        self._load_binary_sensor_schedules(name, "delay", delay_settings)

        weekly_settings = data.get("weeklySettings", {})

        for day in list(calendar.day_name):
            day_data = weekly_settings.get(day.lower(), {})
            self._load_binary_sensor_schedules(name, day, day_data)

    def _load_select_led_mode(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Led Mode"

        try:
            led = data.get("led", {})
            led_mode = led.get("ledMode", 1)
            led_intensity = led.get("ledIntensity", 80)
            led_enable = led.get("ledEnable", False)

            state = led_mode
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                CONF_ENABLED: led_enable,
                ATTR_INTENSITY: led_intensity
            }

            entity = self.entity_manager.get(DOMAIN_SELECT, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_SELECT

            data = {
                CONF_STATE: (str(entity.state), str(state)),
                CONF_DEVICE_ID: (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity_description = SelectDescription(
                    key=ATTR_LED_MODE,
                    name=ATTR_LED_MODE,
                    icon=LED_MODE_ICON_DEFAULT,
                    device_class=f"{DOMAIN}__{ATTR_LED_MODE}",
                    options=tuple(ICON_LED_MODES.keys()),
                    entity_category=EntityCategory.CONFIG,
                )

                entity.state = state
                entity.attributes = attributes
                entity.device_name = device
                entity.entity_description = entity_description
                entity.action = self.set_led_mode
                entity.icon = ICON_LED_MODES.get(state, LED_MODE_ICON_DEFAULT)

                entity.set_created_or_updated(created)

            self.entity_manager.set(entity)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load {DOMAIN_SELECT}: {entity_name}"
            )

    def _load_binary_sensor_weekly_timer(
            self,
            device: str,
            data: dict
    ):
        weekly_timer = data.get("weeklyTimer", {})
        status = weekly_timer.get(ATTR_STATUS, "disabled")

        is_enabled = status == "enable"
        entity_name = f"{device} Weekly Schedule Enabled"
        try:
            state = STATE_ON if is_enabled else STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_STATUS: status
            }

            entity = self.entity_manager.get(DOMAIN_BINARY_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = "mdi:calendar-check" if is_enabled else "mdi:calendar-remove"
                entity.domain = DOMAIN_BINARY_SENSOR

            data = {
                CONF_STATE: (str(entity.state), str(state)),
                CONF_ATTRIBUTES: (entity.attributes, attributes),
                CONF_DEVICE_ID: (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity_description = EntityDescription(
                    key=entity.id,
                    name=entity.name,
                    icon=entity.icon
                )

                entity.state = state
                entity.attributes = attributes
                entity.device_name = device
                entity.entity_description = entity_description

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
        is_enabled = data.get("isEnabled", False)
        cleaning_mode = data.get("cleaningMode", {})
        job_time = data.get("time", {})

        mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
        mode_name = get_cleaning_mode_name(mode)
        hours = job_time.get("hours", 255)
        minutes = job_time.get("minutes", 255)

        entity_name = f"{device} Schedule {day.capitalize()}"

        job_start_time = None
        if hours < 255 and minutes < 255:
            job_start_time = str(datetime.timedelta(hours=hours, minutes=minutes))

        try:
            state = STATE_ON if is_enabled else STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: mode_name,
                ATTR_START_TIME: job_start_time
            }

            entity = self.entity_manager.get(DOMAIN_BINARY_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = "mdi:calendar-check" if is_enabled else "mdi:calendar-remove"
                entity.domain = DOMAIN_BINARY_SENSOR

            data = {
                CONF_STATE: (str(entity.state), str(state)),
                CONF_ATTRIBUTES: (entity.attributes, attributes),
                CONF_DEVICE_ID: (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity_description = EntityDescription(
                    key=entity.id,
                    name=entity.name,
                    icon=entity.icon
                )

                entity.state = state
                entity.attributes = attributes
                entity.device_name = device
                entity.entity_description = entity_description

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
            filter_bag_indication = data.get("filterBagIndication", {})
            filter_state = filter_bag_indication.get(CONF_STATE, 0)
            reset_fbi = filter_bag_indication.get("resetFBI", 0)

            state = STATE_ON if filter_state != 0 else STATE_OFF
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_RESET_FBI: reset_fbi,
                ATTR_STATUS: filter_state
            }

            entity = self.entity_manager.get(DOMAIN_BINARY_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = "mdi:tray" if state else "mdi:tray-alert"
                entity.domain = DOMAIN_BINARY_SENSOR
                entity.binary_sensor_device_class = BinarySensorDeviceClass.OCCUPANCY

            data = {
                CONF_STATE: (str(entity.state), str(state)),
                CONF_ATTRIBUTES: (entity.attributes, attributes),
                CONF_DEVICE_ID: (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity_description = EntityDescription(
                    key=entity.id,
                    name=entity.name,
                    icon=entity.icon
                )

                entity.state = state
                entity.attributes = attributes
                entity.device_name = device
                entity.entity_description = entity_description

                entity.set_created_or_updated(created)

            self.entity_manager.set(entity)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_sensor_cleaning_time(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Cleaning Time"

        try:
            cycle_info = data.get("cycleInfo", {})
            cleaning_mode = cycle_info.get("cleaningMode", {})
            mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
            mode_name = get_cleaning_mode_name(mode)

            cycle_time_minutes = cleaning_mode.get("cycleTime", 0)
            cycle_start_time_ts = cycle_info.get("cycleStartTime", 0)
            cycle_start_time = get_date_time_from_timestamp(cycle_start_time_ts)
            cycle_time = str(datetime.timedelta(minutes=cycle_time_minutes))

            state = cycle_time
            state_parts = state.split(":")
            state_hours = state_parts[0]

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: mode_name,
                ATTR_START_TIME: cycle_start_time
            }

            entity = self.entity_manager.get(DOMAIN_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = CLOCK_HOURS_ICONS.get(state_hours, "mdi:clock-time-twelve")
                entity.domain = DOMAIN_SENSOR
                entity.sensor_device_class = SensorDeviceClass.DURATION
                entity.sensor_state_class = SensorStateClass.MEASUREMENT

            data = {
                CONF_STATE: (str(entity.state), str(state)),
                CONF_ATTRIBUTES: (entity.attributes, attributes),
                CONF_DEVICE_ID: (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity_description = EntityDescription(
                    key=entity.id,
                    name=entity.name,
                    icon=entity.icon
                )

                entity.state = state
                entity.attributes = attributes
                entity.device_name = device
                entity.entity_description = entity_description

                entity.set_created_or_updated(created)

            self.entity_manager.set(entity)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}"
            )

    def _load_sensor_broker_status(self, device: str):
        entity_name = f"{device} AWS Broker"

        try:
            state = str(self.api.awsiot_client_status)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name
            }

            entity = self.entity_manager.get(DOMAIN_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.domain = DOMAIN_SENSOR
                entity.icon = "mdi:aws"
                entity.sensor_state_class = SensorStateClass.MEASUREMENT

            data = {
                CONF_STATE: (str(entity.state), str(state)),
                CONF_ATTRIBUTES: (entity.attributes, attributes),
                CONF_DEVICE_ID: (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity_description = EntityDescription(
                    key=entity.id,
                    name=entity.name,
                    icon=entity.icon
                )

                entity.state = state
                entity.attributes = attributes
                entity.device_name = device
                entity.entity_description = entity_description

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
        entity_name = f"{device} Time Left"

        try:
            cycle_info = data.get("cycleInfo", {})
            cleaning_mode = cycle_info.get("cleaningMode", {})
            mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
            mode_name = get_cleaning_mode_name(mode)

            cycle_time = cleaning_mode.get("cycleTime", 0)
            cycle_time_in_seconds = cycle_time * 60

            cycle_start_time_ts = cycle_info.get("cycleStartTime", 0)
            cycle_start_time = get_date_time_from_timestamp(cycle_start_time_ts)

            now_ts = datetime.datetime.now().timestamp()
            now = get_date_time_from_timestamp(now_ts)

            expected_cycle_end_time_ts = cycle_time_in_seconds + cycle_start_time_ts
            expected_cycle_end_time = get_date_time_from_timestamp(expected_cycle_end_time_ts)

            seconds_left = 0
            if expected_cycle_end_time_ts > now_ts:
                # still working
                seconds_left = expected_cycle_end_time_ts - now_ts

            state = str(datetime.timedelta(seconds=seconds_left))

            state_parts = state.split(":")
            state_hours = state_parts[0]

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: mode_name,
                ATTR_START_TIME: cycle_start_time,
                ATTR_EXPECTED_END_TIME: expected_cycle_end_time
            }

            entity = self.entity_manager.get(DOMAIN_SENSOR, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = CLOCK_HOURS_ICONS.get(state_hours, "mdi:clock-time-twelve")
                entity.domain = DOMAIN_SENSOR
                entity.sensor_device_class = SensorDeviceClass.DURATION
                entity.sensor_state_class = SensorStateClass.MEASUREMENT

            data = {
                CONF_STATE: (str(entity.state), str(state)),
                CONF_ATTRIBUTES: (entity.attributes, attributes),
                CONF_DEVICE_ID: (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity_description = EntityDescription(
                    key=entity.id,
                    name=entity.name,
                    icon=entity.icon
                )

                entity.state = state
                entity.attributes = attributes
                entity.device_name = device
                entity.entity_description = entity_description

                entity.set_created_or_updated(created)

            self.entity_manager.set(entity)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}"
            )

    def _load_light_led_enabled(
            self,
            device: str,
            data: dict
    ):
        entity_name = f"{device} Led"

        try:
            led = data.get("led", {})
            led_mode = led.get("ledMode", 1)
            led_intensity = led.get("ledIntensity", 80)
            led_enable = led.get("ledEnable", False)

            state = led_enable
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: led_mode,
                ATTR_INTENSITY: led_intensity
            }

            entity = self.entity_manager.get(DOMAIN_LIGHT, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_LIGHT

            data = {
                CONF_STATE: (str(entity.state), str(state)),
                CONF_ATTRIBUTES: (entity.attributes, attributes),
                CONF_DEVICE_ID: (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity.state = state
                entity.attributes = attributes
                entity.device_name = device
                entity.action = self.set_led_enabled

                entity.set_created_or_updated(created)

            self.entity_manager.set(entity)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load {DOMAIN_LIGHT}: {entity_name}"
            )

    def _load_vacuum(
            self,
            device: str,
            data: dict
    ):
        entity_name = device

        try:
            details = self.get_system_status_details(data)

            debug = data.get("debug", {})
            wifi_rssi = debug.get("WIFI_RSSI", 0)

            wifi = data.get("wifi", {})
            net_name = wifi.get("netName")

            state = details.get(CONF_STATE)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_RSSI: wifi_rssi,
                ATTR_NETWORK_NAME: net_name
            }

            for key in details:
                attributes[key] = details.get(key)

            entity = self.entity_manager.get(DOMAIN_VACUUM, entity_name)
            created = entity is None

            if created:
                entity = self.entity_manager.get_empty_entity(self.entry_id)

                entity.id = entity_name
                entity.name = entity_name
                entity.icon = DEFAULT_ICON
                entity.domain = DOMAIN_VACUUM

            data = {
                CONF_STATE: (str(entity.state), str(state)),
                CONF_ATTRIBUTES: (entity.attributes, attributes),
                CONF_DEVICE_ID: (entity.device_name, device),
            }

            if created or self.entity_manager.compare_data(entity, data):
                entity.state = state
                entity.attributes = attributes
                entity.device_name = device
                entity.action = self.set_led_enabled

                entity.set_created_or_updated(created)

            self.entity_manager.set(entity)

        except Exception as ex:
            self.log_exception(
                ex, f"Failed to load {DOMAIN_VACUUM}: {entity_name}"
            )

    async def set_cleaning_mode(self, cleaning_mode):
        await self.api.set_cleaning_mode(cleaning_mode)

    async def set_delay(self,
                        enabled: bool | None = False,
                        mode: str | None = CLEANING_MODE_REGULAR,
                        job_time: str | None = None):
        await self.api.set_delay(enabled, mode, job_time)

    async def set_schedule(self,
                           day: str,
                           enabled: bool | None = False,
                           mode: str | None = CLEANING_MODE_REGULAR,
                           job_time: str | None = None):
        await self.api.set_schedule(day, enabled, mode, job_time)

    async def set_led_mode(self, mode: int):
        await self.api.set_led_mode(mode)

    async def set_led_intensity(self, intensity: int):
        await self.api.set_led_intensity(intensity)

    async def set_led_enabled(self, is_enabled: bool):
        await self.api.set_led_enabled(is_enabled)

    async def navigate(self, direction: str):
        await self.api.navigate(direction)

    async def pickup(self):
        await self.api.pickup()

    async def set_power_state(self, is_on: bool):
        await self.api.set_power_state(is_on)

    @staticmethod
    def log_exception(ex, message):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"{message}, Error: {str(ex)}, Line: {line_number}")

    @staticmethod
    def get_system_status_details(data: dict):
        system_state = data.get("systemState", {})
        pws_state = system_state.get("pwsState", "off")
        robot_state = system_state.get("robotState", "off")
        robot_type = system_state.get("robotType")
        is_busy = system_state.get("isBusy", False)
        turn_on_count = system_state.get("rTurnOnCount", 0)
        time_zone = system_state.get("timeZone", 0)
        time_zone_name = system_state.get("timeZoneName", "UTC")

        pws_on = pws_state in [PWS_STATE_ON]
        pws_off = pws_state in [PWS_STATE_OFF, PWS_STATE_HOLD_DELAY, PWS_STATE_HOLD_WEEKLY]
        pws_programming = pws_state == PWS_STATE_PROGRAMMING

        robot_on = robot_state not in [ROBOT_STATE_INIT, ROBOT_STATE_SCANNING, ROBOT_STATE_NOT_CONNECTED]
        robot_off = robot_state not in [ROBOT_STATE_FINISHED, ROBOT_STATE_FAULT, ROBOT_STATE_NOT_CONNECTED]
        robot_programming = robot_state == PWS_STATE_PROGRAMMING

        if pws_off and robot_off:
            calculated_state = PWS_STATE_OFF
        elif pws_programming and robot_programming:
            calculated_state = PWS_STATE_PROGRAMMING
        elif pws_state == PWS_STATE_ON and robot_state == ROBOT_STATE_NOT_CONNECTED:
            calculated_state = ROBOT_STATE_NOT_CONNECTED
        elif (pws_on and robot_on) or (pws_programming and not robot_programming):
            calculated_state = PWS_STATE_ON
        else:
            state_description = f"pwsState: {pws_state}, robotState: {robot_state}"
            _LOGGER.warning(f"Unhandled mapping, state will be set according to pws_state, {state_description}")

            calculated_state = pws_state

        state = CALCULATED_STATES.get(calculated_state, "Unmapped")

        result = {
            "Calculated Status": calculated_state,
            "PWS Status": pws_state,
            "Robot Status": robot_state,
            "Robot Type": robot_type,
            "Busy": is_busy,
            "Turn on count": turn_on_count,
            "Time Zone": f"{time_zone_name} ({time_zone})",
            CONF_STATE: state
        }

        return result
