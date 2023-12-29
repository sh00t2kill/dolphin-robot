from __future__ import annotations

from datetime import datetime
import json
import logging
import os
import sys
from time import sleep
from typing import Any
import uuid

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

from homeassistant.const import CONF_MODE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from ..common.clean_modes import CleanModes
from ..common.connectivity_status import IGNORED_TRANSITIONS, ConnectivityStatus
from ..common.consts import (
    API_DATA_MOTOR_UNIT_SERIAL,
    API_DATA_SERIAL_NUMBER,
    API_RESPONSE_DATA_ACCESS_KEY_ID,
    API_RESPONSE_DATA_SECRET_ACCESS_KEY,
    API_RESPONSE_DATA_TOKEN,
    ATTR_REMOTE_CONTROL_MODE_EXIT,
    AWS_IOT_PORT,
    AWS_IOT_URL,
    CA_FILE_NAME,
    DATA_CYCLE_INFO_CLEANING_MODE_DURATION,
    DATA_FILTER_BAG_INDICATION_RESET_FBI_COMMAND,
    DATA_LED_ENABLE,
    DATA_LED_INTENSITY,
    DATA_LED_MODE,
    DATA_ROOT_STATE,
    DATA_ROOT_TIMESTAMP,
    DATA_ROOT_VERSION,
    DATA_SCHEDULE_CLEANING_MODE,
    DATA_SCHEDULE_IS_ENABLED,
    DATA_SCHEDULE_TIME,
    DATA_SCHEDULE_TIME_HOURS,
    DATA_SCHEDULE_TIME_MINUTES,
    DATA_SECTION_CYCLE_INFO,
    DATA_SECTION_DYNAMIC,
    DATA_SECTION_FILTER_BAG_INDICATION,
    DATA_SECTION_LED,
    DATA_SECTION_SYSTEM_STATE,
    DATA_STATE_DESIRED,
    DATA_STATE_REPORTED,
    DATA_SYSTEM_STATE_PWS_STATE,
    DEFAULT_ENABLE,
    DEFAULT_LED_INTENSITY,
    DEFAULT_TIME_PART,
    DYNAMIC_CONTENT,
    DYNAMIC_CONTENT_DIRECTION,
    DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL,
    DYNAMIC_CONTENT_REMOTE_CONTROL_MODE,
    DYNAMIC_CONTENT_SERIAL_NUMBER,
    DYNAMIC_CONTENT_SPEED,
    DYNAMIC_DESCRIPTION,
    DYNAMIC_DESCRIPTION_JOYSTICK,
    DYNAMIC_DESCRIPTION_TEMPERATURE,
    DYNAMIC_TYPE,
    DYNAMIC_TYPE_PWS_REQUEST,
    JOYSTICK_SPEED,
    LED_MODE_BLINKING,
    MQTT_MESSAGE_ENCODING,
    MQTT_QOS_0,
    MQTT_QOS_1,
    PWS_STATE_OFF,
    PWS_STATE_ON,
    SIGNAL_AWS_CLIENT_STATUS,
    TOPIC_CALLBACK_ACCEPTED,
    TOPIC_CALLBACK_REJECTED,
    UPDATE_API_INTERVAL,
    WS_DATA_DIFF,
    WS_DATA_TIMESTAMP,
    WS_DATA_VERSION,
    WS_LAST_UPDATE,
)
from ..models.topic_data import TopicData
from .config_manager import ConfigManager

_LOGGER = logging.getLogger(__name__)


