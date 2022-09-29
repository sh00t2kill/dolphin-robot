from __future__ import annotations

from datetime import datetime
import json
import logging
import os
import sys
from typing import Callable
import uuid

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import aiohttp
from aiohttp import ClientResponseError, ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from ...component.helpers.const import *
from ...component.helpers.exceptions import APIValidationException
from ...configuration.models.config_data import ConfigData
from ..helpers.common import get_date_time_from_timestamp
from ..helpers.enums import ConnectivityStatus
from ..models.topic_data import TopicData

REQUIREMENTS = ["aiohttp"]

_LOGGER = logging.getLogger(__name__)


class MyDolphinPlusAPI:
    session: ClientSession | None
    hass: HomeAssistant
    config_data: ConfigData
    base_url: str | None
    status: ConnectivityStatus | None

    login_token: str | None
    aws_token: str | None
    serial_number: str | None
    motor_unit_serial: str | None
    aws_token: str | None
    aws_key: str | None
    aws_secret: str | None
    awsiot_id: str | None
    awsiot_client: AWSIoTMQTTClient | None
    awsiot_client_status: ConnectivityStatus | None

    callback: Callable[[], None]

    server_version: int | None
    server_timestamp: int | None
    server_time_diff: int

    topic_data: TopicData | None

    def __init__(self, hass: HomeAssistant | None, config_data: ConfigData, callback: Callable[[], None] | None = None):
        try:
            self._last_update = datetime.now()
            self.hass = hass
            self.config_data = config_data
            self.session = None
            self.base_url = None

            self.awsiot_id = str(uuid.uuid4())
            self.status = ConnectivityStatus.NotConnected

            self.login_token = None
            self.aws_token = None
            self.serial_number = None
            self.motor_unit_serial = None
            self.aws_token = None
            self.aws_key = None
            self.aws_secret = None
            self.awsiot_id = None
            self.awsiot_client = None
            self.awsiot_client_status = ConnectivityStatus.NotConnected

            self.callback = callback
            self.data = {}

            self.server_version = None
            self.server_timestamp = None
            self.server_time_diff = 0

            self.topic_data = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load MyDolphin Plus API, error: {ex}, line: {line_number}"
            )

    async def terminate(self):
        self.status = ConnectivityStatus.Disconnected

    async def initialize(self, config_data: ConfigData | None = None):
        _LOGGER.info("Initializing MyDolphin Plus")

        try:
            if config_data is not None:
                self.config_data = config_data

            if self.hass is None:
                if self.session is not None:
                    await self.session.close()

                self.session = aiohttp.client.ClientSession()
            else:
                self.session = async_create_clientsession(hass=self.hass)

            await self._login()
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize MyDolphin Plus API ({self.base_url}), error: {ex}, line: {line_number}"
            )

    async def validate(self):
        _LOGGER.info("Initializing MyDolphin Plus")

        try:
            if self.hass is None:
                if self.session is not None:
                    await self.session.close()

                self.session = aiohttp.client.ClientSession()
            else:
                self.session = async_create_clientsession(hass=self.hass)

            await self._service_login()
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to validate login to MyDolphin Plus API ({self.base_url}), error: {ex}, line: {line_number}"
            )

    def _validate_request(self, endpoint):
        if not ConnectivityStatus.is_api_request_allowed(endpoint, self.status):
            raise APIValidationException(endpoint, self.status)

    async def _async_post(self, url, headers: dict, request_data: str | dict | None):
        result = None

        try:
            async with self.session.post(url, headers=headers, data=request_data, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                _LOGGER.debug(f"POST request [{url}] completed successfully, Result: {result}")

                self._last_update = datetime.now()

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to post JSON to {url}, HTTP Status: {crex.message} ({crex.status})"
            )

            if crex.status in [404, 405]:
                self.status = ConnectivityStatus.NotFound

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to post JSON to {url}, Error: {ex}, Line: {line_number}"
            )

            self.status = ConnectivityStatus.Failed

        return result

    async def _async_get(self, url, headers: dict):
        result = None

        try:
            async with self.session.get(url, headers=headers, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                _LOGGER.debug(f"GET request [{url}] completed successfully, Result: {result}")

                self._last_update = datetime.now()

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to get data from {url}, HTTP Status: {crex.message} ({crex.status})"
            )

            if crex.status in [404, 405]:
                self.status = ConnectivityStatus.NotFound

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {url}, Error: {ex}, Line: {line_number}"
            )

            self.status = ConnectivityStatus.Failed

        return result

    async def async_update(self):
        _LOGGER.info(f"Updating data from XXX)")

        if self.status == ConnectivityStatus.Failed:
            await self.initialize()

        self._refresh_details()

    async def _login(self):
        await self._service_login()
        await self._generate_token()

        self._connect_aws_iot_client()

        await self._load_details()

        for key in self.data:
            _LOGGER.info(f"{key}: {self.data[key]}")

        self._refresh_details()

    async def _service_login(self):
        try:
            self.status = ConnectivityStatus.Connecting
            username = self.config_data.username
            password = self.config_data.password

            request_data = f"Email={username}&Password={password}"

            payload = await self._async_post(LOGIN_URL, LOGIN_HEADERS, request_data)

            data = payload.get("Data", {})
            if data:
                motor_unit_serial = data.get("Sernum")
                token = data.get("token")

                actual_motor_unit_serial = motor_unit_serial[:-2]

                _LOGGER.debug(f"Device {motor_unit_serial} with token: {token}")

                self.motor_unit_serial = actual_motor_unit_serial
                self.login_token = token

                self.topic_data = TopicData(self.motor_unit_serial)

                self.status = ConnectivityStatus.TemporaryConnected

            else:
                self.status = ConnectivityStatus.Failed

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to login into {DEFAULT_NAME} service, Error: {str(ex)}, Line: {line_number}")
            self.status = ConnectivityStatus.Failed

    async def _generate_token(self):
        if self.status != ConnectivityStatus.TemporaryConnected:
            self.status = ConnectivityStatus.Failed
            return

        try:
            headers = {
                "token": self.login_token
            }

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = f"Sernum={self.motor_unit_serial}"

            payload = await self._async_post(TOKEN_URL, headers, request_data)

            data = payload.get("Data")

            self.aws_token = data.get("Token")
            self.aws_key = data.get("AccessKeyId")
            self.aws_secret = data.get("SecretAccessKey")

            _LOGGER.debug(f"Logged in to AWS using {self.aws_key}:{self.aws_secret}:{self.aws_token}")
            self.status = ConnectivityStatus.Connected

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed  to retrieve AWS token from service, Error: {str(ex)}, Line: {line_number}")
            self.status = ConnectivityStatus.Failed

    def _connect_aws_iot_client(self):
        if self.status != ConnectivityStatus.Connected:
            self.status = ConnectivityStatus.Failed
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
            aws_client.subscribe(topic, 0, self._internal_callback)

        connected = aws_client.connect()

        if connected:
            _LOGGER.debug(f"Connected to {AWS_IOT_URL}")
            self.awsiot_client = aws_client

        else:
            _LOGGER.error(f"Failed to connect to {AWS_IOT_URL}")
            self.status = ConnectivityStatus.Failed

    def _refresh_details(self):
        if self.status != ConnectivityStatus.Connected:
            self.status = ConnectivityStatus.Failed
            return

        self.awsiot_client.publish(self.topic_data.get, None, MQTT_QOS_AT_LEAST_ONCE)

    async def _load_details(self):
        if self.status != ConnectivityStatus.Connected:
            self.status = ConnectivityStatus.Failed
            return

        try:
            headers = {
                "token": self.login_token
            }

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = f"Sernum={self.motor_unit_serial}"

            payload = await self._async_post(ROBOT_DETAILS_URL, headers, request_data)

            response_status = payload.get("Status", "0")

            if response_status == "1":
                data = payload.get("Data", "0")
                self.serial_number = data.get("SERN")

                for key in DATA_ROBOT_DETAILS:
                    new_key = DATA_ROBOT_DETAILS.get(key)

                    self.data[new_key] = data.get(key)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to retrieve Robot Details, Error: {str(ex)}, Line: {line_number}")

    def _handle_aws_client_online(self):
        self.awsiot_client_status = ConnectivityStatus.Connected

    def _handle_aws_client_offline(self):
        self.awsiot_client_status = ConnectivityStatus.Disconnected

    def _internal_callback(self, client, userdata, message):
        try:
            message_topic: str = message.topic
            message_payload = message.payload.decode("utf-8")

            payload = json.loads(message_payload)

            _LOGGER.info(f"Message received for device {self.motor_unit_serial}, Topic: {message_topic}")

            if message_topic.endswith(TOPIC_CALLBACK_REJECTED):
                _LOGGER.warning(f"Rejected message for {message_topic}, Message: {payload}")

            elif message_topic == self.topic_data.dynamic:
                _LOGGER.debug(f"Dynamic payload: {payload}")

            elif message_topic == self.topic_data.update_accepted:
                self._refresh_details()

            elif message_topic == self.topic_data.get_accepted:
                now = datetime.now().timestamp()
                server_timestamp = payload.get(DATA_ROOT_TIMESTAMP)

                self.server_version = payload.get(DATA_ROOT_VERSION)
                self.server_timestamp = server_timestamp
                self.server_time_diff = now - server_timestamp

                state = payload.get(DATA_ROOT_STATE, {})
                reported = state.get(DATA_STATE_REPORTED, {})

                for category in reported.keys():
                    category_data = reported.get(category)

                    if category_data is not None:
                        _LOGGER.debug(f"{category} - {category_data}")
                        self.data[category] = category_data

                self._read_temperature_and_in_water_details()

                if self.callback is not None:
                    server_time = get_date_time_from_timestamp(self.server_timestamp)
                    local_time = get_date_time_from_timestamp(now)

                    _LOGGER.debug(f"Server Version: {self.server_version}")
                    _LOGGER.debug(f"Server Timestamp: {server_time} [{self.server_timestamp}]")
                    _LOGGER.debug(f"Local Timestamp: {local_time} [{self.server_timestamp}]")
                    _LOGGER.debug(f"Diff: {self.server_time_diff}")

                    self.callback()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Callback parsing failed, Data: {message}, Error: {str(ex)}, Line: {line_number}")

    @staticmethod
    def _string_join(data_items, delimiter):
        return delimiter.join(data_items)

    @staticmethod
    def _get_system_data_attribute(data, key):
        result = None

        system_data_attributes = data.get("L", [])
        if key in system_data_attributes:
            system_data_value = system_data_attributes[key]

            result = system_data_value.get("S")

        return result

    def _send_desired_command(self, payload: dict | None):
        data = {
            DATA_ROOT_STATE: {
                DATA_STATE_DESIRED: payload
            }
        }

        self._publish(self.topic_data.update, data)

    def _send_dynamic_command(self, payload: dict | None):
        data = {
            DYNAMIC_CONTENT: payload
        }

        self._publish(self.topic_data.dynamic, data)

    def _publish(self, topic: str, data: dict | None):
        payload = json.dumps(data)

        if self.status == ConnectivityStatus.Connected:
            try:
                self.awsiot_client.publish(topic, payload, MQTT_QOS_AT_LEAST_ONCE)
            except Exception as ex:
                _LOGGER.error(f"Error while trying to publish message: {data} to {topic}, Error: {str(ex)}")

        else:
            _LOGGER.error(f"Failed to publish message: {data} to {topic}")

    async def set_cleaning_mode(self, cleaning_mode):
        data = {
            DATA_SECTION_CYCLE_INFO: {
                DATA_SCHEDULE_CLEANING_MODE: {
                    CONF_MODE: cleaning_mode
                }
            }
        }

        _LOGGER.info(f"Set cleaning mode, Desired: {data}")
        self._send_desired_command(data)

    async def set_delay(self,
                        enabled: bool | None = False,
                        mode: str | None = CLEANING_MODE_REGULAR,
                        job_time: str | None = None):
        scheduling = self._get_schedule_settings(enabled, mode, job_time)

        request_data = {
            DATA_SECTION_DELAY: scheduling
        }

        _LOGGER.info(f"Set delay, Desired: {request_data}")
        self._send_desired_command(request_data)

    async def set_schedule(self,
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

    async def set_led_mode(self, mode: int):
        data = self._get_led_settings(DATA_LED_MODE, mode)

        _LOGGER.info(f"Set led mode, Desired: {data}")
        self._send_desired_command(data)

    async def set_led_intensity(self, intensity: int):
        data = self._get_led_settings(DATA_LED_INTENSITY, intensity)

        _LOGGER.info(f"Set led intensity, Desired: {data}")
        self._send_desired_command(data)

    async def set_led_enabled(self, is_enabled: bool):
        data = self._get_led_settings(DATA_LED_ENABLE, is_enabled)

        _LOGGER.info(f"Set led enabled mode, Desired: {data}")
        self._send_desired_command(data)

    async def navigate(self, direction: str):
        request_data = {
            DYNAMIC_CONTENT_SPEED: JOYSTICK_SPEED,
            DYNAMIC_CONTENT_DIRECTION: direction
        }

        self._send_dynamic_command(request_data)

    async def quit_navigation(self):
        request_data = {
            DYNAMIC_CONTENT_REMOTE_CONTROL_MODE: ATTR_REMOTE_CONTROL_MODE_EXIT
        }

        self._send_dynamic_command(request_data)

    def _read_temperature_and_in_water_details(self):
        request_data = {
            DYNAMIC_CONTENT_SERIAL_NUMBER: self.serial_number,
            DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL: self.motor_unit_serial
        }

        self._send_dynamic_command(request_data)

    async def pickup(self):
        await self.set_cleaning_mode(CLEANING_MODE_PICKUP)

    async def set_power_state(self, is_on: bool):
        request_data = {
            DATA_SECTION_SYSTEM_STATE: {
                DATA_SYSTEM_STATE_PWS_STATE: PWS_STATE_ON if is_on else PWS_STATE_OFF
            }
        }

        _LOGGER.info(f"Set power state, Desired: {request_data}")
        self._send_desired_command(request_data)

    async def reset_filter_indicator(self):
        request_data = {
            DATA_SECTION_FILTER_BAG_INDICATION: {
                DATA_FILTER_BAG_INDICATION_RESET_FBI_COMMAND: True
            }
        }

        _LOGGER.info(f"Reset filter bag indicator, Desired: {request_data}")
        await self._send_desired_command(request_data)

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
