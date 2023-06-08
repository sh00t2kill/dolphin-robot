from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
import json
import logging
import os
import sys
import uuid

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

from homeassistant.const import CONF_MODE
from homeassistant.core import HomeAssistant

from ...configuration.models.config_data import ConfigData
from ...core.api.base_api import BaseAPI
from ...core.helpers.enums import ConnectivityStatus
from ..helpers.const import (
    API_DATA_MOTOR_UNIT_SERIAL,
    API_DATA_SERIAL_NUMBER,
    API_RESPONSE_DATA_ACCESS_KEY_ID,
    API_RESPONSE_DATA_SECRET_ACCESS_KEY,
    API_RESPONSE_DATA_TOKEN,
    ATTR_REMOTE_CONTROL_MODE_EXIT,
    AWS_IOT_PORT,
    AWS_IOT_URL,
    CA_FILE_NAME,
    CLEANING_MODE_PICKUP,
    CLEANING_MODE_REGULAR,
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
    DATA_SCHEDULE_TRIGGERED_BY,
    DATA_SECTION_CYCLE_INFO,
    DATA_SECTION_DELAY,
    DATA_SECTION_FILTER_BAG_INDICATION,
    DATA_SECTION_LED,
    DATA_SECTION_SYSTEM_STATE,
    DATA_SECTION_WEEKLY_SETTINGS,
    DATA_STATE_DESIRED,
    DATA_STATE_REPORTED,
    DATA_SYSTEM_STATE_PWS_STATE,
    DEFAULT_ENABLE,
    DEFAULT_LED_INTENSITY,
    DEFAULT_TIME_PART,
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
    TOPIC_CALLBACK_ACCEPTED,
    TOPIC_CALLBACK_REJECTED,
    UPDATE_API_INTERVAL,
    WS_DATA_DIFF,
    WS_DATA_TIMESTAMP,
    WS_DATA_VERSION,
    WS_LAST_UPDATE,
)
from ..models.topic_data import TopicData

_LOGGER = logging.getLogger(__name__)


