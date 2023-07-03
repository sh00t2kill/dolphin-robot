from asyncio import sleep
import calendar
from datetime import datetime, timedelta
import logging
import sys
from typing import Any, Callable

from voluptuous import MultipleInvalid

from homeassistant.const import (
    ATTR_ICON,
    ATTR_MODE,
    ATTR_STATE,
    CONF_ENABLED,
    CONF_MODE,
    CONF_PASSWORD,
    CONF_STATE,
)
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify

from ..common.connectivity_status import ConnectivityStatus
from ..common.consts import (
    ACTION_ENTITY_LOCATE,
    ACTION_ENTITY_PAUSE,
    ACTION_ENTITY_RETURN_TO_BASE,
    ACTION_ENTITY_SELECT_OPTION,
    ACTION_ENTITY_SEND_COMMAND,
    ACTION_ENTITY_SET_FAN_SPEED,
    ACTION_ENTITY_SET_NATIVE_VALUE,
    ACTION_ENTITY_START,
    ACTION_ENTITY_STOP,
    ACTION_ENTITY_TOGGLE,
    ACTION_ENTITY_TURN_OFF,
    ACTION_ENTITY_TURN_ON,
    API_DATA_SERIAL_NUMBER,
    API_RECONNECT_INTERVAL,
    ATTR_ACTIONS,
    ATTR_ATTRIBUTES,
    ATTR_CALCULATED_STATUS,
    ATTR_DISABLED,
    ATTR_ENABLE,
    ATTR_EXPECTED_END_TIME,
    ATTR_IS_BUSY,
    ATTR_IS_ON,
    ATTR_PWS_STATUS,
    ATTR_RESET_FBI,
    ATTR_ROBOT_STATUS,
    ATTR_ROBOT_TYPE,
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
    CONFIGURATION_URL,
    CONSIDERED_POWER_STATE,
    DATA_CYCLE_INFO_CLEANING_MODE,
    DATA_CYCLE_INFO_CLEANING_MODE_DURATION,
    DATA_CYCLE_INFO_CLEANING_MODE_START_TIME,
    DATA_DEBUG_WIFI_RSSI,
    DATA_FEATURE_WEEKLY_TIMER,
    DATA_FILTER_BAG_INDICATION_RESET_FBI,
    DATA_KEY_AWS_BROKER,
    DATA_KEY_BUSY,
    DATA_KEY_CLEAN_MODE,
    DATA_KEY_CYCLE_COUNT,
    DATA_KEY_CYCLE_TIME,
    DATA_KEY_CYCLE_TIME_LEFT,
    DATA_KEY_FILTER_STATUS,
    DATA_KEY_LED,
    DATA_KEY_LED_INTENSITY,
    DATA_KEY_LED_MODE,
    DATA_KEY_MAIN_UNIT_STATUS,
    DATA_KEY_NETWORK_NAME,
    DATA_KEY_ROBOT_STATUS,
    DATA_KEY_ROBOT_TYPE,
    DATA_KEY_RSSI,
    DATA_KEY_SCHEDULE,
    DATA_KEY_STATUS,
    DATA_KEY_VACUUM,
    DATA_KEY_WEEKLY_SCHEDULER,
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
    DEFAULT_ENABLE,
    DEFAULT_LED_INTENSITY,
    DEFAULT_NAME,
    DEFAULT_TIME_PART,
    DEFAULT_TIME_ZONE_NAME,
    FILTER_BAG_ICONS,
    FILTER_BAG_STATUS,
    ICON_LED_MODES,
    LED_MODE_BLINKING,
    LED_MODE_ICON_DEFAULT,
    MANUFACTURER,
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
    WS_RECONNECT_INTERVAL,
)
from ..common.entity_descriptions import MyDolphinPlusDailyBinarySensorEntityDescription
from .aws_client import AWSClient
from .config_manager import ConfigManager
from .rest_api import RestAPI

_LOGGER = logging.getLogger(__name__)


class MyDolphinPlusCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    _api: RestAPI
    _aws_client: AWSClient | None

    _data_mapping: dict[str, Callable[[EntityDescription], dict | None]] | None
    _system_status_details: dict | None

    _last_update: float

    def __init__(self, hass, config_manager: ConfigManager):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=config_manager.name,
            update_interval=UPDATE_ENTITIES_INTERVAL,
            update_method=self._async_update_data,
        )

        self._api = RestAPI(hass, config_manager, self._on_api_status_changed)
        self._aws_client = AWSClient(hass, self._on_aws_client_status_changed)

        self._config_manager = config_manager

        self._data_mapping = None
        self._system_status_details = None

        self._last_update = 0

        self._robot_actions: dict[str, [dict[str, Any] | list[Any] | None]] = {
            SERVICE_NAVIGATE: self._command_navigate,
            SERVICE_DAILY_SCHEDULE: self._command_set_schedule,
            SERVICE_DELAYED_CLEAN: self._command_set_delay,
        }

    @property
    def robot_name(self):
        robot_name = self._api.data.get(DATA_ROBOT_NAME)

        return robot_name

    @property
    def aws_data(self) -> dict:
        data = self._aws_client.data

        return data

    async def initialize(self):
        self._build_data_mapping()

        await self._api.initialize(self._config_manager.aws_token_encrypted_key)

    def get_device_serial_number(self) -> str:
        serial_number = self._api.data.get(API_DATA_SERIAL_NUMBER)

        return serial_number

    def get_device_debug_data(self) -> dict:
        config_data = {}
        for config_item_key in self._config_manager.data:
            if config_item_key not in [CONF_PASSWORD]:
                config_data[config_item_key] = self._config_manager.data[
                    config_item_key
                ]

        data = {
            "config": config_data,
            "api": self._api.data,
            "aws_client": self._aws_client.data,
        }

        return data

    def get_device(self) -> DeviceInfo:
        data = self._api.data
        device_name = self.robot_name
        model = data.get("Product Description")
        versions = data.get("versions", {})
        pws_version = versions.get("pwsVersion", {})
        sw_version = pws_version.get("pwsSwVersion")
        hw_version = pws_version.get("pwsHwVersion")

        serial_number = data.get(API_DATA_SERIAL_NUMBER)

        device_info = DeviceInfo(
            identifiers={(DEFAULT_NAME, serial_number)},
            name=device_name,
            model=model,
            manufacturer=MANUFACTURER,
            hw_version=hw_version,
            sw_version=sw_version,
            configuration_url=CONFIGURATION_URL,
        )

        return device_info

    async def _set_aws_token_encrypted_key(self):
        aws_token_encrypted_key = self._api.aws_token_encrypted_key

        if self._config_manager.aws_token_encrypted_key != aws_token_encrypted_key:
            await self._config_manager.update_aws_token_encrypted_key(
                aws_token_encrypted_key
            )

    async def _on_api_status_changed(self, status: ConnectivityStatus):
        if status == ConnectivityStatus.Connected:
            await self._set_aws_token_encrypted_key()

            await self._api.update()

            await self._aws_client.update_api_data(self._api.data)

            await self._aws_client.initialize()

        elif status == ConnectivityStatus.Failed:
            await self._aws_client.terminate()

            await sleep(API_RECONNECT_INTERVAL.total_seconds())

            await self._api.initialize(self._config_manager.aws_token_encrypted_key)

    async def _on_aws_client_status_changed(self, status: ConnectivityStatus):
        if status == ConnectivityStatus.Connected:
            await self._aws_client.update()

        if status == ConnectivityStatus.Failed:
            await self._api.initialize(None)

            await sleep(WS_RECONNECT_INTERVAL.total_seconds())

            await self._api.initialize(self._config_manager.aws_token_encrypted_key)

    async def _async_update_data(self):
        """Fetch parameters from API endpoint.

        This is the place to pre-process the parameters to lookup tables
        so entities can quickly look up their parameters.
        """
        try:
            api_connected = self._api.status == ConnectivityStatus.Connected
            aws_client_connected = (
                self._aws_client.status == ConnectivityStatus.Connected
            )

            is_ready = api_connected and aws_client_connected

            if is_ready:
                now = datetime.now().timestamp()

                if now - self._last_update >= UPDATE_API_INTERVAL.total_seconds():
                    await self._api.update()
                    await self._aws_client.update()

                    self._last_update = now

                self._set_system_status_details()

            return {}

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    def _build_data_mapping(self):
        data_mapping = {
            slugify(DATA_KEY_STATUS): self._get_status_data,
            slugify(DATA_KEY_RSSI): self._get_rssi_data,
            slugify(DATA_KEY_NETWORK_NAME): self._get_network_name_data,
            slugify(DATA_KEY_CLEAN_MODE): self._get_clean_mode_data,
            slugify(DATA_KEY_MAIN_UNIT_STATUS): self._get_main_unit_status_data,
            slugify(DATA_KEY_ROBOT_STATUS): self._get_robot_status_data,
            slugify(DATA_KEY_ROBOT_TYPE): self._get_robot_type_data,
            slugify(DATA_KEY_BUSY): self._get_busy_data,
            slugify(DATA_KEY_CYCLE_COUNT): self._get_cycle_count_data,
            slugify(DATA_KEY_VACUUM): self._get_vacuum_data,
            slugify(DATA_KEY_LED_MODE): self._get_led_mode_data,
            slugify(DATA_KEY_LED): self._get_led_data,
            slugify(DATA_KEY_LED_INTENSITY): self._get_led_intensity_data,
            slugify(DATA_KEY_FILTER_STATUS): self._get_filter_status_data,
            slugify(DATA_KEY_CYCLE_TIME): self._get_cycle_time_data,
            slugify(DATA_KEY_CYCLE_TIME_LEFT): self._get_cycle_time_left_data,
            slugify(DATA_KEY_AWS_BROKER): self._get_aws_broker_data,
            slugify(DATA_KEY_WEEKLY_SCHEDULER): self._get_weekly_schedule,
        }

        schedules = list(calendar.day_name)
        schedules.append(DATA_SECTION_DELAY)

        for day in schedules:
            data_mapping[
                slugify(f"{DATA_KEY_SCHEDULE} {day}")
            ] = self._get_daily_schedule_data

        self._data_mapping = data_mapping

        _LOGGER.debug(f"Data retrieval mapping created, Mapping: {self._data_mapping}")

    def get_data(self, entity_description: EntityDescription) -> dict | None:
        result = None

        try:
            handler = self._data_mapping.get(entity_description.key)

            if handler is None:
                _LOGGER.error(
                    f"Handler was not found for {entity_description.key}, Entity Description: {entity_description}"
                )

            else:
                if self._system_status_details is not None:
                    result = handler(entity_description)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to extract data for {entity_description}, Error: {ex}, Line: {line_number}"
            )

        return result

    def get_device_action(
        self, entity_description: EntityDescription, action_key: str
    ) -> Callable:
        device_data = self.get_data(entity_description)
        actions = device_data.get(ATTR_ACTIONS)
        async_action = actions.get(action_key)

        return async_action

    def _get_status_data(self, _entity_description) -> dict | None:
        state = self._system_status_details.get(ATTR_CALCULATED_STATUS)

        result = {
            ATTR_STATE: None if state is None else state.lower(),
            ATTR_ATTRIBUTES: self._system_status_details,
        }

        return result

    def _get_rssi_data(self, _entity_description) -> dict | None:
        debug = self.aws_data.get(DATA_SECTION_DEBUG, {})
        wifi_rssi = debug.get(DATA_DEBUG_WIFI_RSSI, 0)

        result = {ATTR_STATE: wifi_rssi}

        return result

    def _get_network_name_data(self, _entity_description) -> dict | None:
        wifi = self.aws_data.get(DATA_SECTION_WIFI, {})
        net_name = wifi.get(DATA_WIFI_NETWORK_NAME)

        result = {ATTR_STATE: net_name}

        return result

    def _get_clean_mode_data(self, _entity_description) -> dict | None:
        cycle_info = self.aws_data.get(DATA_SECTION_CYCLE_INFO, {})
        cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
        mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)

        result = {ATTR_STATE: mode}

        return result

    def _get_main_unit_status_data(self, _entity_description) -> dict | None:
        state = self._system_status_details.get(ATTR_PWS_STATUS)

        result = {ATTR_STATE: state}

        return result

    def _get_robot_status_data(self, _entity_description) -> dict | None:
        state = self._system_status_details.get(ATTR_ROBOT_STATUS)

        result = {ATTR_STATE: None if state is None else state.lower()}

        return result

    def _get_robot_type_data(self, _entity_description) -> dict | None:
        state = self._system_status_details.get(ATTR_ROBOT_TYPE)

        result = {ATTR_STATE: state}

        return result

    def _get_busy_data(self, _entity_description) -> dict | None:
        is_on = self._system_status_details.get(ATTR_IS_BUSY)

        result = {ATTR_IS_ON: is_on}

        return result

    def _get_cycle_count_data(self, _entity_description) -> dict | None:
        state = self._system_status_details.get(ATTR_TURN_ON_COUNT)

        result = {ATTR_STATE: state}

        return result

    def _get_vacuum_data(self, _entity_description) -> dict | None:
        cycle_info = self.aws_data.get(DATA_SECTION_CYCLE_INFO, {})
        cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
        mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)

        state = self._system_status_details.get(ATTR_CALCULATED_STATUS)

        result = {
            ATTR_STATE: state,
            ATTR_ATTRIBUTES: {ATTR_MODE: mode},
            ATTR_ACTIONS: {
                ACTION_ENTITY_TURN_ON: self._vacuum_turn_on,
                ACTION_ENTITY_TURN_OFF: self._vacuum_turn_off,
                ACTION_ENTITY_TOGGLE: self._vacuum_toggle,
                ACTION_ENTITY_START: self._vacuum_start,
                ACTION_ENTITY_STOP: self._vacuum_stop,
                ACTION_ENTITY_PAUSE: self._vacuum_pause,
                ACTION_ENTITY_SET_FAN_SPEED: self._set_cleaning_mode,
                ACTION_ENTITY_LOCATE: self._vacuum_locate,
                ACTION_ENTITY_SEND_COMMAND: self._send_command,
                ACTION_ENTITY_RETURN_TO_BASE: self._pickup,
            },
        }

        return result

    def _get_led_mode_data(self, _entity_description) -> dict | None:
        led = self.aws_data.get(DATA_SECTION_LED, {})
        led_mode = str(led.get(DATA_LED_MODE, LED_MODE_BLINKING))

        result = {
            ATTR_STATE: led_mode,
            ATTR_ICON: ICON_LED_MODES.get(led_mode, LED_MODE_ICON_DEFAULT),
            ATTR_ACTIONS: {ACTION_ENTITY_SELECT_OPTION: self._set_led_mode},
        }

        return result

    def _get_led_data(self, _entity_description) -> dict | None:
        led = self.aws_data.get(DATA_SECTION_LED, {})
        led_enable = led.get(DATA_LED_ENABLE, DEFAULT_ENABLE)

        result = {
            ATTR_IS_ON: led_enable,
            ATTR_ACTIONS: {
                ACTION_ENTITY_TURN_ON: self._set_led_enabled,
                ACTION_ENTITY_TURN_OFF: self._set_led_disabled,
            },
        }

        return result

    def _get_led_intensity_data(self, _entity_description) -> dict | None:
        led = self.aws_data.get(DATA_SECTION_LED, {})
        led_intensity = led.get(DATA_LED_INTENSITY, DEFAULT_LED_INTENSITY)

        result = {
            ATTR_STATE: led_intensity,
            ATTR_ACTIONS: {
                ACTION_ENTITY_SET_NATIVE_VALUE: self._set_led_intensity,
            },
        }

        return result

    def _get_weekly_schedule(self, _entity_description) -> dict | None:
        features = self.aws_data.get(DATA_SECTION_FEATURE, {})

        weekly_timer = features.get(DATA_FEATURE_WEEKLY_TIMER, {})
        status = weekly_timer.get(ATTR_STATUS, ATTR_DISABLED)

        is_enabled = status == ATTR_ENABLE

        result = {
            ATTR_IS_ON: is_enabled,
            ATTR_ATTRIBUTES: {ATTR_STATUS: status},
            ATTR_ICON: "mdi:calendar-check" if is_enabled else "mdi:calendar-remove",
        }

        return result

    def _get_daily_schedule_data(self, entity_description) -> dict | None:
        local_entity: MyDolphinPlusDailyBinarySensorEntityDescription = (
            entity_description
        )

        if local_entity.day == DATA_SECTION_DELAY:
            schedule_settings = self.aws_data.get(local_entity.day, {})

        else:
            weekly_settings = self.aws_data.get(DATA_SECTION_WEEKLY_SETTINGS, {})

            schedule_settings = weekly_settings.get(local_entity.day.lower(), {})

        is_enabled = schedule_settings.get(DATA_SCHEDULE_IS_ENABLED, DEFAULT_ENABLE)
        cleaning_mode = schedule_settings.get(DATA_SCHEDULE_CLEANING_MODE, {})
        job_time = schedule_settings.get(DATA_SCHEDULE_TIME, {})

        mode = cleaning_mode.get(ATTR_MODE, CLEANING_MODE_REGULAR)
        hours = job_time.get(DATA_SCHEDULE_TIME_HOURS, DEFAULT_TIME_PART)
        minutes = job_time.get(DATA_SCHEDULE_TIME_MINUTES, DEFAULT_TIME_PART)

        job_start_time = None
        if hours < DEFAULT_TIME_PART and minutes < DEFAULT_TIME_PART:
            job_start_time = str(timedelta(hours=hours, minutes=minutes))

        result = {
            ATTR_IS_ON: is_enabled,
            ATTR_ATTRIBUTES: {
                ATTR_MODE: mode,
                ATTR_START_TIME: job_start_time,
            },
            ATTR_ICON: "mdi:calendar-check" if is_enabled else "mdi:calendar-remove",
        }

        return result

    def _get_filter_status_data(self, _entity_description) -> dict | None:
        filter_bag_indication = self.aws_data.get(
            DATA_SECTION_FILTER_BAG_INDICATION, {}
        )
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

        result = {
            ATTR_STATE: state,
            ATTR_ATTRIBUTES: {
                ATTR_RESET_FBI: reset_fbi,
                ATTR_STATUS: filter_state,
            },
            ATTR_ICON: FILTER_BAG_ICONS.get(filter_state),
        }

        return result

    def _get_cycle_time_data(self, _entity_description) -> dict | None:
        cycle_info = self.aws_data.get(DATA_SECTION_CYCLE_INFO, {})
        cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})

        cycle_time_minutes = cleaning_mode.get(
            DATA_CYCLE_INFO_CLEANING_MODE_DURATION, 0
        )
        cycle_time = timedelta(minutes=cycle_time_minutes)
        cycle_time_hours = cycle_time / timedelta(hours=1)

        cycle_start_time_ts = cycle_info.get(
            DATA_CYCLE_INFO_CLEANING_MODE_START_TIME, 0
        )
        cycle_start_time = self._get_date_time_from_timestamp(cycle_start_time_ts)

        result = {
            ATTR_STATE: cycle_time_minutes,
            ATTR_ATTRIBUTES: {
                ATTR_START_TIME: cycle_start_time,
            },
            ATTR_ICON: CLOCK_HOURS_ICONS.get(cycle_time_hours, "mdi:clock-time-twelve"),
        }

        return result

    def _get_cycle_time_left_data(self, _entity_description) -> dict | None:
        system_details = self._system_status_details
        calculated_state = system_details.get(ATTR_CALCULATED_STATUS)

        cycle_info = self.aws_data.get(DATA_SECTION_CYCLE_INFO, {})
        cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})

        cycle_time = cleaning_mode.get(DATA_CYCLE_INFO_CLEANING_MODE_DURATION, 0)
        cycle_time_in_seconds = cycle_time * 60

        cycle_start_time_ts = cycle_info.get(
            DATA_CYCLE_INFO_CLEANING_MODE_START_TIME, 0
        )
        cycle_start_time = self._get_date_time_from_timestamp(cycle_start_time_ts)

        now = datetime.now()
        now_ts = now.timestamp()

        expected_cycle_end_time_ts = cycle_time_in_seconds + cycle_start_time_ts
        expected_cycle_end_time = self._get_date_time_from_timestamp(
            expected_cycle_end_time_ts
        )

        seconds_left = 0
        if (
            calculated_state in [PWS_STATE_ON, PWS_STATE_CLEANING]
            and expected_cycle_end_time_ts > now_ts
        ):
            seconds_left = expected_cycle_end_time_ts - now_ts

        state = timedelta(seconds=seconds_left).total_seconds()
        state_hours = int((expected_cycle_end_time - now) / timedelta(hours=1))

        result = {
            ATTR_STATE: state,
            ATTR_ATTRIBUTES: {
                ATTR_START_TIME: cycle_start_time,
                ATTR_EXPECTED_END_TIME: expected_cycle_end_time,
            },
            ATTR_ICON: CLOCK_HOURS_ICONS.get(state_hours, "mdi:clock-time-twelve"),
        }

        return result

    def _get_aws_broker_data(self, _entity_description) -> dict | None:
        is_on = self._aws_client.status == ConnectivityStatus.Connected

        result = {
            ATTR_IS_ON: is_on,
            ATTR_ATTRIBUTES: {ATTR_STATUS: self._aws_client.status},
        }

        return result

    async def _set_cleaning_mode(self, fan_speed):
        data = self._get_vacuum_data(None)
        attributes = data.get(ATTR_ATTRIBUTES)
        mode = attributes.get(ATTR_MODE)

        _LOGGER.debug(f"Change cleaning mode, State: {mode}, New: {fan_speed}")

        if mode != fan_speed:
            for cleaning_mode in CLEANING_MODES_SHORT:
                value = CLEANING_MODES[cleaning_mode]

                if value == fan_speed:
                    self._aws_client.set_cleaning_mode(cleaning_mode)

    async def _set_led_mode(self, option: str):
        _LOGGER.debug(f"Change led mode, New: {option}")

        value = int(option)

        self._aws_client.set_led_mode(value)

    async def _set_led_enabled(self):
        _LOGGER.debug("Enable LED light")

        self._aws_client.set_led_enabled(True)

    async def _set_led_disabled(self):
        _LOGGER.debug("Disable LED light")

        self._aws_client.set_led_enabled(False)

    def _set_led_intensity(self, intensity: int):
        self._aws_client.set_led_intensity(intensity)

    async def _pickup(self):
        _LOGGER.debug("Pickup robot")

        self._aws_client.pickup()

    async def _switch_power(self, state: str, desired_state: bool):
        considered_state = CONSIDERED_POWER_STATE.get(state, False)
        _LOGGER.debug(f"Set vacuum power state, State: {state}, Power: {desired_state}")

        if considered_state != desired_state:
            self._aws_client.set_power_state(True)

    async def _vacuum_turn_on(self, state):
        await self._switch_power(state, True)

    async def _vacuum_turn_off(self, state):
        await self._switch_power(state, False)

    async def _vacuum_toggle(self, state):
        considered_state = CONSIDERED_POWER_STATE.get(state, False)

        await self._switch_power(state, not considered_state)

    async def _vacuum_start(self, state):
        await self._switch_power(state, True)

    async def _vacuum_stop(self, state):
        await self._switch_power(state, False)

    async def _vacuum_pause(self, state):
        await self._switch_power(state, False)

    async def _vacuum_locate(self):
        led_light_entity = self._get_led_data(None)

        led_light_state = led_light_entity.get(CONF_STATE)

        if led_light_state:
            _LOGGER.warning(
                "Locate will not run as the LED currently on, "
                "you should see the robot"
            )

        else:
            _LOGGER.debug("Locate robot")

            await self._config_manager.update_is_locating(True)
            await self._set_led_enabled()

    async def _send_command(
        self,
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
            _LOGGER.error("Direction is mandatory")
            return

        self._aws_client.navigate(direction)

    def _command_set_schedule(self, data: dict[str, Any] | list[Any] | None):
        day = data.get(CONF_DAY)
        enabled = data.get(CONF_ENABLED, DEFAULT_ENABLE)
        cleaning_mode = data.get(CONF_MODE, CLEANING_MODE_REGULAR)
        job_time = data.get(CONF_TIME)

        self._aws_client.set_schedule(day, enabled, cleaning_mode, job_time)

    def _command_set_delay(self, data: dict[str, Any] | list[Any] | None):
        enabled = data.get(CONF_ENABLED, DEFAULT_ENABLE)
        cleaning_mode = data.get(CONF_MODE, CLEANING_MODE_REGULAR)
        job_time = data.get(CONF_TIME)

        self._aws_client.set_delay(enabled, cleaning_mode, job_time)

    def _set_system_status_details(self):
        data = self.aws_data

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

        pws_on = pws_state.lower() in [
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

            _LOGGER.debug(
                f"System status recalculated, "
                f"Calculated State: {calculated_state}, "
                f"Main Unit State: {pws_state}, "
                f"Robot State: {robot_state}"
            )

            self._system_status_details = result

    @staticmethod
    def _get_date_time_from_timestamp(timestamp):
        result = datetime.fromtimestamp(timestamp)

        return result
