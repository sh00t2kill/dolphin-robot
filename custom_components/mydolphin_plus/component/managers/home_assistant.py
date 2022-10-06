"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/mydolphin_plus/
"""
from __future__ import annotations

from asyncio import sleep
import datetime
import logging
import sys
from typing import Any

from voluptuous import MultipleInvalid

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.components.light import LightEntityDescription
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from ...configuration.managers.configuration_manager import ConfigurationManager
from ...configuration.models.config_data import ConfigData
from ...core.helpers.enums import ConnectivityStatus
from ...core.managers.home_assistant import HomeAssistantManager
from ...core.models.entity_data import EntityData
from ...core.models.select_description import SelectDescription
from ...core.models.vacuum_description import VacuumDescription
from ..api.mydolphin_plus_api import IntegrationAPI
from ..api.storage_api import StorageAPI
from ..helpers.common import get_cleaning_mode_name, get_date_time_from_timestamp
from ..helpers.const import *

_LOGGER = logging.getLogger(__name__)


class MyDolphinPlusHomeAssistantManager(HomeAssistantManager):
    def __init__(self, hass: HomeAssistant):
        super().__init__(hass, SCAN_INTERVAL)

        self._api: IntegrationAPI = IntegrationAPI(self._hass, self._api_data_changed, self._api_status_changed)
        self._config_manager: ConfigurationManager | None = None
        self._storage_api = StorageAPI(self._hass)

        self._robot_actions: dict[str, [dict[str, Any] | list[Any] | None]] = {
            SERVICE_NAVIGATE: self._command_navigate,
            SERVICE_DAILY_SCHEDULE: self._command_set_schedule,
            SERVICE_DELAYED_CLEAN: self._command_set_delay,
        }

    @property
    def api(self) -> IntegrationAPI:
        return self._api

    @property
    def storage_api(self) -> StorageAPI:
        return self._storage_api

    @property
    def config_data(self) -> ConfigData:
        return self._config_manager.get(self.entry_id)

    async def async_component_initialize(self, entry: ConfigEntry):
        try:
            self._config_manager = ConfigurationManager(self._hass, self.api)
            await self._config_manager.load(entry)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_component_initialize, error: {ex}, line: {line_number}")

    async def async_initialize_data_providers(self, entry: ConfigEntry | None = None):
        await self.storage_api.initialize()
        await self.api.initialize(self.config_data)

    async def async_stop_data_providers(self):
        await self.api.terminate()

    async def async_update_data_providers(self):
        try:
            await self._api.async_update()
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to async_update_data_providers, Error: {ex}, Line: {line_number}")

    def load_devices(self):
        try:
            data = self._api.data
            device_name = data.get(DATA_ROBOT_NAME)
            model = data.get("Product Description")
            versions = data.get("versions", {})
            pws_version = versions.get("pwsVersion", {})
            sw_version = pws_version.get("pwsSwVersion")
            hw_version = pws_version.get("pwsHwVersion")

            device_info = {
                "identifiers": {(DEFAULT_NAME, device_name)},
                "name": device_name,
                "manufacturer": MANUFACTURER,
                "model": model,
                "sw_version": sw_version,
                "hw_version": hw_version
            }

            self.device_manager.set(device_name, device_info)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to load devices, Error: {ex}, Line: {line_number}")

    def load_entities(self):
        data = self._api.data
        name = data.get(DATA_ROBOT_NAME)

        if name is None:
            return

        # Main Entity
        self._load_vacuum(name, data)

        # LED Settings
        self._load_select_led_mode(name, data)
        self._load_light_led_enabled(name, data)

        # Sensors
        self._load_sensor_filter_status(name, data)
        self._load_sensor_cycle_time(name, data)
        self._load_sensor_cycle_time_left(name, data)
        self._load_binary_sensor_broker_status(name)

        # Scheduling Sensors
        self._load_binary_sensor_weekly_timer(name, data)

        delay_settings = data.get(DATA_SECTION_DELAY, {})
        self._load_binary_sensor_schedules(name, DATA_SECTION_DELAY, delay_settings)

        weekly_settings = data.get(DATA_SECTION_WEEKLY_SETTINGS, {})

        for day in list(calendar.day_name):
            day_data = weekly_settings.get(day.lower(), {})
            self._load_binary_sensor_schedules(name, day, day_data)

    def _load_select_led_mode(
            self,
            device_name: str,
            data: dict
    ):
        entity_name = f"{device_name} Led Mode"

        try:
            led = data.get(DATA_SECTION_LED, {})
            led_mode = led.get(DATA_LED_MODE, LED_MODE_BLINKING)
            led_intensity = led.get(DATA_LED_INTENSITY, DEFAULT_LED_INTENSITY)
            led_enable = led.get(DATA_LED_ENABLE, DEFAULT_ENABLE)

            state = led_mode
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                CONF_ENABLED: led_enable,
                ATTR_INTENSITY: led_intensity
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SELECT, entity_name)

            entity_description = SelectDescription(
                key=unique_id,
                name=entity_name,
                icon=ICON_LED_MODES.get(state, LED_MODE_ICON_DEFAULT),
                device_class=f"{DOMAIN}__{ATTR_LED_MODE}",
                options=tuple(ICON_LED_MODES.keys()),
                entity_category=EntityCategory.CONFIG,
            )

            self.entity_manager.set_entity(DOMAIN_SELECT,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           device_name,
                                           entity_description)

            self.set_action(unique_id, ACTION_CORE_ENTITY_SELECT_OPTION, self._set_led_mode)

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_SELECT}: {entity_name}"
            )

    def _load_binary_sensor_weekly_timer(
            self,
            device_name: str,
            data: dict
    ):
        entity_name = f"{device_name} Weekly Schedule"
        try:
            features = data.get(DATA_SECTION_FEATURE, {})

            weekly_timer = features.get(DATA_FEATURE_WEEKLY_TIMER, {})
            status = weekly_timer.get(ATTR_STATUS, ATTR_DISABLED)

            is_enabled = status == ATTR_ENABLE

            state = STATE_ON if is_enabled else STATE_OFF

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_STATUS: status
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_BINARY_SENSOR, entity_name)

            entity_description = BinarySensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon="mdi:calendar-check" if is_enabled else "mdi:calendar-remove"
            )

            self.entity_manager.set_entity(DOMAIN_BINARY_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           device_name,
                                           entity_description)

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_binary_sensor_schedules(
            self,
            device_name: str,
            day: str,
            data: dict
    ):
        is_enabled = data.get(DATA_SCHEDULE_IS_ENABLED, DEFAULT_ENABLE)
        state = STATE_ON if is_enabled else STATE_OFF
        cleaning_mode = data.get(DATA_SCHEDULE_CLEANING_MODE, {})
        job_time = data.get(DATA_SCHEDULE_TIME, {})

        mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
        mode_name = get_cleaning_mode_name(mode)
        hours = job_time.get(DATA_SCHEDULE_TIME_HOURS, DEFAULT_TIME_PART)
        minutes = job_time.get(DATA_SCHEDULE_TIME_MINUTES, DEFAULT_TIME_PART)

        entity_name = f"{device_name} Schedule {day.capitalize()}"

        job_start_time = None
        if hours < DEFAULT_TIME_PART and minutes < DEFAULT_TIME_PART:
            job_start_time = str(datetime.timedelta(hours=hours, minutes=minutes))

        try:
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: mode_name,
                ATTR_START_TIME: job_start_time
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_BINARY_SENSOR, entity_name)

            entity_description = BinarySensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon="mdi:calendar-check" if is_enabled else "mdi:calendar-remove"
            )

            self.entity_manager.set_entity(DOMAIN_BINARY_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           device_name,
                                           entity_description)

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_sensor_filter_status(
            self,
            device_name: str,
            data: dict
    ):
        entity_name = f"{device_name} Filter"

        try:
            filter_bag_indication = data.get(DATA_SECTION_FILTER_BAG_INDICATION, {})
            filter_state = filter_bag_indication.get(CONF_STATE, -1)
            reset_fbi = filter_bag_indication.get(DATA_FILTER_BAG_INDICATION_RESET_FBI, False)

            state = FILTER_BAG_STATUS.get(filter_state)
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_RESET_FBI: reset_fbi,
                ATTR_STATUS: filter_state
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=FILTER_BAG_ICONS.get(filter_state)
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           device_name,
                                           entity_description)

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}"
            )

    def _load_sensor_cycle_time(
            self,
            device_name: str,
            data: dict
    ):
        entity_name = f"{device_name} Cycle Time"

        try:
            cycle_info = data.get(DATA_SECTION_CYCLE_INFO, {})
            cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
            mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
            mode_name = get_cleaning_mode_name(mode)

            cycle_time_minutes = cleaning_mode.get(DATA_CYCLE_INFO_CLEANING_MODE_DURATION, 0)
            cycle_start_time_ts = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE_START_TIME, 0)
            cycle_start_time = get_date_time_from_timestamp(cycle_start_time_ts)
            cycle_time = str(datetime.timedelta(minutes=cycle_time_minutes))

            state = cycle_time
            state_parts = state.split(":")
            state_hours = int(state_parts[0])

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: mode_name,
                ATTR_START_TIME: cycle_start_time
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=CLOCK_HOURS_ICONS.get(state_hours, "mdi:clock-time-twelve"),
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           device_name,
                                           entity_description)

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}"
            )

    def _load_binary_sensor_broker_status(self, device_name: str):
        entity_name = f"{device_name} AWS Broker"

        try:
            data = self.api.data
            aws_iot_broker_status = data.get(ATTR_AWS_IOT_BROKER_STATUS, ConnectivityStatus.NotConnected)

            state = STATE_ON if aws_iot_broker_status == ConnectivityStatus.Connected else STATE_OFF

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_STATUS: aws_iot_broker_status
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_BINARY_SENSOR, entity_name)

            entity_description = BinarySensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon="mdi:aws",
                device_class=BinarySensorDeviceClass.CONNECTIVITY
            )

            self.entity_manager.set_entity(DOMAIN_BINARY_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           device_name,
                                           entity_description)

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_sensor_cycle_time_left(
            self,
            device_name: str,
            data: dict
    ):
        entity_name = f"{device_name} Cycle Time Left"

        try:
            system_details = self._get_system_status_details(data)
            calculated_state = system_details.get(ATTR_CALCULATED_STATUS)

            cycle_info = data.get(DATA_SECTION_CYCLE_INFO, {})
            cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
            mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
            mode_name = get_cleaning_mode_name(mode)

            cycle_time = cleaning_mode.get(DATA_CYCLE_INFO_CLEANING_MODE_DURATION, 0)
            cycle_time_in_seconds = cycle_time * 60

            cycle_start_time_ts = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE_START_TIME, 0)
            cycle_start_time = get_date_time_from_timestamp(cycle_start_time_ts)

            now_ts = datetime.datetime.now().timestamp()

            expected_cycle_end_time_ts = cycle_time_in_seconds + cycle_start_time_ts
            expected_cycle_end_time = get_date_time_from_timestamp(expected_cycle_end_time_ts)

            seconds_left = 0
            # make sure we check the cleaner state -- if its currently off, leave seconds_left to 0
            if calculated_state in [PWS_STATE_ON, PWS_STATE_CLEANING] and expected_cycle_end_time_ts > now_ts:
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

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=CLOCK_HOURS_ICONS.get(state_hours, "mdi:clock-time-twelve"),
                device_class=BinarySensorDeviceClass.CONNECTIVITY
            )

            self.entity_manager.set_entity(DOMAIN_SENSOR,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           device_name,
                                           entity_description)

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}"
            )

    def _load_light_led_enabled(
            self,
            device_name: str,
            data: dict
    ):
        entity_name = device_name

        try:
            led = data.get(DATA_SECTION_LED, {})
            led_mode = led.get(DATA_LED_MODE, LED_MODE_BLINKING)
            led_intensity = led.get(DATA_LED_INTENSITY, DEFAULT_LED_INTENSITY)
            led_enable = led.get(DATA_LED_ENABLE, DEFAULT_ENABLE)

            state = led_enable

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: led_mode,
                ATTR_INTENSITY: led_intensity
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_LIGHT, entity_name)

            entity_description = LightEntityDescription(
                key=unique_id,
                name=entity_name,
                entity_category=EntityCategory.CONFIG
            )

            self.entity_manager.set_entity(DOMAIN_LIGHT,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           device_name,
                                           entity_description)

            self.set_action(unique_id, ACTION_CORE_ENTITY_TURN_ON, self._set_led_enabled)
            self.set_action(unique_id, ACTION_CORE_ENTITY_TURN_OFF, self._set_led_disabled)

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_LIGHT}: {entity_name}"
            )

    def _load_vacuum(
            self,
            device_name: str,
            data: dict
    ):
        entity_name = device_name

        try:
            details = self._get_system_status_details(data)

            debug = data.get(DATA_SECTION_DEBUG, {})
            wifi_rssi = debug.get(DATA_DEBUG_WIFI_RSSI, 0)

            wifi = data.get(DATA_SECTION_WIFI, {})
            net_name = wifi.get(DATA_WIFI_NETWORK_NAME)

            cycle_info = data.get(DATA_SECTION_CYCLE_INFO, {})
            cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
            mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
            mode_name = get_cleaning_mode_name(mode)

            state = details.get(ATTR_CALCULATED_STATUS)

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_RSSI: wifi_rssi,
                ATTR_NETWORK_NAME: net_name,
                ATTR_BATTERY_LEVEL: DEFAULT_BATTERY_LEVEL,
                ATTR_MODE: mode_name
            }

            for key in details:
                attributes[key] = details.get(key)

            unique_id = EntityData.generate_unique_id(DOMAIN_LIGHT, DOMAIN_VACUUM)

            entity_description = VacuumDescription(
                key=unique_id,
                name=entity_name,
                features=VACUUM_FEATURES,
                fan_speed_list=list(CLEANING_MODES_SHORT.values())
            )

            self.entity_manager.set_entity(DOMAIN_VACUUM,
                                           self.entry_id,
                                           state,
                                           attributes,
                                           device_name,
                                           entity_description)

            self.set_action(unique_id, ACTION_CORE_ENTITY_TURN_ON, self._vacuum_turn_on)
            self.set_action(unique_id, ACTION_CORE_ENTITY_TURN_OFF, self._vacuum_turn_off)
            self.set_action(unique_id, ACTION_CORE_ENTITY_TOGGLE, self._vacuum_toggle)
            self.set_action(unique_id, ACTION_CORE_ENTITY_START, self._vacuum_start)
            self.set_action(unique_id, ACTION_CORE_ENTITY_STOP, self._vacuum_stop)
            self.set_action(unique_id, ACTION_CORE_ENTITY_PAUSE, self._vacuum_pause)
            self.set_action(unique_id, ACTION_CORE_ENTITY_SET_FAN_SPEED, self._set_cleaning_mode)
            self.set_action(unique_id, ACTION_CORE_ENTITY_LOCATE, self._vacuum_locate)
            self.set_action(unique_id, ACTION_CORE_ENTITY_SEND_COMMAND, self._send_command)
            self.set_action(unique_id, ACTION_CORE_ENTITY_RETURN_TO_BASE, self._pickup)

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_VACUUM}: {entity_name}"
            )

    async def _set_cleaning_mode(self, entity: EntityData, fan_speed):
        current_clean_mode = entity.attributes.get(ATTR_MODE)

        _LOGGER.debug(f"Change cleaning mode, State: {current_clean_mode}, New: {fan_speed}")

        if current_clean_mode != fan_speed:
            for cleaning_mode in CLEANING_MODES_SHORT:
                value = CLEANING_MODES[cleaning_mode]

                if value == fan_speed:
                    self.api.set_cleaning_mode(cleaning_mode)

    async def _set_led_mode(self, entity: EntityData, option: str):
        led_mode_name = LED_MODES_NAMES.get(option)
        _LOGGER.debug(f"Change led mode, State: {entity.state}, New: {led_mode_name} ({option})")

        if entity.state != led_mode_name:
            value = int(option)

            self.api.set_led_mode(value)

    def set_led_intensity(self, intensity: int):
        self.api.set_led_intensity(intensity)

    async def _set_led_enabled(self, entity: EntityData):
        _LOGGER.debug(f"Enable LED light, State: {entity.state}")

        if not entity.state:
            self.api.set_led_enabled(True)

    async def _set_led_disabled(self, entity: EntityData):
        _LOGGER.debug(f"Disable LED light, State: {entity.state}")

        if entity.state:
            self.api.set_led_enabled(False)

    def get_core_entity_fan_speed(self, entity: EntityData) -> str | None:
        data = self.api.data

        cycle_info = data.get(DATA_SECTION_CYCLE_INFO, {})
        cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
        mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
        mode_name = get_cleaning_mode_name(mode)

        return mode_name

    async def _pickup(self, entity: EntityData):
        _LOGGER.debug("Pickup robot")

        self.api.pickup()

    async def _vacuum_turn_on(self, entity: EntityData):
        _LOGGER.debug(f"Turn on vacuum, State: {entity.state}")
        if entity.state in [PWS_STATE_OFF, PWS_STATE_ERROR]:
            self.api.set_power_state(True)

    async def _vacuum_turn_off(self, entity: EntityData):
        _LOGGER.debug(f"Turn off vacuum, State: {entity.state}")

        if entity.state in [PWS_STATE_ON, PWS_STATE_CLEANING, PWS_STATE_PROGRAMMING]:
            self.api.set_power_state(False)

    async def _vacuum_toggle(self, entity: EntityData):
        is_on = entity.state in [PWS_STATE_ON, PWS_STATE_CLEANING, PWS_STATE_PROGRAMMING]
        toggle_value = not is_on

        _LOGGER.debug(f"Toggle vacuum, State: {entity.state} ({is_on})")
        self.api.set_power_state(toggle_value)

    async def _vacuum_start(self, entity: EntityData):
        _LOGGER.debug(f"Start cleaning, State: {entity.state}")
        if entity.state in [PWS_STATE_ON, PWS_STATE_OFF]:
            self.api.set_power_state(True)

    async def _vacuum_stop(self, entity: EntityData):
        _LOGGER.debug(f"Stop cleaning, State: {entity.state}")

        if entity.state in [PWS_STATE_CLEANING, PWS_STATE_ON]:
            self.api.set_power_state(False)

    async def _vacuum_pause(self, entity: EntityData):
        _LOGGER.debug(f"Pause cleaning, State: {entity.state}")

        if entity.state in [PWS_STATE_CLEANING, PWS_STATE_ON]:
            self.api.set_power_state(False)

    async def _vacuum_locate(self, entity: EntityData):
        data = self.api.data
        device_name = data.get(DATA_ROBOT_NAME)
        unique_id = EntityData.generate_unique_id(DOMAIN_LIGHT, device_name)

        led_light_entity = self.entity_manager.get(unique_id)

        if led_light_entity.state:
            _LOGGER.warning(
                f"Locate will not run as the LED currently on, "
                f"you should see the robot"
            )

        else:
            _LOGGER.debug("Locate robot")

            await self.storage_api.set_locating_mode(True)
            await self._set_led_enabled(led_light_entity)

    async def _send_command(self,
                            entity: EntityData,
                            command: str,
                            params: dict[str, Any] | list[Any] | None):
        validator = SERVICE_VALIDATION.get(command)
        action = self._robot_actions.get(command)

        if validator is None or action is None:
            _LOGGER.error(f"Command {command} is not supported")

        else:
            try:
                validator(params)

                action(params)
            except MultipleInvalid as ex:
                _LOGGER.error(ex.msg)

    def _command_navigate(self, data: dict[str, Any] | list[Any] | None):
        direction = data.get(CONF_DIRECTION)
        _LOGGER.debug(f"Navigate robot {direction}")

        if direction is None:
            _LOGGER.error("Direction is mandatory parameter, please provide and try again")
            return

        self.api.navigate(direction)

    def _command_set_schedule(self, data: dict[str, Any] | list[Any] | None):
        day = data.get(CONF_DAY)
        enabled = data.get(CONF_ENABLED, DEFAULT_ENABLE)
        cleaning_mode = data.get(CONF_MODE, CLEANING_MODE_REGULAR)
        job_time = data.get(CONF_TIME)

        self.api.set_schedule(day, enabled, cleaning_mode, job_time)

    def _command_set_delay(self, data: dict[str, Any] | list[Any] | None):
        enabled = data.get(CONF_ENABLED, DEFAULT_ENABLE)
        cleaning_mode = data.get(CONF_MODE, CLEANING_MODE_REGULAR)
        job_time = data.get(CONF_TIME)

        self.api.set_delay(enabled, cleaning_mode, job_time)

    @staticmethod
    def _log_exception(ex, message):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"{message}, Error: {str(ex)}, Line: {line_number}")

    @staticmethod
    def _get_system_status_details(data: dict):
        system_state = data.get(DATA_SECTION_SYSTEM_STATE, {})
        pws_state = system_state.get(DATA_SYSTEM_STATE_PWS_STATE, PWS_STATE_OFF)
        robot_state = system_state.get(DATA_SYSTEM_STATE_ROBOT_STATE, ROBOT_STATE_NOT_CONNECTED)
        robot_type = system_state.get(DATA_SYSTEM_STATE_ROBOT_TYPE)
        is_busy = system_state.get(DATA_SYSTEM_STATE_IS_BUSY, False)
        turn_on_count = system_state.get(DATA_SYSTEM_STATE_TURN_ON_COUNT, 0)
        time_zone = system_state.get(DATA_SYSTEM_STATE_TIME_ZONE, 0)
        time_zone_name = system_state.get(DATA_SYSTEM_STATE_TIME_ZONE_NAME, DEFAULT_TIME_ZONE_NAME)

        calculated_state = PWS_STATE_OFF

        pws_on = pws_state in [PWS_STATE_ON, PWS_STATE_HOLD_DELAY, PWS_STATE_HOLD_WEEKLY, PWS_STATE_PROGRAMMING]
        pws_error = pws_state in [PWS_STATE_ERROR]
        pws_cleaning = pws_state in [PWS_STATE_ON, ROBOT_STATE_SCANNING]
        pws_programming = pws_state == PWS_STATE_PROGRAMMING

        robot_error = robot_state in [ROBOT_STATE_FAULT]
        robot_cleaning = robot_state not in [ROBOT_STATE_INIT, ROBOT_STATE_NOT_CONNECTED]

        robot_programming = robot_state == PWS_STATE_PROGRAMMING

        if pws_error or robot_error:
            calculated_state = PWS_STATE_ERROR

        elif pws_programming and robot_programming:
            calculated_state = PWS_STATE_PROGRAMMING

        elif pws_on:
            if (pws_cleaning and robot_cleaning) or (pws_programming and not robot_programming):
                calculated_state = PWS_STATE_CLEANING

            else:
                calculated_state = PWS_STATE_OFF

        state_description = f"pwsState: {pws_state} | robotState: {robot_state}"
        _LOGGER.info(f"System status recalculated, State: {calculated_state}, Parameters: {state_description}")

        result = {
            ATTR_CALCULATED_STATUS: calculated_state,
            ATTR_PWS_STATUS: pws_state,
            ATTR_ROBOT_STATUS: robot_state,
            ATTR_ROBOT_TYPE: robot_type,
            ATTR_IS_BUSY: is_busy,
            ATTR_TURN_ON_COUNT: turn_on_count,
            ATTR_TIME_ZONE: f"{time_zone_name} ({time_zone})"
        }

        return result

    async def _api_data_changed(self):
        if self.api.status == ConnectivityStatus.Connected:
            super().update()

            data = self.api.data
            device_name = data.get(DATA_ROBOT_NAME)
            led = data.get(DATA_SECTION_LED, {})
            led_enable = led.get(DATA_LED_ENABLE, DEFAULT_ENABLE)

            if self.storage_api.is_locating and led_enable:
                await sleep(LOCATE_OFF_INTERVAL_SECONDS.total_seconds())

                unique_id = EntityData.generate_unique_id(DOMAIN_LIGHT, device_name)

                entity = self.entity_manager.get(unique_id)

                await self.storage_api.set_locating_mode(False)
                await self._set_led_disabled(entity)

    async def _api_status_changed(self, status: ConnectivityStatus):
        if status == ConnectivityStatus.Connected:
            await self.async_update(datetime.datetime.now())