class IntegrationWS(BaseAPI):
    _config_data: ConfigData | None

    _awsiot_client: AWSIoTMQTTClient | None

    _topic_data: TopicData | None

    def __init__(
        self,
        hass: HomeAssistant | None,
        async_on_data_changed: Callable[[], Awaitable[None]] | None = None,
        async_on_status_changed: Callable[[ConnectivityStatus], Awaitable[None]]
        | None = None,
    ):
        super().__init__(hass, async_on_data_changed, async_on_status_changed)

        try:
            self._config_data = None

            self._api_data = {}

            self._topic_data = None
            self._awsiot_client = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load MyDolphin Plus WS, error: {ex}, line: {line_number}"
            )

    @property
    def has_running_loop(self):
        return self.hass.loop is not None and not self.hass.loop.is_closed()

    async def terminate(self):
        await super().terminate()

        if self._awsiot_client is not None:
            self._awsiot_client.disconnectAsync(self._ack_callback)

    async def initialize(self, config_data: ConfigData):
        try:
            _LOGGER.info("Initializing MyDolphin AWS IOT WS")
            self._config_data = config_data

            await self.set_status(ConnectivityStatus.Connecting)

            awsiot_id = str(uuid.uuid4())
            aws_token = self._api_data.get(API_RESPONSE_DATA_TOKEN)
            aws_key = self._api_data.get(API_RESPONSE_DATA_ACCESS_KEY_ID)
            aws_secret = self._api_data.get(API_RESPONSE_DATA_SECRET_ACCESS_KEY)

            _LOGGER.debug(f"AWS IAM Credentials {aws_key}:{aws_secret}:{aws_token}")

            motor_unit_serial = self._api_data.get(API_DATA_MOTOR_UNIT_SERIAL)

            self._topic_data = TopicData(motor_unit_serial)

            script_dir = os.path.dirname(__file__)
            ca_file_path = os.path.join(script_dir, CA_FILE_NAME)

            _LOGGER.debug(f"Loading CA file from {ca_file_path}")

            aws_client = AWSIoTMQTTClient(awsiot_id, useWebsocket=True)
            aws_client.configureEndpoint(AWS_IOT_URL, AWS_IOT_PORT)
            aws_client.configureCredentials(ca_file_path)
            aws_client.configureIAMCredentials(aws_key, aws_secret, aws_token)
            aws_client.configureAutoReconnectBackoffTime(1, 32, 20)
            aws_client.configureOfflinePublishQueueing(
                -1
            )  # Infinite offline Publish queueing
            aws_client.configureDrainingFrequency(2)  # Draining: 2 Hz
            aws_client.configureConnectDisconnectTimeout(10)
            aws_client.configureMQTTOperationTimeout(10)
            aws_client.enableMetricsCollection()
            aws_client.onOnline = self._handle_aws_client_online
            aws_client.onOffline = self._handle_aws_client_offline

            for topic in self._topic_data.subscribe:
                aws_client.subscribeAsync(
                    topic, MQTT_QOS_0, self._ack_callback, self._message_callback
                )

            connected = aws_client.connectAsync(ackCallback=self._ack_callback)

            if connected:
                _LOGGER.debug(f"Connected to {AWS_IOT_URL}")
                self._awsiot_client = aws_client

            else:
                _LOGGER.error(f"Failed to connect to {AWS_IOT_URL}")
                await self.set_status(ConnectivityStatus.Failed)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize MyDolphin Plus WS, error: {ex}, line: {line_number}"
            )

            await self.set_status(ConnectivityStatus.Failed)

    async def update_api_data(self, api_data: dict):
        self._api_data = api_data

    async def async_update(self):
        if self.status == ConnectivityStatus.Connected:
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

        if self.is_home_assistant:
            if self.has_running_loop:
                self.hass.async_create_task(
                    self.set_status(ConnectivityStatus.Connected)
                )

        else:
            loop = asyncio.get_running_loop()
            loop.create_task(self.set_status(ConnectivityStatus.Connected))

    def _handle_aws_client_offline(self):
        _LOGGER.debug("AWS IOT Client is Offline")

        if self.is_home_assistant:
            if self.has_running_loop:
                self.hass.async_create_task(self.set_status(ConnectivityStatus.Failed))

        else:
            loop = asyncio.get_running_loop()
            loop.create_task(self.set_status(ConnectivityStatus.Failed))

    @staticmethod
    def _ack_callback(mid, data):
        _LOGGER.debug(f"ACK packet ID: {mid}, QoS: {data}")

    def _message_callback(self, client, userdata, message):
        message_topic: str = message.topic
        message_payload = message.payload.decode(MQTT_MESSAGE_ENCODING)

        try:
            has_message = len(message_payload) <= 0
            payload = {} if has_message else json.loads(message_payload)

            motor_unit_serial = self._api_data.get(API_DATA_SERIAL_NUMBER)
            _LOGGER.info(
                f"Message received for device {motor_unit_serial}, Topic: {message_topic}"
            )

            if message_topic.endswith(TOPIC_CALLBACK_REJECTED):
                _LOGGER.warning(
                    f"Rejected message for {message_topic}, Message: {message_payload}"
                )

            elif message_topic == self._topic_data.dynamic:
                _LOGGER.debug(f"Dynamic payload: {message_payload}")

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
                        self.data[category] = category_data

                if message_topic == self._topic_data.get_accepted:
                    self._read_temperature_and_in_water_details()

                if self.is_home_assistant:
                    if self.has_running_loop:
                        self.hass.async_create_task(self.fire_data_changed_event())

                else:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.fire_data_changed_event())

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

        if self.status == ConnectivityStatus.Connected:
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

    def set_cleaning_mode(self, cleaning_mode):
        data = {
            DATA_SECTION_CYCLE_INFO: {
                DATA_SCHEDULE_CLEANING_MODE: {CONF_MODE: cleaning_mode}
            }
        }

        _LOGGER.info(f"Set cleaning mode, Desired: {data}")
        self._send_desired_command(data)

    def set_delay(
        self,
        enabled: bool | None = False,
        mode: str | None = CLEANING_MODE_REGULAR,
        job_time: str | None = None,
    ):
        scheduling = self._get_schedule_settings(enabled, mode, job_time)

        request_data = {DATA_SECTION_DELAY: scheduling}

        _LOGGER.info(f"Set delay, Desired: {request_data}")
        self._send_desired_command(request_data)

    def set_schedule(
        self,
        day: str,
        enabled: bool | None = False,
        mode: str | None = CLEANING_MODE_REGULAR,
        job_time: str | None = None,
    ):
        scheduling = self._get_schedule_settings(enabled, mode, job_time)

        request_data = {
            DATA_SECTION_WEEKLY_SETTINGS: {
                DATA_SCHEDULE_TRIGGERED_BY: 0,
                day: scheduling,
            }
        }

        _LOGGER.info(f"Set schedule, Desired: {request_data}")
        self._send_desired_command(request_data)

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

    def quit_navigation(self):
        request_data = {
            DYNAMIC_CONTENT_REMOTE_CONTROL_MODE: ATTR_REMOTE_CONTROL_MODE_EXIT
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_JOYSTICK, request_data)

    def _read_temperature_and_in_water_details(self):
        motor_unit_serial = self.data.get(API_DATA_SERIAL_NUMBER)
        serial_number = self.data.get(API_DATA_SERIAL_NUMBER)

        request_data = {
            DYNAMIC_CONTENT_SERIAL_NUMBER: serial_number,
            DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL: motor_unit_serial,
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_TEMPERATURE, request_data)

    def pickup(self):
        self.set_cleaning_mode(CLEANING_MODE_PICKUP)

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