class AWSClient:
    _awsiot_client: AWSIoTMQTTClient | None

    _topic_data: TopicData | None
    _status: ConnectivityStatus | None

    def __init__(self, hass: HomeAssistant | None, config_manager: ConfigManager):
        try:
            self._hass = hass
            self._config_manager = config_manager

            self._api_data = {}
            self._data = {}

            self._topic_data = None
            self._awsiot_client = None

            self._status = None

            self._local_async_dispatcher_send = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load MyDolphin Plus WS, error: {ex}, line: {line_number}"
            )

    @property
    def status(self) -> str | None:
        status = self._status

        return status

    @property
    def _is_home_assistant(self):
        return self._hass is not None

    @property
    def _has_running_loop(self):
        return self._hass.loop is not None and not self._hass.loop.is_closed()

    @property
    def data(self) -> dict:
        return self._data

    async def terminate(self):
        if self._awsiot_client is not None:
            topics = self._topic_data.subscribe
            _LOGGER.debug(f"Unsubscribing topics: {', '.join(topics)}")
            for topic in self._topic_data.subscribe:
                self._awsiot_client.unsubscribeAsync(topic)

            _LOGGER.debug("Disconnecting AWS Client")
            self._awsiot_client.disconnectAsync(self._ack_callback)

            self._awsiot_client = None

        self._set_status(ConnectivityStatus.Disconnected)
        _LOGGER.debug("AWS Client is disconnected")

    async def initialize(self):
        try:
            _LOGGER.info("Initializing MyDolphin AWS IOT WS")

            self._set_status(ConnectivityStatus.Connecting)

            awsiot_id = str(uuid.uuid4())
            aws_token = self._api_data.get(API_RESPONSE_DATA_TOKEN)
            aws_key = self._api_data.get(API_RESPONSE_DATA_ACCESS_KEY_ID)
            aws_secret = self._api_data.get(API_RESPONSE_DATA_SECRET_ACCESS_KEY)

            _LOGGER.debug(
                f"AWS IAM Credentials, Key: {aws_key}, Secret: {aws_secret}, Token: {aws_token}"
            )

            motor_unit_serial = self._api_data.get(API_DATA_MOTOR_UNIT_SERIAL)

            self._topic_data = TopicData(motor_unit_serial)

            script_dir = os.path.dirname(__file__)
            ca_file_path = os.path.join(script_dir, CA_FILE_NAME)

            _LOGGER.debug(f"Loading CA file from {ca_file_path}")

            client = AWSIoTMQTTClient(awsiot_id, useWebsocket=True)
            client.configureEndpoint(AWS_IOT_URL, AWS_IOT_PORT)
            client.configureCredentials(ca_file_path)
            client.configureIAMCredentials(aws_key, aws_secret, aws_token)
            client.configureAutoReconnectBackoffTime(1, 32, 20)
            client.configureOfflinePublishQueueing(
                -1
            )  # Infinite offline Publish queueing
            client.configureDrainingFrequency(2)  # Draining: 2 Hz
            client.configureConnectDisconnectTimeout(10)
            client.configureMQTTOperationTimeout(10)
            client.enableMetricsCollection()
            client.onOnline = self._handle_aws_client_online
            client.onOffline = self._handle_aws_client_offline

            for topic in self._topic_data.subscribe:
                client.subscribeAsync(
                    topic, MQTT_QOS_0, self._ack_callback, self._message_callback
                )

            connected = client.connectAsync(ackCallback=self._ack_callback)

            if connected:
                _LOGGER.debug(f"Connected to {AWS_IOT_URL}")
                self._awsiot_client = client

            else:
                _LOGGER.error(f"Failed to connect to {AWS_IOT_URL}")
                self._set_status(ConnectivityStatus.Failed)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize MyDolphin Plus WS, error: {ex}, line: {line_number}"
            )

            self._set_status(ConnectivityStatus.Failed)

    async def update_api_data(self, api_data: dict):
        self._api_data = api_data

    async def update(self):
        if self._status == ConnectivityStatus.Connected:
            _LOGGER.debug("Connected. Refresh details")
            await self._refresh_details()

    async def _refresh_details(self, forced: bool = False):
        try:
            now = datetime.now().timestamp()
            last_update = self.data.get(WS_LAST_UPDATE, 0)

            diff_seconds = int(now) - last_update

            if forced or diff_seconds >= UPDATE_API_INTERVAL.total_seconds():
                self.data[WS_LAST_UPDATE] = int(now)

                self._publish(self._topic_data.get, None)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to refresh MyDolphin Plus WS data, error: {ex}, line: {line_number}"
            )

    def _handle_aws_client_online(self):
        _LOGGER.debug("AWS IOT Client is Online")

        self._set_status(ConnectivityStatus.Connected)

    def _handle_aws_client_offline(self):
        _LOGGER.debug("AWS IOT Client is Offline")

        self._set_status(ConnectivityStatus.Failed)

    @staticmethod
    def _ack_callback(mid, data):
        _LOGGER.debug(f"ACK packet ID: {mid}, QoS: {data}")

    def _message_callback(self, _client, _userdata, message):
        message_topic: str = message.topic
        message_payload = message.payload.decode(MQTT_MESSAGE_ENCODING)

        try:
            has_message = len(message_payload) <= 0
            payload = {} if has_message else json.loads(message_payload)

            motor_unit_serial = self._api_data.get(API_DATA_SERIAL_NUMBER)
            _LOGGER.debug(
                f"Message received for device {motor_unit_serial}, Topic: {message_topic}"
            )

            if message_topic.endswith(TOPIC_CALLBACK_REJECTED):
                _LOGGER.warning(
                    f"Rejected message for {message_topic}, Message: {message_payload}"
                )

            elif message_topic == self._topic_data.dynamic:
                _LOGGER.debug(f"Dynamic payload: {message_payload}")

                response_type = payload.get(DYNAMIC_TYPE)
                data = payload.get(DYNAMIC_CONTENT)

                if response_type not in self.data:
                    self.data[DATA_SECTION_DYNAMIC] = {}

                self.data[DATA_SECTION_DYNAMIC][response_type] = data

            elif message_topic.endswith(TOPIC_CALLBACK_ACCEPTED):
                _LOGGER.debug(f"Payload: {message_payload}")

                version = payload.get(DATA_ROOT_VERSION)
                server_timestamp = payload.get(DATA_ROOT_TIMESTAMP)

                now = datetime.now().timestamp()
                diff = int(now) - server_timestamp

                self.data[WS_DATA_VERSION] = version
                self.data[WS_DATA_TIMESTAMP] = server_timestamp
                self.data[WS_DATA_DIFF] = diff

                state = payload.get(DATA_ROOT_STATE, {})
                reported = state.get(DATA_STATE_REPORTED, {})

                for category in reported.keys():
                    category_data = reported.get(category)

                    if category_data is not None:
                        latest_data = self.data.get(category)

                        if isinstance(latest_data, dict):
                            self.data[category].update(category_data)

                        else:
                            self.data[category] = category_data

                if message_topic == self._topic_data.get_accepted:
                    self._read_temperature_and_in_water_details()

                elif message_topic == self._topic_data.update_accepted:
                    desired = state.get(DATA_STATE_DESIRED)

                    if desired is not None:
                        cleaning_mode = desired.get(DATA_SCHEDULE_CLEANING_MODE, {})
                        mode = cleaning_mode.get(CONF_MODE)

                        if mode is not None:
                            sleep(1)
                            self._set_cycle_time(mode)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno
            message_details = f"Topic: {message_topic}, Data: {message_payload}"
            error_details = f"Error: {str(ex)}, Line: {line_number}"

            _LOGGER.error(
                f"Callback parsing failed, {message_details}, {error_details}"
            )

    def _send_desired_command(self, payload: dict | None):
        data = {DATA_ROOT_STATE: {DATA_STATE_DESIRED: payload}}

        self._publish(self._topic_data.update, data)

    def _send_dynamic_command(self, description: str, payload: dict | None):
        payload[DYNAMIC_TYPE] = DYNAMIC_TYPE_PWS_REQUEST
        payload[DYNAMIC_DESCRIPTION] = description

        self._publish(self._topic_data.dynamic, payload)

    def _publish(self, topic: str, data: dict | None):
        payload = "" if data is None else json.dumps(data)

        if self._status == ConnectivityStatus.Connected:
            try:
                if self._awsiot_client is not None:
                    published = self._awsiot_client.publishAsync(
                        topic, payload, MQTT_QOS_1
                    )

                    if published:
                        _LOGGER.debug(f"Published message: {data} to {topic}")
                    else:
                        _LOGGER.warning(f"Failed to publish message: {data} to {topic}")

            except Exception as ex:
                _LOGGER.error(
                    f"Error while trying to publish message: {data} to {topic}, Error: {str(ex)}"
                )

        else:
            _LOGGER.error(
                f"Failed to publish message: {data} to {topic}, Broker is not connected"
            )

    def set_cleaning_mode(self, clean_mode: CleanModes):
        data = {DATA_SCHEDULE_CLEANING_MODE: {CONF_MODE: str(clean_mode)}}

        _LOGGER.info(f"Set cleaning mode, Desired: {data}")
        self._send_desired_command(data)

    def _set_cycle_time(self, clean_mode: CleanModes):
        cycle_time = self._config_manager.get_clean_cycle_time(clean_mode)

        data = {
            DATA_SECTION_CYCLE_INFO: {
                DATA_CYCLE_INFO_CLEANING_MODE_DURATION: cycle_time,
            }
        }

        _LOGGER.info(f"Set cycle time, Desired: {data}")
        self._send_desired_command(data)

    def set_led_mode(self, mode: int):
        data = self._get_led_settings(DATA_LED_MODE, mode)

        _LOGGER.info(f"Set led mode, Desired: {data}")
        self._send_desired_command(data)

    def set_led_intensity(self, intensity: int):
        data = self._get_led_settings(DATA_LED_INTENSITY, intensity)

        _LOGGER.info(f"Set led intensity, Desired: {data}")
        self._send_desired_command(data)

    def set_led_enabled(self, is_enabled: bool):
        data = self._get_led_settings(DATA_LED_ENABLE, is_enabled)

        _LOGGER.info(f"Set led enabled mode, Desired: {data}")
        self._send_desired_command(data)

    def navigate(self, direction: str):
        request_data = {
            DYNAMIC_CONTENT_SPEED: JOYSTICK_SPEED,
            DYNAMIC_CONTENT_DIRECTION: direction,
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_JOYSTICK, request_data)

    def exit_navigation(self):
        request_data = {
            DYNAMIC_CONTENT_REMOTE_CONTROL_MODE: ATTR_REMOTE_CONTROL_MODE_EXIT
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_JOYSTICK, request_data)

    def _read_temperature_and_in_water_details(self):
        motor_unit_serial = self._api_data.get(API_DATA_SERIAL_NUMBER)
        serial_number = self._api_data.get(API_DATA_SERIAL_NUMBER)

        request_data = {
            DYNAMIC_CONTENT_SERIAL_NUMBER: serial_number,
            DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL: motor_unit_serial,
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_TEMPERATURE, request_data)

    def pickup(self):
        self.set_cleaning_mode(CleanModes.PICKUP)

    def set_power_state(self, is_on: bool):
        request_data = {
            DATA_SECTION_SYSTEM_STATE: {
                DATA_SYSTEM_STATE_PWS_STATE: PWS_STATE_ON if is_on else PWS_STATE_OFF
            }
        }

        _LOGGER.info(f"Set power state, Desired: {request_data}")
        self._send_desired_command(request_data)

    def reset_filter_indicator(self):
        request_data = {
            DATA_SECTION_FILTER_BAG_INDICATION: {
                DATA_FILTER_BAG_INDICATION_RESET_FBI_COMMAND: True
            }
        }

        _LOGGER.info(f"Reset filter bag indicator, Desired: {request_data}")
        self._send_desired_command(request_data)

    @staticmethod
    def _get_schedule_settings(enabled, mode, job_time):
        hours = DEFAULT_TIME_PART
        minutes = DEFAULT_TIME_PART

        if enabled and job_time is not None:
            job_time_parts = job_time.split(":")
            hours = int(job_time_parts[0])
            minutes = int(job_time_parts[1])

        data = {
            DATA_SCHEDULE_IS_ENABLED: enabled,
            DATA_SCHEDULE_CLEANING_MODE: {CONF_MODE: mode},
            DATA_SCHEDULE_TIME: {
                DATA_SCHEDULE_TIME_HOURS: hours,
                DATA_SCHEDULE_TIME_MINUTES: minutes,
            },
        }

        return data

    def _get_led_settings(self, key, value):
        default_data = {
            DATA_LED_ENABLE: DEFAULT_ENABLE,
            DATA_LED_INTENSITY: DEFAULT_LED_INTENSITY,
            DATA_LED_MODE: LED_MODE_BLINKING,
        }

        request_data = self.data.get(DATA_SECTION_LED, default_data)
        request_data[key] = value

        data = {DATA_SECTION_LED: request_data}

        return data

    def _set_status(self, status: ConnectivityStatus):
        if status != self._status:
            ignored_transitions = IGNORED_TRANSITIONS.get(self._status, [])

            if status in ignored_transitions:
                return

            log_level = ConnectivityStatus.get_log_level(status)

            _LOGGER.log(
                log_level,
                f"Status changed from '{self._status}' to '{status}'",
            )

            self._status = status

            self._async_dispatcher_send(
                SIGNAL_AWS_CLIENT_STATUS,
                self._config_manager.entry_id,
                status,
            )

    def set_local_async_dispatcher_send(self, callback):
        self._local_async_dispatcher_send = callback

    def _async_dispatcher_send(self, signal: str, *args: Any) -> None:
        if self._hass is None:
            self._local_async_dispatcher_send(signal, *args)

        else:
            async_dispatcher_send(self._hass, signal, *args)
