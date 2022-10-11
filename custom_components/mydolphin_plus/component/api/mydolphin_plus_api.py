from __future__ import annotations

from datetime import datetime
import json
import logging
import os
import sys
from typing import Awaitable, Callable
import uuid

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import aiohttp
from aiohttp import ClientResponseError, ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ...configuration.models.config_data import ConfigData
from ...core.api.base_api import BaseAPI
from ...core.helpers.enums import ConnectivityStatus
from ..helpers.const import *
from ..models.topic_data import TopicData

REQUIREMENTS = ["aiohttp"]

_LOGGER = logging.getLogger(__name__)


class IntegrationAPI(BaseAPI):
    session: ClientSession | None
    hass: HomeAssistant | None
    config_data: ConfigData | None
    base_url: str | None

    login_token: str | None
    aws_token: str | None
    serial_number: str | None
    motor_unit_serial: str | None
    aws_token: str | None
    aws_key: str | None
    aws_secret: str | None
    awsiot_id: str | None
    awsiot_client: AWSIoTMQTTClient | None

    callback: Callable[[], None]

    server_version: int | None
    server_timestamp: float | None
    server_time_diff: float

    topic_data: TopicData | None
    last_update: float | None

    def __init__(self,
                 hass: HomeAssistant | None,
                 async_on_data_changed: Callable[[], Awaitable[None]] | None = None,
                 async_on_status_changed: Callable[[ConnectivityStatus], Awaitable[None]] | None = None
                 ):

        super().__init__(hass, async_on_data_changed, async_on_status_changed)

        try:
            self.hass = hass
            self.config_data = None
            self.session = None
            self.base_url = None

            self.awsiot_id = str(uuid.uuid4())

            self.login_token = None
            self.aws_token = None
            self.serial_number = None
            self.motor_unit_serial = None
            self.aws_token = None
            self.aws_key = None
            self.aws_secret = None
            self.awsiot_id = None
            self.awsiot_client = None

            self.server_version = None
            self.server_timestamp = None
            self.server_time_diff = 0

            self.topic_data = None
            self.last_update = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load MyDolphin Plus API, error: {ex}, line: {line_number}"
            )

    async def terminate(self):
        if self.awsiot_client is not None:
            self.awsiot_client.disconnectAsync(self._ack_callback)

        await self._handle_aws_client_status_changed(ConnectivityStatus.Disconnected)

        await self.set_status(ConnectivityStatus.Disconnected)

    async def initialize(self, config_data: ConfigData):
        _LOGGER.info("Initializing MyDolphin API")

        await self._session_initialize(config_data)

        await self._login()

    async def validate(self, data: dict | None = None):
        config_data = ConfigData.from_dict(data)

        await self._session_initialize(config_data)

        await self._service_login()

    async def _session_initialize(self, config_data: ConfigData):
        _LOGGER.info("Initializing MyDolphin API Session")

        try:
            self.config_data = config_data

            if self.hass is None:
                if self.session is not None:
                    await self.session.close()

                self.session = aiohttp.client.ClientSession()
            else:
                self.session = async_create_clientsession(hass=self.hass)
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize MyDolphin Plus API ({self.base_url}), error: {ex}, line: {line_number}"
            )

    async def _async_post(self, url, headers: dict, request_data: str | dict | None):
        result = None

        try:
            async with self.session.post(url, headers=headers, data=request_data, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                _LOGGER.debug(f"POST request [{url}] completed successfully, Result: {result}")

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to post JSON to {url}, HTTP Status: {crex.message} ({crex.status})"
            )

            if crex.status in [404, 405]:
                await self.set_status(ConnectivityStatus.NotFound)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to post JSON to {url}, Error: {ex}, Line: {line_number}"
            )

            await self.set_status(ConnectivityStatus.Failed)

        return result

    async def _async_get(self, url, headers: dict):
        result = None

        try:
            async with self.session.get(url, headers=headers, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                _LOGGER.debug(f"GET request [{url}] completed successfully, Result: {result}")

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to get data from {url}, HTTP Status: {crex.message} ({crex.status})"
            )

            if crex.status in [404, 405]:
                await self.set_status(ConnectivityStatus.NotFound)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {url}, Error: {ex}, Line: {line_number}"
            )

            await self.set_status(ConnectivityStatus.Failed)

        return result

    async def async_update(self):
        _LOGGER.info(f"Updating data from MyDolphin Plus AWSIOTHUB")
        _LOGGER.debug(f"Current status: {self.status}")

        if self.status == ConnectivityStatus.Failed:
            _LOGGER.debug("Connection failed. Reinitialize")
            await self.initialize(self.config_data)

        if self.status == ConnectivityStatus.Connected:
            _LOGGER.debug("Connected. Refresh details")
            await self._refresh_details()

    async def _login(self):
        await self._service_login()
        await self._generate_token()

        await self._connect_aws_iot_client()

        await self._load_details()

        for key in self.data:
            _LOGGER.info(f"{key}: {self.data[key]}")

        await self._refresh_details()

    async def _service_login(self):
        try:
            await self.set_status(ConnectivityStatus.Connecting)

            username = self.config_data.username
            password = self.config_data.password

            request_data = f"{API_REQUEST_SERIAL_EMAIL}={username}&{API_REQUEST_SERIAL_PASSWORD}={password}"

            payload = await self._async_post(LOGIN_URL, LOGIN_HEADERS, request_data)

            if payload is None:
                payload = {}

            data = payload.get(API_RESPONSE_DATA, {})
            if data:
                motor_unit_serial = data.get(API_REQUEST_SERIAL_NUMBER)
                token = data.get(API_REQUEST_HEADER_TOKEN)

                actual_motor_unit_serial = motor_unit_serial[:-2]

                _LOGGER.debug(f"Device {motor_unit_serial} with token: {token}")

                self.motor_unit_serial = actual_motor_unit_serial
                self.serial_number = motor_unit_serial
                self.login_token = token

                self.topic_data = TopicData(self.motor_unit_serial)

                await self.set_status(ConnectivityStatus.TemporaryConnected)

            else:
                await self.set_status(ConnectivityStatus.Failed)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to login into {DEFAULT_NAME} service, Error: {str(ex)}, Line: {line_number}")
            await self.set_status(ConnectivityStatus.Failed)

    async def _generate_token(self):
        if self.status != ConnectivityStatus.TemporaryConnected:
            await self.set_status(ConnectivityStatus.Failed)
            return

        try:
            headers = {
                API_REQUEST_HEADER_TOKEN: self.login_token
            }

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = f"{API_REQUEST_SERIAL_NUMBER}={self.motor_unit_serial}"

            payload = await self._async_post(TOKEN_URL, headers, request_data)

            data = payload.get(API_RESPONSE_DATA, {})

            self.aws_token = data.get(API_RESPONSE_DATA_TOKEN)
            self.aws_key = data.get(API_RESPONSE_DATA_ACCESS_KEY_ID)
            self.aws_secret = data.get(API_RESPONSE_DATA_SECRET_ACCESS_KEY)

            _LOGGER.debug(f"Logged in to AWS using {self.aws_key}:{self.aws_secret}:{self.aws_token}")
            await self.set_status(ConnectivityStatus.Connected)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed  to retrieve AWS token from service, Error: {str(ex)}, Line: {line_number}")
            await self.set_status(ConnectivityStatus.Failed)

    async def _connect_aws_iot_client(self):
        if self.status != ConnectivityStatus.Connected:
            await self.set_status(ConnectivityStatus.Failed)
            return

        script_dir = os.path.dirname(__file__)
        ca_file_path = os.path.join(script_dir, CA_FILE_NAME)

        _LOGGER.debug(f"Loading CA file from {ca_file_path}")

        aws_client = AWSIoTMQTTClient(self.awsiot_id, useWebsocket=True)
        aws_client.configureEndpoint(AWS_IOT_URL, AWS_IOT_PORT)
        aws_client.configureCredentials(ca_file_path)
        aws_client.configureIAMCredentials(self.aws_key, self.aws_secret, self.aws_token)
        aws_client.configureAutoReconnectBackoffTime(1, 32, 20)
        aws_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        aws_client.configureDrainingFrequency(2)  # Draining: 2 Hz
        aws_client.configureConnectDisconnectTimeout(10)
        aws_client.configureMQTTOperationTimeout(10)
        aws_client.enableMetricsCollection()
        aws_client.onOnline = self._handle_aws_client_online
        aws_client.onOffline = self._handle_aws_client_offline

        for topic in self.topic_data.subscribe:
            aws_client.subscribeAsync(topic, MQTT_QOS_0, self._ack_callback, self._message_callback)

        connected = aws_client.connectAsync(ackCallback=self._ack_callback)

        if connected:
            _LOGGER.debug(f"Connected to {AWS_IOT_URL}")
            self.awsiot_client = aws_client

        else:
            _LOGGER.error(f"Failed to connect to {AWS_IOT_URL}")
            await self.set_status(ConnectivityStatus.Failed)

    async def _refresh_details(self, forced: bool = False):
        if self.status != ConnectivityStatus.Connected:
            await self.set_status(ConnectivityStatus.Failed)
            return

        now = datetime.now().timestamp()
        last_update = 0 if self.last_update is None else self.last_update

        diff_seconds = now - last_update

        if forced or diff_seconds >= SCAN_INTERVAL.total_seconds():
            self.last_update = now

            self._publish(self.topic_data.get, None)

    async def _load_details(self):
        if self.status != ConnectivityStatus.Connected:
            await self.set_status(ConnectivityStatus.Failed)
            return

        try:
            headers = {
                API_REQUEST_HEADER_TOKEN: self.login_token
            }

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = f"{API_REQUEST_SERIAL_NUMBER}={self.motor_unit_serial}"

            payload = await self._async_post(ROBOT_DETAILS_URL, headers, request_data)

            response_status = payload.get(API_RESPONSE_STATUS, API_RESPONSE_STATUS_FAILURE)

            if response_status == API_RESPONSE_STATUS_SUCCESS:
                data = payload.get(API_RESPONSE_DATA, {})

                for key in DATA_ROBOT_DETAILS:
                    new_key = DATA_ROBOT_DETAILS.get(key)

                    self.data[new_key] = data.get(key)

            await self.fire_data_changed_event()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to retrieve Robot Details, Error: {str(ex)}, Line: {line_number}")

    def _handle_aws_client_online(self):
        self.hass.async_create_task(self._handle_aws_client_status_changed(ConnectivityStatus.Connected))

    def _handle_aws_client_offline(self):
        self.hass.async_create_task(self._handle_aws_client_status_changed(ConnectivityStatus.Disconnected))

    async def _handle_aws_client_status_changed(self, status: ConnectivityStatus):
        self.data[ATTR_AWS_IOT_BROKER_STATUS] = status

        await self.fire_data_changed_event()

    @staticmethod
    def _ack_callback(mid, data):
        _LOGGER.debug(f"ACK packet ID: {mid}, QoS: {data}")

    def _message_callback(self, client, userdata, message):
        message_topic: str = message.topic
        message_payload = message.payload.decode(MQTT_MESSAGE_ENCODING)

        try:
            has_message = len(message_payload) <= 0
            payload = {} if has_message else json.loads(message_payload)

            _LOGGER.info(f"Message received for device {self.motor_unit_serial}, Topic: {message_topic}")

            if message_topic.endswith(TOPIC_CALLBACK_REJECTED):
                _LOGGER.warning(f"Rejected message for {message_topic}, Message: {message_payload}")

            elif message_topic == self.topic_data.dynamic:
                _LOGGER.debug(f"Dynamic payload: {message_payload}")

            elif message_topic.endswith(TOPIC_CALLBACK_ACCEPTED):
                _LOGGER.debug(f"Payload: {message_payload}")

                now = datetime.now().timestamp()

                self.server_version = payload.get(DATA_ROOT_VERSION)
                self.server_timestamp = payload.get(DATA_ROOT_TIMESTAMP)

                self.server_time_diff = now - self.server_timestamp

                state = payload.get(DATA_ROOT_STATE, {})
                reported = state.get(DATA_STATE_REPORTED, {})

                for category in reported.keys():
                    category_data = reported.get(category)

                    if category_data is not None:
                        self.data[category] = category_data

                if message_topic == self.topic_data.get_accepted:
                    self._read_temperature_and_in_water_details()

                self.hass.async_create_task(self.fire_data_changed_event())

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno
            message_details = f"Topic: {message_topic}, Data: {message_payload}"
            error_details = f"Error: {str(ex)}, Line: {line_number}"

            _LOGGER.error(f"Callback parsing failed, {message_details}, {error_details}")

    def _send_desired_command(self, payload: dict | None):
        data = {
            DATA_ROOT_STATE: {
                DATA_STATE_DESIRED: payload
            }
        }

        self._publish(self.topic_data.update, data)

    def _send_dynamic_command(self, description: str, payload: dict | None):
        payload[DYNAMIC_TYPE] = DYNAMIC_TYPE_PWS_REQUEST
        payload[DYNAMIC_DESCRIPTION] = description

        self._publish(self.topic_data.dynamic, payload)

    def _publish(self, topic: str, data: dict | None):
        payload = "" if data is None else json.dumps(data)

        if self.status == ConnectivityStatus.Connected:
            try:
                if self.awsiot_client is not None:
                    self.awsiot_client.publishAsync(topic, payload, MQTT_QOS_1)
                    _LOGGER.debug(f"Success:: published message: {data} to {topic}")

            except Exception as ex:
                _LOGGER.error(f"Error while trying to publish message: {data} to {topic}, Error: {str(ex)}")

        else:
            _LOGGER.error(f"Failed to publish message: {data} to {topic}, Broker is not connected")

    def set_cleaning_mode(self, cleaning_mode):
        data = {
            DATA_SECTION_CYCLE_INFO: {
                DATA_SCHEDULE_CLEANING_MODE: {
                    CONF_MODE: cleaning_mode
                }
            }
        }

        _LOGGER.info(f"Set cleaning mode, Desired: {data}")
        self._send_desired_command(data)

    def set_delay(self,
                  enabled: bool | None = False,
                  mode: str | None = CLEANING_MODE_REGULAR,
                  job_time: str | None = None):
        scheduling = self._get_schedule_settings(enabled, mode, job_time)

        request_data = {
            DATA_SECTION_DELAY: scheduling
        }

        _LOGGER.info(f"Set delay, Desired: {request_data}")
        self._send_desired_command(request_data)

    def set_schedule(self,
                     day: str,
                     enabled: bool | None = False,
                     mode: str | None = CLEANING_MODE_REGULAR,
                     job_time: str | None = None):
        scheduling = self._get_schedule_settings(enabled, mode, job_time)

        request_data = {
            DATA_SECTION_WEEKLY_SETTINGS: {
                DATA_SCHEDULE_TRIGGERED_BY: 0,
                day: scheduling
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
            DYNAMIC_CONTENT_DIRECTION: direction
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_JOYSTICK, request_data)

    def quit_navigation(self):
        request_data = {
            DYNAMIC_CONTENT_REMOTE_CONTROL_MODE: ATTR_REMOTE_CONTROL_MODE_EXIT
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_JOYSTICK, request_data)

    def _read_temperature_and_in_water_details(self):
        request_data = {
            DYNAMIC_CONTENT_SERIAL_NUMBER: self.serial_number,
            DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL: self.motor_unit_serial
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
            DATA_SCHEDULE_CLEANING_MODE: {
                CONF_MODE: mode
            },
            DATA_SCHEDULE_TIME: {
                DATA_SCHEDULE_TIME_HOURS: hours,
                DATA_SCHEDULE_TIME_MINUTES: minutes
            }
        }

        return data

    def _get_led_settings(self, key, value):
        default_data = {
            DATA_LED_ENABLE: DEFAULT_ENABLE,
            DATA_LED_INTENSITY: DEFAULT_LED_INTENSITY,
            DATA_LED_MODE: LED_MODE_BLINKING
        }

        request_data = self.data.get(DATA_SECTION_LED, default_data)
        request_data[key] = value

        data = {
            DATA_SECTION_LED: request_data
        }

        return data
