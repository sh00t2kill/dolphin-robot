"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/mydolphin_plus/
"""
from __future__ import annotations

from asyncio import sleep
import calendar
from datetime import datetime, timedelta
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
from homeassistant.const import (
    ATTR_MODE,
    CONF_ENABLED,
    CONF_MODE,
    CONF_STATE,
    STATE_OFF,
    STATE_ON,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from ...configuration.helpers.const import DEFAULT_NAME, DOMAIN, MANUFACTURER
from ...configuration.managers.configuration_manager import ConfigurationManager
from ...configuration.models.config_data import ConfigData
from ...core.helpers.const import (
    ACTION_CORE_ENTITY_LOCATE,
    ACTION_CORE_ENTITY_PAUSE,
    ACTION_CORE_ENTITY_RETURN_TO_BASE,
    ACTION_CORE_ENTITY_SELECT_OPTION,
    ACTION_CORE_ENTITY_SEND_COMMAND,
    ACTION_CORE_ENTITY_SET_FAN_SPEED,
    ACTION_CORE_ENTITY_START,
    ACTION_CORE_ENTITY_STOP,
    ACTION_CORE_ENTITY_TOGGLE,
    ACTION_CORE_ENTITY_TURN_OFF,
    ACTION_CORE_ENTITY_TURN_ON,
    DOMAIN_BINARY_SENSOR,
    DOMAIN_LIGHT,
    DOMAIN_SELECT,
    DOMAIN_SENSOR,
    DOMAIN_VACUUM,
)
from ...core.helpers.enums import ConnectivityStatus
from ...core.managers.home_assistant import HomeAssistantManager
from ...core.models.entity_data import EntityData
from ...core.models.select_description import SelectDescription
from ...core.models.vacuum_description import VacuumDescription
from ..api.aws_iot_websocket import IntegrationWS
from ..api.mydolphin_plus_api import IntegrationAPI
from ..api.storage_api import StorageAPI
from ..helpers.common import get_cleaning_mode_name, get_date_time_from_timestamp
from ..helpers.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_CALCULATED_STATUS,
    ATTR_DISABLED,
    ATTR_ENABLE,
    ATTR_EXPECTED_END_TIME,
    ATTR_FRIENDLY_NAME,
    ATTR_INTENSITY,
    ATTR_IS_BUSY,
    ATTR_LED_MODE,
    ATTR_NETWORK_NAME,
    ATTR_PWS_STATUS,
    ATTR_RESET_FBI,
    ATTR_ROBOT_STATUS,
    ATTR_ROBOT_TYPE,
    ATTR_RSSI,
    ATTR_START_TIME,
    ATTR_STATUS,
    ATTR_TIME_ZONE,
    ATTR_TURN_ON_COUNT,
    CLEANING_MODE_REGULAR,
    CLEANING_MODES,
    CLEANING_MODES_SHORT,
    CLOCK_HOURS_ICONS,
    CONF_DAY,
    CONF_DIRECTION,
    CONF_TIME,
    DATA_CYCLE_INFO_CLEANING_MODE,
    DATA_CYCLE_INFO_CLEANING_MODE_DURATION,
    DATA_CYCLE_INFO_CLEANING_MODE_START_TIME,
    DATA_DEBUG_WIFI_RSSI,
    DATA_FEATURE_WEEKLY_TIMER,
    DATA_FILTER_BAG_INDICATION_RESET_FBI,
    DATA_LED_ENABLE,
    DATA_LED_INTENSITY,
    DATA_LED_MODE,
    DATA_ROBOT_NAME,
    DATA_SCHEDULE_CLEANING_MODE,
    DATA_SCHEDULE_IS_ENABLED,
    DATA_SCHEDULE_TIME,
    DATA_SCHEDULE_TIME_HOURS,
    DATA_SCHEDULE_TIME_MINUTES,
    DATA_SECTION_CYCLE_INFO,
    DATA_SECTION_DEBUG,
    DATA_SECTION_DELAY,
    DATA_SECTION_FEATURE,
    DATA_SECTION_FILTER_BAG_INDICATION,
    DATA_SECTION_LED,
    DATA_SECTION_SYSTEM_STATE,
    DATA_SECTION_WEEKLY_SETTINGS,
    DATA_SECTION_WIFI,
    DATA_SYSTEM_STATE_IS_BUSY,
    DATA_SYSTEM_STATE_PWS_STATE,
    DATA_SYSTEM_STATE_ROBOT_STATE,
    DATA_SYSTEM_STATE_ROBOT_TYPE,
    DATA_SYSTEM_STATE_TIME_ZONE,
    DATA_SYSTEM_STATE_TIME_ZONE_NAME,
    DATA_SYSTEM_STATE_TURN_ON_COUNT,
    DATA_WIFI_NETWORK_NAME,
    DEFAULT_BATTERY_LEVEL,
    DEFAULT_ENABLE,
    DEFAULT_LED_INTENSITY,
    DEFAULT_TIME_PART,
    DEFAULT_TIME_ZONE_NAME,
    FILTER_BAG_ICONS,
    FILTER_BAG_STATUS,
    ICON_LED_MODES,
    LED_MODE_BLINKING,
    LED_MODE_ICON_DEFAULT,
    LED_MODES_NAMES,
    LOCATE_OFF_INTERVAL_SECONDS,
    PWS_STATE_CLEANING,
    PWS_STATE_ERROR,
    PWS_STATE_HOLD_DELAY,
    PWS_STATE_HOLD_WEEKLY,
    PWS_STATE_OFF,
    PWS_STATE_ON,
    PWS_STATE_PROGRAMMING,
    ROBOT_STATE_FAULT,
    ROBOT_STATE_INIT,
    ROBOT_STATE_NOT_CONNECTED,
    ROBOT_STATE_SCANNING,
    SERVICE_DAILY_SCHEDULE,
    SERVICE_DELAYED_CLEAN,
    SERVICE_NAVIGATE,
    SERVICE_VALIDATION,
    UPDATE_API_INTERVAL,
    UPDATE_ENTITIES_INTERVAL,
    VACUUM_FEATURES,
    WS_RECONNECT_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class MyDolphinPlusHomeAssistantManager(HomeAssistantManager):
    def __init__(self, hass: HomeAssistant):
        super().__init__(hass, UPDATE_API_INTERVAL)

        self._api: IntegrationAPI = IntegrationAPI(
            self._hass, self._api_data_changed, self._api_status_changed
        )
        self._ws: IntegrationWS = IntegrationWS(
            self._hass, self._ws_data_changed, self._ws_status_changed
        )
        self._config_manager: ConfigurationManager | None = None
        self._storage_api = StorageAPI(self._hass)
        self._can_load_components = False
        self._system_status_details = None

        self._robot_actions: dict[str, [dict[str, Any] | list[Any] | None]] = {
            SERVICE_NAVIGATE: self._command_navigate,
            SERVICE_DAILY_SCHEDULE: self._command_set_schedule,
            SERVICE_DELAYED_CLEAN: self._command_set_delay,
        }

    @property
    def api(self) -> IntegrationAPI:
        return self._api

    @property
    def ws(self) -> IntegrationWS:
        return self._ws

    @property
    def storage_api(self) -> StorageAPI:
        return self._storage_api

    @property
    def config_data(self) -> ConfigData:
        return self._config_manager.get(self.entry_id)

    @property
    def robot_name(self):
        robot_name = self.api.data.get(DATA_ROBOT_NAME)

        return robot_name

    async def async_component_initialize(self, entry: ConfigEntry):
        try:
            self._config_manager = ConfigurationManager(self._hass, self.api)
            await self._config_manager.load(entry)

            self.update_intervals(UPDATE_ENTITIES_INTERVAL, UPDATE_API_INTERVAL)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to async_component_initialize, error: {ex}, line: {line_number}"
            )

    async def async_initialize_data_providers(self, entry: ConfigEntry | None = None):
        await self.storage_api.initialize(self.config_data)

        aws_token_encrypted_key = self.storage_api.aws_token_encrypted_key

        await self.api.initialize(self.config_data, aws_token_encrypted_key)

    async def async_stop_data_providers(self):
        await self.api.terminate()

    async def async_update_data_providers(self):
        try:
            await self.api.async_update()

            await self.ws.async_update()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to async_update_data_providers, Error: {ex}, Line: {line_number}"
            )

    def load_devices(self):
        if not self._can_load_components:
            return

        try:
            data = self.api.data
            device_name = self.robot_name
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
                "hw_version": hw_version,
            }

            self.device_manager.set(device_name, device_info)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to load devices, Error: {ex}, Line: {line_number}")

    def load_entities(self):
        if not self._can_load_components:
            return

        name = self.robot_name

        data = self.ws.data

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

    def _load_select_led_mode(self, device_name: str, data: dict):
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
                ATTR_INTENSITY: led_intensity,
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SELECT, entity_name)

            entity_description = SelectDescription(
                key=unique_id,
                name=entity_name,
                icon=ICON_LED_MODES.get(state, LED_MODE_ICON_DEFAULT),
                device_class=f"{DOMAIN}__{ATTR_LED_MODE}",
                attr_options=tuple(ICON_LED_MODES.keys()),
                entity_category=EntityCategory.CONFIG,
            )

            self.entity_manager.set_entity(
                DOMAIN_SELECT,
                self.entry_id,
                state,
                attributes,
                device_name,
                entity_description,
            )

            self.set_action(
                unique_id, ACTION_CORE_ENTITY_SELECT_OPTION, self._set_led_mode
            )

        except Exception as ex:
            self._log_exception(ex, f"Failed to load {DOMAIN_SELECT}: {entity_name}")

    def _load_binary_sensor_weekly_timer(self, device_name: str, data: dict):
        entity_name = f"{device_name} Weekly Schedule"
        try:
            features = data.get(DATA_SECTION_FEATURE, {})

            weekly_timer = features.get(DATA_FEATURE_WEEKLY_TIMER, {})
            status = weekly_timer.get(ATTR_STATUS, ATTR_DISABLED)

            is_enabled = status == ATTR_ENABLE

            state = STATE_ON if is_enabled else STATE_OFF

            attributes = {ATTR_FRIENDLY_NAME: entity_name, ATTR_STATUS: status}

            unique_id = EntityData.generate_unique_id(DOMAIN_BINARY_SENSOR, entity_name)

            entity_description = BinarySensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon="mdi:calendar-check" if is_enabled else "mdi:calendar-remove",
            )

            self.entity_manager.set_entity(
                DOMAIN_BINARY_SENSOR,
                self.entry_id,
                state,
                attributes,
                device_name,
                entity_description,
            )

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_binary_sensor_schedules(self, device_name: str, day: str, data: dict):
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
            job_start_time = str(timedelta(hours=hours, minutes=minutes))

        try:
            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: mode_name,
                ATTR_START_TIME: job_start_time,
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_BINARY_SENSOR, entity_name)

            entity_description = BinarySensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon="mdi:calendar-check" if is_enabled else "mdi:calendar-remove",
            )

            self.entity_manager.set_entity(
                DOMAIN_BINARY_SENSOR,
                self.entry_id,
                state,
                attributes,
                device_name,
                entity_description,
            )

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_sensor_filter_status(self, device_name: str, data: dict):
        entity_name = f"{device_name} Filter"

        try:
            filter_bag_indication = data.get(DATA_SECTION_FILTER_BAG_INDICATION, {})
            filter_state = filter_bag_indication.get(CONF_STATE, -1)
            reset_fbi = filter_bag_indication.get(
                DATA_FILTER_BAG_INDICATION_RESET_FBI, False
            )
            state = None

            for state_name in FILTER_BAG_STATUS:
                state_range = FILTER_BAG_STATUS.get(state_name)
                state_range_min = int(state_range[0])
                state_range_max = int(state_range[1])

                is_in_range = state_range_max >= filter_state >= state_range_min

                if is_in_range:
                    state = state_name
                    break

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_RESET_FBI: reset_fbi,
                ATTR_STATUS: filter_state,
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)

            entity_description = SensorEntityDescription(
                key=unique_id, name=entity_name, icon=FILTER_BAG_ICONS.get(filter_state)
            )

            self.entity_manager.set_entity(
                DOMAIN_SENSOR,
                self.entry_id,
                state,
                attributes,
                device_name,
                entity_description,
            )

        except Exception as ex:
            self._log_exception(ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}")

    def _load_sensor_cycle_time(self, device_name: str, data: dict):
        entity_name = f"{device_name} Cycle Time"

        try:
            cycle_info = data.get(DATA_SECTION_CYCLE_INFO, {})
            cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
            mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
            mode_name = get_cleaning_mode_name(mode)

            cycle_time_minutes = cleaning_mode.get(
                DATA_CYCLE_INFO_CLEANING_MODE_DURATION, 0
            )
            cycle_time = timedelta(minutes=cycle_time_minutes)
            cycle_time_hours = cycle_time / timedelta(hours=1)

            cycle_start_time_ts = cycle_info.get(
                DATA_CYCLE_INFO_CLEANING_MODE_START_TIME, 0
            )
            cycle_start_time = get_date_time_from_timestamp(cycle_start_time_ts)

            state = cycle_time_minutes

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: mode_name,
                ATTR_START_TIME: cycle_start_time,
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=CLOCK_HOURS_ICONS.get(cycle_time_hours, "mdi:clock-time-twelve"),
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTime.MINUTES,
            )

            self.entity_manager.set_entity(
                DOMAIN_SENSOR,
                self.entry_id,
                state,
                attributes,
                device_name,
                entity_description,
            )

        except Exception as ex:
            self._log_exception(ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}")

    def _load_binary_sensor_broker_status(self, device_name: str):
        entity_name = f"{device_name} AWS Broker"

        try:
            state = (
                STATE_ON
                if self.ws.status == ConnectivityStatus.Connected
                else STATE_OFF
            )

            attributes = {ATTR_FRIENDLY_NAME: entity_name, ATTR_STATUS: self.ws.status}

            unique_id = EntityData.generate_unique_id(DOMAIN_BINARY_SENSOR, entity_name)

            entity_description = BinarySensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon="mdi:aws",
                device_class=BinarySensorDeviceClass.CONNECTIVITY,
            )

            self.entity_manager.set_entity(
                DOMAIN_BINARY_SENSOR,
                self.entry_id,
                state,
                attributes,
                device_name,
                entity_description,
            )

        except Exception as ex:
            self._log_exception(
                ex, f"Failed to load {DOMAIN_BINARY_SENSOR}: {entity_name}"
            )

    def _load_sensor_cycle_time_left(self, device_name: str, data: dict):
        entity_name = f"{device_name} Cycle Time Left"

        try:
            system_details = self._system_status_details
            calculated_state = system_details.get(ATTR_CALCULATED_STATUS)

            cycle_info = data.get(DATA_SECTION_CYCLE_INFO, {})
            cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
            mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
            mode_name = get_cleaning_mode_name(mode)

            cycle_time = cleaning_mode.get(DATA_CYCLE_INFO_CLEANING_MODE_DURATION, 0)
            cycle_time_in_seconds = cycle_time * 60

            cycle_start_time_ts = cycle_info.get(
                DATA_CYCLE_INFO_CLEANING_MODE_START_TIME, 0
            )
            cycle_start_time = get_date_time_from_timestamp(cycle_start_time_ts)

            now = datetime.now()
            now_ts = now.timestamp()

            expected_cycle_end_time_ts = cycle_time_in_seconds + cycle_start_time_ts
            expected_cycle_end_time = get_date_time_from_timestamp(
                expected_cycle_end_time_ts
            )

            seconds_left = 0
            # make sure we check the cleaner state -- if its currently off, leave seconds_left to 0
            if (
                calculated_state in [PWS_STATE_ON, PWS_STATE_CLEANING]
                and expected_cycle_end_time_ts > now_ts
            ):
                # still working
                seconds_left = expected_cycle_end_time_ts - now_ts

            state = timedelta(seconds=seconds_left).total_seconds()
            state_hours = int((expected_cycle_end_time - now) / timedelta(hours=1))

            attributes = {
                ATTR_FRIENDLY_NAME: entity_name,
                ATTR_MODE: mode_name,
                ATTR_START_TIME: cycle_start_time,
                ATTR_EXPECTED_END_TIME: expected_cycle_end_time,
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_SENSOR, entity_name)

            entity_description = SensorEntityDescription(
                key=unique_id,
                name=entity_name,
                icon=CLOCK_HOURS_ICONS.get(state_hours, "mdi:clock-time-twelve"),
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                native_unit_of_measurement=UnitOfTime.SECONDS,
            )

            self.entity_manager.set_entity(
                DOMAIN_SENSOR,
                self.entry_id,
                state,
                attributes,
                device_name,
                entity_description,
            )

        except Exception as ex:
            self._log_exception(ex, f"Failed to load {DOMAIN_SENSOR}: {entity_name}")

    def _load_light_led_enabled(self, device_name: str, data: dict):
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
                ATTR_INTENSITY: led_intensity,
            }

            unique_id = EntityData.generate_unique_id(DOMAIN_LIGHT, entity_name)

            entity_description = LightEntityDescription(
                key=unique_id, name=entity_name, entity_category=EntityCategory.CONFIG
            )

            self.entity_manager.set_entity(
                DOMAIN_LIGHT,
                self.entry_id,
                state,
                attributes,
                device_name,
                entity_description,
            )

            self.set_action(
                unique_id, ACTION_CORE_ENTITY_TURN_ON, self._set_led_enabled
            )
            self.set_action(
                unique_id, ACTION_CORE_ENTITY_TURN_OFF, self._set_led_disabled
            )

        except Exception as ex:
            self._log_exception(ex, f"Failed to load {DOMAIN_LIGHT}: {entity_name}")

    def _load_vacuum(self, device_name: str, data: dict):
        entity_name = device_name

        try:
            details = self._system_status_details

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
                ATTR_MODE: mode_name,
            }

            for key in details:
                attributes[key] = details.get(key)

            unique_id = EntityData.generate_unique_id(DOMAIN_LIGHT, DOMAIN_VACUUM)

            entity_description = VacuumDescription(
                key=unique_id,
                name=entity_name,
                features=VACUUM_FEATURES,
                fan_speed_list=list(CLEANING_MODES_SHORT.values()),
            )

            self.entity_manager.set_entity(
                DOMAIN_VACUUM,
                self.entry_id,
                state,
                attributes,
                device_name,
                entity_description,
            )

            self.set_action(unique_id, ACTION_CORE_ENTITY_TURN_ON, self._vacuum_turn_on)
            self.set_action(
                unique_id, ACTION_CORE_ENTITY_TURN_OFF, self._vacuum_turn_off
            )
            self.set_action(unique_id, ACTION_CORE_ENTITY_TOGGLE, self._vacuum_toggle)
            self.set_action(unique_id, ACTION_CORE_ENTITY_START, self._vacuum_start)
            self.set_action(unique_id, ACTION_CORE_ENTITY_STOP, self._vacuum_stop)
            self.set_action(unique_id, ACTION_CORE_ENTITY_PAUSE, self._vacuum_pause)
            self.set_action(
                unique_id, ACTION_CORE_ENTITY_SET_FAN_SPEED, self._set_cleaning_mode
            )
            self.set_action(unique_id, ACTION_CORE_ENTITY_LOCATE, self._vacuum_locate)
            self.set_action(
                unique_id, ACTION_CORE_ENTITY_SEND_COMMAND, self._send_command
            )
            self.set_action(unique_id, ACTION_CORE_ENTITY_RETURN_TO_BASE, self._pickup)

        except Exception as ex:
            self._log_exception(ex, f"Failed to load {DOMAIN_VACUUM}: {entity_name}")

    async def _set_cleaning_mode(self, entity: EntityData, fan_speed):
        current_clean_mode = entity.attributes.get(ATTR_MODE)

        _LOGGER.debug(
            f"Change cleaning mode, State: {current_clean_mode}, New: {fan_speed}"
        )

        if current_clean_mode != fan_speed:
            for cleaning_mode in CLEANING_MODES_SHORT:
                value = CLEANING_MODES[cleaning_mode]

                if value == fan_speed:
                    self.ws.set_cleaning_mode(cleaning_mode)

    async def _set_led_mode(self, entity: EntityData, option: str):
        led_mode_name = LED_MODES_NAMES.get(option)
        _LOGGER.debug(
            f"Change led mode, State: {entity.state}, New: {led_mode_name} ({option})"
        )

        if entity.state != led_mode_name:
            value = int(option)

            self.ws.set_led_mode(value)

    def set_led_intensity(self, intensity: int):
        self.ws.set_led_intensity(intensity)

    async def _set_led_enabled(self, entity: EntityData):
        _LOGGER.debug(f"Enable LED light, State: {entity.state}")

        if not entity.state:
            self.ws.set_led_enabled(True)

    async def _set_led_disabled(self, entity: EntityData):
        _LOGGER.debug(f"Disable LED light, State: {entity.state}")

        if entity.state:
            self.ws.set_led_enabled(False)

    def get_core_entity_fan_speed(self, entity: EntityData) -> str | None:
        data = self.ws.data

        cycle_info = data.get(DATA_SECTION_CYCLE_INFO, {})
        cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
        mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
        mode_name = get_cleaning_mode_name(mode)

        return mode_name

    async def _pickup(self, entity: EntityData):
        _LOGGER.debug("Pickup robot")

        self.ws.pickup()

    async def _vacuum_turn_on(self, entity: EntityData):
        _LOGGER.debug(f"Turn on vacuum, State: {entity.state}")
        if entity.state in [PWS_STATE_OFF, PWS_STATE_ERROR]:
            self.ws.set_power_state(True)

    async def _vacuum_turn_off(self, entity: EntityData):
        _LOGGER.debug(f"Turn off vacuum, State: {entity.state}")

        if entity.state in [PWS_STATE_ON, PWS_STATE_CLEANING, PWS_STATE_PROGRAMMING]:
            self.ws.set_power_state(False)

    async def _vacuum_toggle(self, entity: EntityData):
        is_on = entity.state in [
            PWS_STATE_ON,
            PWS_STATE_CLEANING,
            PWS_STATE_PROGRAMMING,
        ]
        toggle_value = not is_on

        _LOGGER.debug(f"Toggle vacuum, State: {entity.state} ({is_on})")
        self.ws.set_power_state(toggle_value)

    async def _vacuum_start(self, entity: EntityData):
        _LOGGER.debug(f"Start cleaning, State: {entity.state}")
        if entity.state in [PWS_STATE_ON, PWS_STATE_OFF]:
            self.ws.set_power_state(True)

    async def _vacuum_stop(self, entity: EntityData):
        _LOGGER.debug(f"Stop cleaning, State: {entity.state}")

        if entity.state in [PWS_STATE_CLEANING, PWS_STATE_ON]:
            self.ws.set_power_state(False)

    async def _vacuum_pause(self, entity: EntityData):
        _LOGGER.debug(f"Pause cleaning, State: {entity.state}")

        if entity.state in [PWS_STATE_CLEANING, PWS_STATE_ON]:
            self.ws.set_power_state(False)

    async def _vacuum_locate(self, entity: EntityData):
        device_name = self.robot_name
        unique_id = EntityData.generate_unique_id(DOMAIN_LIGHT, device_name)

        led_light_entity = self.entity_manager.get(unique_id)

        if led_light_entity.state:
            _LOGGER.warning(
                "Locate will not run as the LED currently on, "
                "you should see the robot"
            )

        else:
            _LOGGER.debug("Locate robot")

            await self.storage_api.set_locating_mode(True)
            await self._set_led_enabled(led_light_entity)

    async def _send_command(
        self,
        entity: EntityData,
        command: str,
        params: dict[str, Any] | list[Any] | None,
    ):
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
            _LOGGER.error(
                "Direction is mandatory parameter, please provide and try again"
            )
            return

        self.ws.navigate(direction)

    def _command_set_schedule(self, data: dict[str, Any] | list[Any] | None):
        day = data.get(CONF_DAY)
        enabled = data.get(CONF_ENABLED, DEFAULT_ENABLE)
        cleaning_mode = data.get(CONF_MODE, CLEANING_MODE_REGULAR)
        job_time = data.get(CONF_TIME)

        self.ws.set_schedule(day, enabled, cleaning_mode, job_time)

    def _command_set_delay(self, data: dict[str, Any] | list[Any] | None):
        enabled = data.get(CONF_ENABLED, DEFAULT_ENABLE)
        cleaning_mode = data.get(CONF_MODE, CLEANING_MODE_REGULAR)
        job_time = data.get(CONF_TIME)

        self.ws.set_delay(enabled, cleaning_mode, job_time)

    @staticmethod
    def _log_exception(ex, message):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"{message}, Error: {str(ex)}, Line: {line_number}")

    def _set_system_status_details(self, data: dict):
        system_state = data.get(DATA_SECTION_SYSTEM_STATE, {})
        pws_state = system_state.get(DATA_SYSTEM_STATE_PWS_STATE, PWS_STATE_OFF)
        robot_state = system_state.get(
            DATA_SYSTEM_STATE_ROBOT_STATE, ROBOT_STATE_NOT_CONNECTED
        )
        robot_type = system_state.get(DATA_SYSTEM_STATE_ROBOT_TYPE)
        is_busy = system_state.get(DATA_SYSTEM_STATE_IS_BUSY, False)
        turn_on_count = system_state.get(DATA_SYSTEM_STATE_TURN_ON_COUNT, 0)
        time_zone = system_state.get(DATA_SYSTEM_STATE_TIME_ZONE, 0)
        time_zone_name = system_state.get(
            DATA_SYSTEM_STATE_TIME_ZONE_NAME, DEFAULT_TIME_ZONE_NAME
        )

        calculated_state = PWS_STATE_OFF

        pws_on = pws_state in [
            PWS_STATE_ON,
            PWS_STATE_HOLD_DELAY,
            PWS_STATE_HOLD_WEEKLY,
            PWS_STATE_PROGRAMMING,
        ]
        pws_error = pws_state in [PWS_STATE_ERROR]
        pws_cleaning = pws_state in [PWS_STATE_ON, ROBOT_STATE_SCANNING]
        pws_programming = pws_state == PWS_STATE_PROGRAMMING

        robot_error = robot_state in [ROBOT_STATE_FAULT]
        robot_cleaning = robot_state not in [ROBOT_STATE_NOT_CONNECTED]

        robot_programming = robot_state == PWS_STATE_PROGRAMMING

        if pws_error or robot_error:
            calculated_state = PWS_STATE_ERROR

        elif pws_programming and robot_programming:
            calculated_state = PWS_STATE_PROGRAMMING

        elif pws_on:
            if (pws_cleaning and robot_cleaning) or (
                pws_programming and not robot_programming
            ):
                calculated_state = (
                    ROBOT_STATE_INIT
                    if robot_state == ROBOT_STATE_INIT
                    else PWS_STATE_CLEANING
                )

            else:
                calculated_state = PWS_STATE_OFF

        result = {
            ATTR_CALCULATED_STATUS: calculated_state,
            ATTR_PWS_STATUS: pws_state,
            ATTR_ROBOT_STATUS: robot_state,
            ATTR_ROBOT_TYPE: robot_type,
            ATTR_IS_BUSY: is_busy,
            ATTR_TURN_ON_COUNT: turn_on_count,
            ATTR_TIME_ZONE: f"{time_zone_name} ({time_zone})",
        }

        if self._system_status_details != result:
            self._can_load_components = True

            state_description = f"pwsState: {pws_state} | robotState: {robot_state}"
            _LOGGER.debug(
                f"System status recalculated, State: {calculated_state}, Parameters: {state_description}"
            )

            self._system_status_details = result

    async def _set_aws_token_encrypted_key(self):
        aws_token_encrypted_key = self.api.aws_token_encrypted_key

        if self.storage_api.aws_token_encrypted_key != aws_token_encrypted_key:
            await self.storage_api.set_aws_token_encrypted_key(aws_token_encrypted_key)

    async def _api_data_changed(self):
        if self.api.status == ConnectivityStatus.Connected:
            await self.storage_api.debug_log_api(self.api.data)

    async def _api_status_changed(self, status: ConnectivityStatus):
        _LOGGER.info(
            f"API Status changed to {status.name}, WS Status: {self.ws.status.name}"
        )

        if status == ConnectivityStatus.Connected:
            await self._set_aws_token_encrypted_key()

            await self.api.async_update()

            await self.ws.update_api_data(self.api.data)

            self._update_entities(None)

            await self.ws.initialize(self.config_data)

        elif status == ConnectivityStatus.Failed:
            await self._set_aws_token_encrypted_key()

    async def _ws_data_changed(self):
        if self.ws.status == ConnectivityStatus.Connected:
            data = self.ws.data

            await self.storage_api.debug_log_ws(data)

            self._set_system_status_details(data)

            device_name = self.robot_name
            led = data.get(DATA_SECTION_LED, {})
            led_enable = led.get(DATA_LED_ENABLE, DEFAULT_ENABLE)

            if self.storage_api.is_locating and led_enable:
                await sleep(LOCATE_OFF_INTERVAL_SECONDS.total_seconds())

                unique_id = EntityData.generate_unique_id(DOMAIN_LIGHT, device_name)

                entity = self.entity_manager.get(unique_id)

                await self.storage_api.set_locating_mode(False)
                await self._set_led_disabled(entity)

    async def _ws_status_changed(self, status: ConnectivityStatus):
        _LOGGER.info(
            f"WS Status changed to {status.name}, API Status: {self.api.status.name}"
        )

        if status == ConnectivityStatus.Connected:
            await self.async_update_data_providers()

        elif status in [ConnectivityStatus.NotConnected, ConnectivityStatus.Failed]:
            await sleep(WS_RECONNECT_INTERVAL.total_seconds())

            await self.ws.update_api_data(self.api.data)

            await self.ws.initialize(self.config_data)
