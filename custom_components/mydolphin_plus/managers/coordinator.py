from asyncio import sleep
from datetime import datetime, timedelta
import logging
import sys
from typing import Any, Callable

from voluptuous import MultipleInvalid

from homeassistant.components.number.const import SERVICE_SET_VALUE
from homeassistant.components.vacuum import (
    SERVICE_LOCATE,
    SERVICE_PAUSE,
    SERVICE_RETURN_TO_BASE,
    SERVICE_SEND_COMMAND,
    SERVICE_SET_FAN_SPEED,
    SERVICE_START,
    STATE_DOCKED,
)
from homeassistant.const import (
    ATTR_ICON,
    ATTR_MODE,
    ATTR_STATE,
    CONF_STATE,
    SERVICE_SELECT_OPTION,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import Event, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify

from ..common.calculated_state import CalculatedState
from ..common.clean_modes import CleanModes, get_clean_mode_cycle_time_key
from ..common.connectivity_status import ConnectivityStatus
from ..common.consts import (
    API_RECONNECT_INTERVAL,
    ATTR_ACTIONS,
    ATTR_ATTRIBUTES,
    ATTR_EXPECTED_END_TIME,
    ATTR_IS_ON,
    ATTR_RESET_FBI,
    ATTR_START_TIME,
    ATTR_STATUS,
    CLOCK_HOURS_ICON,
    CLOCK_HOURS_NONE,
    CLOCK_HOURS_TEXT,
    CONF_DIRECTION,
    CONFIGURATION_URL,
    DATA_CYCLE_INFO_CLEANING_MODE,
    DATA_CYCLE_INFO_CLEANING_MODE_DURATION,
    DATA_CYCLE_INFO_CLEANING_MODE_START_TIME,
    DATA_DEBUG_WIFI_RSSI,
    DATA_ERROR_CODE,
    DATA_ERROR_TURN_ON_COUNT,
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
    DATA_KEY_NETWORK_NAME,
    DATA_KEY_POWER_SUPPLY_STATUS,
    DATA_KEY_PWS_ERROR,
    DATA_KEY_ROBOT_ERROR,
    DATA_KEY_ROBOT_STATUS,
    DATA_KEY_ROBOT_TYPE,
    DATA_KEY_RSSI,
    DATA_KEY_STATUS,
    DATA_KEY_VACUUM,
    DATA_LED_ENABLE,
    DATA_LED_INTENSITY,
    DATA_LED_MODE,
    DATA_ROBOT_NAME,
    DATA_SECTION_CYCLE_INFO,
    DATA_SECTION_DEBUG,
    DATA_SECTION_DYNAMIC,
    DATA_SECTION_FILTER_BAG_INDICATION,
    DATA_SECTION_LED,
    DATA_SECTION_PWS_ERROR,
    DATA_SECTION_ROBOT_ERROR,
    DATA_SECTION_SYSTEM_STATE,
    DATA_SECTION_WIFI,
    DATA_SYSTEM_STATE_TURN_ON_COUNT,
    DATA_WIFI_NETWORK_NAME,
    DEFAULT_ENABLE,
    DEFAULT_LED_INTENSITY,
    DEFAULT_NAME,
    DOMAIN,
    DYNAMIC_DESCRIPTION_TEMPERATURE,
    DYNAMIC_TYPE_IOT_RESPONSE,
    ERROR_CLEAN_CODES,
    FILTER_BAG_ICONS,
    FILTER_BAG_STATUS,
    ICON_LED_MODES,
    LED_MODE_BLINKING,
    LED_MODE_ICON_DEFAULT,
    MANUFACTURER,
    PLATFORMS,
    SIGNAL_API_STATUS,
    SIGNAL_AWS_CLIENT_STATUS,
    UPDATE_API_INTERVAL,
    UPDATE_ENTITIES_INTERVAL,
    UPDATE_WS_INTERVAL,
)
from ..common.service_schema import (
    SERVICE_EXIT_NAVIGATION,
    SERVICE_NAVIGATE,
    SERVICE_VALIDATION,
)
from ..models.system_details import SystemDetails
from .aws_client import AWSClient
from .config_manager import ConfigManager
from .rest_api import RestAPI

_LOGGER = logging.getLogger(__name__)


class MyDolphinPlusCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    _api: RestAPI
    _aws_client: AWSClient | None

    _data_mapping: dict[str, Callable[[EntityDescription], dict | None]] | None
    _system_details: SystemDetails

    _last_update_api: float
    _last_update_ws: float

    def __init__(self, hass, config_manager: ConfigManager):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=config_manager.name,
            update_interval=UPDATE_ENTITIES_INTERVAL,
            update_method=self._async_update_data,
        )

        self._api = RestAPI(hass, config_manager)
        self._aws_client = AWSClient(hass, config_manager)

        self._config_manager = config_manager

        self._data_mapping = None
        self._system_details = SystemDetails()

        self._last_update_api = 0
        self._last_update_ws = 0

        self._robot_actions: dict[str, [dict[str, Any] | list[Any] | None]] = {
            SERVICE_NAVIGATE: self._service_navigate,
            SERVICE_EXIT_NAVIGATION: self._service_exit_navigation,
        }

        self._load_signal_handlers()

    @property
    def robot_name(self):
        robot_name = self.api_data.get(DATA_ROBOT_NAME)

        if robot_name is None or robot_name == "":
            robot_name = DEFAULT_NAME

        return robot_name

    @property
    def api_data(self) -> dict:
        data = self._api.data

        return data

    @property
    def aws_data(self) -> dict:
        data = self._aws_client.data

        return data

    @property
    def config_manager(self) -> ConfigManager:
        config_manager = self._config_manager

        return config_manager

    async def on_home_assistant_start(self, _event_data: Event):
        await self.initialize()

    async def terminate(self):
        await self._aws_client.terminate()

    async def initialize(self):
        self._build_data_mapping()

        entry = self.config_manager.entry
        await self.hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        _LOGGER.info(f"Start loading {DOMAIN} integration, Entry ID: {entry.entry_id}")

        await self.async_request_refresh()

        for service_name in self._robot_actions:
            service_handler = self._robot_actions.get(service_name)
            schema = SERVICE_VALIDATION.get(service_name)

            self.hass.services.async_register(
                DOMAIN, service_name, service_handler, schema
            )

        await self._api.initialize()

    def _load_signal_handlers(self):
        loop = self.hass.loop

        @callback
        def on_api_status_changed(entry_id: str, status: ConnectivityStatus):
            loop.create_task(self._on_api_status_changed(entry_id, status)).__await__()

        @callback
        def on_aws_client_status_changed(entry_id: str, status: ConnectivityStatus):
            loop.create_task(
                self._on_aws_client_status_changed(entry_id, status)
            ).__await__()

        self.config_entry.async_on_unload(
            async_dispatcher_connect(
                self.hass, SIGNAL_API_STATUS, on_api_status_changed
            )
        )

        self.config_entry.async_on_unload(
            async_dispatcher_connect(
                self.hass, SIGNAL_AWS_CLIENT_STATUS, on_aws_client_status_changed
            )
        )

    def get_device_debug_data(self) -> dict:
        config_data = self._config_manager.get_debug_data()

        data = {
            "config": config_data,
            "api": self.api_data,
            "aws_client": self._aws_client.data,
        }

        return data

    def get_device(self) -> DeviceInfo:
        data = self.api_data
        device_name = self.robot_name
        model = data.get("Product Description")
        versions = data.get("versions", {})
        pws_version = versions.get("pwsVersion", {})
        sw_version = pws_version.get("pwsSwVersion")
        hw_version = pws_version.get("pwsHwVersion")

        serial_number = self.config_manager.serial_number

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

    async def _on_api_status_changed(self, entry_id: str, status: ConnectivityStatus):
        if entry_id != self._config_manager.entry_id:
            return

        if status == ConnectivityStatus.CONNECTED:
            await self._api.update()

            await self._aws_client.update_api_data(self.api_data)

            await self._aws_client.initialize()

        elif status in [
            ConnectivityStatus.FAILED,
            ConnectivityStatus.INVALID_CREDENTIALS,
            ConnectivityStatus.EXPIRED_TOKEN,
        ]:
            await self._handle_connection_failure()

    async def _on_aws_client_status_changed(
        self, entry_id: str, status: ConnectivityStatus
    ):
        if entry_id != self._config_manager.entry_id:
            return

        if status == ConnectivityStatus.CONNECTED:
            await self._aws_client.update()

        if status in [ConnectivityStatus.FAILED, ConnectivityStatus.NOT_CONNECTED]:
            await self._handle_connection_failure()

    async def _handle_connection_failure(self):
        await self._aws_client.terminate()

        await sleep(API_RECONNECT_INTERVAL.total_seconds())

        await self._api.initialize()

    async def _async_update_data(self):
        """Fetch parameters from API endpoint.

        This is the place to pre-process the parameters to lookup tables
        so entities can quickly look up their parameters.
        """
        try:
            api_connected = self._api.status == ConnectivityStatus.CONNECTED
            aws_client_connected = (
                self._aws_client.status == ConnectivityStatus.CONNECTED
            )

            is_ready = api_connected and aws_client_connected

            if is_ready:
                now = datetime.now().timestamp()

                if now - self._last_update_api >= UPDATE_API_INTERVAL.total_seconds():
                    await self._api.update()

                    self._last_update_api = now

                if now - self._last_update_ws >= UPDATE_WS_INTERVAL.total_seconds():
                    await self._aws_client.update()

                    self._last_update_ws = now

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
            slugify(DATA_KEY_POWER_SUPPLY_STATUS): self._get_power_supply_status_data,
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
            slugify(DATA_KEY_ROBOT_ERROR): self._get_robot_error_data,
            slugify(DATA_KEY_PWS_ERROR): self._get_pws_error_data,
            slugify(DYNAMIC_DESCRIPTION_TEMPERATURE): self._get_temperature_data,
        }

        for clean_mode in list(CleanModes):
            key = get_clean_mode_cycle_time_key(CleanModes(clean_mode))

            data_mapping[key] = self._get_clean_mode_cycle_time_data

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
                if self._system_details.is_updated:
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
        state = self._system_details.calculated_state

        result = {
            ATTR_STATE: None if state is None else state.lower(),
            ATTR_ATTRIBUTES: self._system_details.data,
        }

        return result

    def _get_rssi_data(self, _entity_description) -> dict | None:
        debug = self.aws_data.get(DATA_SECTION_DEBUG, {})
        state = debug.get(DATA_DEBUG_WIFI_RSSI, 0)

        result = {ATTR_STATE: state}

        return result

    def _get_temperature_data(self, _entity_description) -> dict | None:
        dynamic = self.aws_data.get(DATA_SECTION_DYNAMIC, {})
        iot_response = dynamic.get(DYNAMIC_TYPE_IOT_RESPONSE, {})
        temperature_int = iot_response.get(DYNAMIC_DESCRIPTION_TEMPERATURE, 0)

        state_str = str(temperature_int)
        state_str_fixed = f"{state_str[:2]}.{state_str[2:].ljust(2, '0')}"
        state = float(state_str_fixed)

        result = {ATTR_STATE: state}

        return result

    def _get_network_name_data(self, _entity_description) -> dict | None:
        wifi = self.aws_data.get(DATA_SECTION_WIFI, {})
        net_name = wifi.get(DATA_WIFI_NETWORK_NAME)

        result = {ATTR_STATE: net_name}

        return result

    def _get_clean_mode_data(self, _entity_description) -> dict | None:
        cycle_info = self.aws_data.get(DATA_SECTION_CYCLE_INFO, {})
        cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
        mode = cleaning_mode.get(ATTR_MODE, CleanModes.REGULAR)

        result = {ATTR_STATE: mode}

        return result

    def _get_power_supply_status_data(self, _entity_description) -> dict | None:
        state = self._system_details.power_unit_state.lower()

        result = {ATTR_STATE: None if state is None else state.lower()}

        return result

    def _get_robot_status_data(self, _entity_description) -> dict | None:
        state = self._system_details.robot_state.lower()

        result = {ATTR_STATE: None if state is None else state.lower()}

        return result

    def _get_robot_type_data(self, _entity_description) -> dict | None:
        state = self._system_details.robot_type

        result = {ATTR_STATE: state}

        return result

    def _get_busy_data(self, _entity_description) -> dict | None:
        is_on = self._system_details.is_busy

        result = {ATTR_IS_ON: is_on}

        return result

    def _get_cycle_count_data(self, _entity_description) -> dict | None:
        state = self._system_details.turn_on_count

        result = {ATTR_STATE: state}

        return result

    def _get_vacuum_data(self, _entity_description) -> dict | None:
        cycle_info = self.aws_data.get(DATA_SECTION_CYCLE_INFO, {})
        cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
        mode = cleaning_mode.get(ATTR_MODE, CleanModes.REGULAR)

        state = self._system_details.vacuum_state

        result = {
            ATTR_STATE: state,
            ATTR_ATTRIBUTES: {ATTR_MODE: mode},
            ATTR_ACTIONS: {
                SERVICE_START: self._vacuum_start,
                SERVICE_PAUSE: self._vacuum_pause,
                SERVICE_SET_FAN_SPEED: self._set_cleaning_mode,
                SERVICE_LOCATE: self._vacuum_locate,
                SERVICE_SEND_COMMAND: self._send_command,
                SERVICE_RETURN_TO_BASE: self._pickup,
            },
        }

        return result

    def _get_led_mode_data(self, _entity_description) -> dict | None:
        led = self.aws_data.get(DATA_SECTION_LED, {})
        led_mode = str(led.get(DATA_LED_MODE, LED_MODE_BLINKING))

        result = {
            ATTR_STATE: led_mode,
            ATTR_ICON: ICON_LED_MODES.get(led_mode, LED_MODE_ICON_DEFAULT),
            ATTR_ACTIONS: {SERVICE_SELECT_OPTION: self._set_led_mode},
        }

        return result

    def _get_led_data(self, _entity_description) -> dict | None:
        led = self.aws_data.get(DATA_SECTION_LED, {})
        led_enable = led.get(DATA_LED_ENABLE, DEFAULT_ENABLE)

        result = {
            ATTR_IS_ON: led_enable,
            ATTR_ACTIONS: {
                SERVICE_TURN_ON: self._set_led_enabled,
                SERVICE_TURN_OFF: self._set_led_disabled,
            },
        }

        return result

    def _get_led_intensity_data(self, _entity_description) -> dict | None:
        led = self.aws_data.get(DATA_SECTION_LED, {})
        led_intensity = led.get(DATA_LED_INTENSITY, DEFAULT_LED_INTENSITY)

        result = {
            ATTR_STATE: led_intensity,
            ATTR_ACTIONS: {
                SERVICE_SET_VALUE: self._set_led_intensity,
            },
        }

        return result

    def _get_clean_mode_cycle_time_data(self, entity_description) -> dict | None:
        key = entity_description.key
        key_parts = key.split("_")
        clean_mode_str = key_parts[len(key_parts) - 1]
        clean_mode = CleanModes(clean_mode_str)
        state = self.config_manager.get_clean_cycle_time(clean_mode)

        result = {
            ATTR_STATE: state,
            ATTR_ACTIONS: {
                SERVICE_SET_VALUE: self._set_clean_mode_cycle_time_data,
            },
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

        attributes = {}

        if cycle_time_minutes == 0:
            cycle_time_hours = None

        else:
            cycle_time = timedelta(minutes=cycle_time_minutes)
            cycle_time_hours = int(cycle_time / timedelta(hours=1))

            cycle_start_time_ts = cycle_info.get(
                DATA_CYCLE_INFO_CLEANING_MODE_START_TIME, 0
            )
            cycle_start_time = self._get_date_time_from_timestamp(cycle_start_time_ts)

            attributes[ATTR_START_TIME] = cycle_start_time

        icon = self._get_hour_icon(cycle_time_hours)

        result = {
            ATTR_STATE: cycle_time_minutes,
            ATTR_ATTRIBUTES: attributes,
            ATTR_ICON: icon,
        }

        return result

    def _get_cycle_time_left_data(self, _entity_description) -> dict | None:
        calculated_state = self._system_details.calculated_state

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

        state = 0
        seconds_left = 0
        state_hours = None

        if (
            calculated_state == CalculatedState.CLEANING
            and expected_cycle_end_time_ts > now_ts
        ):
            seconds_left = expected_cycle_end_time_ts - now_ts

        if seconds_left > 0:
            state = timedelta(seconds=seconds_left).total_seconds()
            state_hours = int((expected_cycle_end_time - now) / timedelta(hours=1))

        icon = self._get_hour_icon(state_hours)

        result = {
            ATTR_STATE: state,
            ATTR_ATTRIBUTES: {
                ATTR_START_TIME: cycle_start_time,
                ATTR_EXPECTED_END_TIME: expected_cycle_end_time,
            },
            ATTR_ICON: icon,
        }

        return result

    def _get_aws_broker_data(self, _entity_description) -> dict | None:
        is_on = self._aws_client.status == ConnectivityStatus.CONNECTED

        result = {
            ATTR_IS_ON: is_on,
            ATTR_ATTRIBUTES: {ATTR_STATUS: self._aws_client.status},
        }

        return result

    def _get_robot_error_data(self, entity_description) -> dict | None:
        result = self._get_error_code(entity_description, DATA_SECTION_ROBOT_ERROR)

        return result

    def _get_pws_error_data(self, entity_description) -> dict | None:
        result = self._get_error_code(entity_description, DATA_SECTION_PWS_ERROR)

        return result

    def _get_error_code(self, entity_description, data_section_key) -> dict | None:
        data = self.aws_data

        system_state = data.get(DATA_SECTION_SYSTEM_STATE, {})
        turn_on_count = system_state.get(DATA_SYSTEM_STATE_TURN_ON_COUNT, 0)

        error_section = data.get(data_section_key, {})
        error_code = error_section.get(DATA_ERROR_CODE, 0)
        error_turn_on_count = error_section.get(DATA_ERROR_TURN_ON_COUNT, 0)

        state = 0

        if error_turn_on_count == turn_on_count:
            state = error_code

        icon = entity_description.icon

        if state not in ERROR_CLEAN_CODES:
            icon = f"{icon}-alert"

        result = {ATTR_STATE: state, ATTR_ICON: icon}

        return result

    async def _set_cleaning_mode(
        self, _entity_description: EntityDescription, fan_speed
    ):
        data = self._get_vacuum_data(None)
        attributes = data.get(ATTR_ATTRIBUTES)
        mode = attributes.get(ATTR_MODE)

        _LOGGER.debug(f"Change cleaning mode, State: {mode}, New: {fan_speed}")

        if mode != fan_speed:
            self._aws_client.set_cleaning_mode(fan_speed)

    async def _set_led_mode(self, _entity_description: EntityDescription, option: str):
        _LOGGER.debug(f"Change led mode, New: {option}")

        value = int(option)

        self._aws_client.set_led_mode(value)

    async def _set_led_enabled(self, _entity_description: EntityDescription):
        _LOGGER.debug("Enable LED light")

        self._aws_client.set_led_enabled(True)

    async def _set_led_disabled(self, _entity_description: EntityDescription):
        _LOGGER.debug("Disable LED light")

        self._aws_client.set_led_enabled(False)

    async def _set_led_intensity(
        self, _entity_description: EntityDescription, intensity: int
    ):
        self._aws_client.set_led_intensity(intensity)

    async def _set_clean_mode_cycle_time_data(
        self, entity_description: EntityDescription, cycle_time: int
    ):
        key_parts = entity_description.key.split("_")
        clean_mode_str = key_parts[len(key_parts) - 1]
        clean_mode = CleanModes(clean_mode_str)

        await self.config_manager.update_clean_cycle_time(clean_mode, cycle_time)

    async def _pickup(self, _entity_description: EntityDescription):
        _LOGGER.debug("Pickup vacuum")

        self._aws_client.pickup()

    async def _vacuum_start(self, _entity_description: EntityDescription, _state):
        _LOGGER.debug("Start vacuum")

        data = self._get_vacuum_data(None)
        attributes = data.get(ATTR_ATTRIBUTES)
        mode = attributes.get(ATTR_MODE, CleanModes.REGULAR)

        self._aws_client.set_cleaning_mode(mode)

    async def _vacuum_pause(self, _entity_description: EntityDescription, state):
        is_idle_state = state == STATE_DOCKED
        _LOGGER.debug(f"Pause vacuum, State: {state}, State: {state}")

        if is_idle_state:
            self._aws_client.pause()

    async def _vacuum_locate(self, entity_description: EntityDescription):
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
            await self._set_led_enabled(entity_description)

    async def _send_command(
        self,
        _entity_description: EntityDescription,
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

    async def _service_exit_navigation(self):
        _LOGGER.debug("Exit navigation mode")

        self._aws_client.exit_navigation()

    async def _service_navigate(self, data: dict[str, Any] | list[Any] | None):
        direction = data.get(CONF_DIRECTION)
        _LOGGER.debug(f"Navigate robot {direction}")

        if direction is None:
            _LOGGER.error("Direction is mandatory")
            return

        self._aws_client.navigate(direction)

    def _set_system_status_details(self):
        updated = self._system_details.update(self.aws_data)

        if updated:
            self._can_load_components = True

            _LOGGER.debug(
                f"System status recalculated, "
                f"Calculated State: {self._system_details.calculated_state}, "
                f"Main Unit State: {self._system_details.power_unit_state}, "
                f"Robot State: {self._system_details.robot_state}"
            )

    @staticmethod
    def _get_date_time_from_timestamp(timestamp):
        result = datetime.fromtimestamp(timestamp)

        return result

    @staticmethod
    def _get_hour_icon(current_hour: int | None) -> str:
        if current_hour is None:
            icon = CLOCK_HOURS_NONE

        else:
            if current_hour > 11:
                current_hour = current_hour - 12

            if current_hour >= len(CLOCK_HOURS_TEXT):
                current_hour = 0

            hour_text = CLOCK_HOURS_TEXT[current_hour]
            icon = "".join([CLOCK_HOURS_ICON, hour_text])

        return icon
