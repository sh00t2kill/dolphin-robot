from __future__ import annotations

from datetime import datetime
import hashlib
import hmac
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
    serial: str | None
    aws_token: str | None
    aws_key: str | None
    aws_secret: str | None
    awsiot_id: str | None
    awsiot_client: AWSIoTMQTTClient | None

    callback: Callable[[], None]

    server_version: int | None
    server_timestamp: int | None
    server_time_diff: int

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
            self.serial = None
            self.aws_token = None
            self.aws_key = None
            self.aws_secret = None
            self.awsiot_id = None
            self.awsiot_client = None

            self.callback = callback
            self.data = {}

            self.server_version = None
            self.server_timestamp = None
            self.server_time_diff = 0

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
        await self._aws_login()

        self._connect_aws_iot_client()

        await self._load_details()

        for key in self.data:
            _LOGGER.info(f"{key}: {self.data[key]}")

        self._listen()

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
                serial = data.get("Sernum")
                token = data.get("token")

                actual_serial = serial[:-2]

                _LOGGER.debug(f"Device {serial} with token: {token}")

                self.serial = actual_serial
                self.login_token = token

                self.status = ConnectivityStatus.TemporaryConnected

            else:
                self.status = ConnectivityStatus.Failed

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to login into {DEFAULT_NAME} service, Error: {str(ex)}, Line: {line_number}")
            self.status = ConnectivityStatus.Failed

    async def _aws_login(self):
        if self.status != ConnectivityStatus.TemporaryConnected:
            self.status = ConnectivityStatus.Failed
            return

        try:
            headers = {
                "token": self.login_token
            }

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = f"Sernum={self.serial}"

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

    def _refresh_details(self):
        if self.status != ConnectivityStatus.Connected:
            self.status = ConnectivityStatus.Failed
            return

        get_topic = TOPIC_GET.replace("/#", "").replace("{}", self.serial)

        self.awsiot_client.publish(get_topic, None, 0)

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

            request_data = f"Sernum={self.serial}"

            payload = await self._async_post(ROBOT_DETAILS_URL, headers, request_data)

            response_status = payload.get("Status", "0")

            if response_status == "1":
                data = payload.get("Data", "0")

                for key in DATA_ROBOT_DETAILS:
                    new_key = DATA_ROBOT_DETAILS.get(key)

                    self.data[new_key] = data.get(key)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to retrieve Robot Details, Error: {str(ex)}, Line: {line_number}")

    def get_signature_key(self, key, date_stamp, service_name):
        """
        This is pretty much straight out of AWS documentation RE creating a signature.
        I'm not convinced its doing anything but every time it gets touched, things break
        """

        aws_key = f"AWS4{key}".encode()

        date_key = self._sign(aws_key, date_stamp)
        region_key = self._sign(date_key, AWS_REGION)
        service_key = self._sign(region_key, service_name)

        full_signature = self._sign(service_key, AWS_REQUEST_KEY)

        return full_signature

    def get_aws_header(self, service, payload):
        current_time = datetime.now()
        amz_date = current_time.strftime(AWS_DATE_TIME_FORMAT)
        date_stamp = current_time.strftime(AWS_DATE_FORMAT)

        signature_key = self.get_signature_key(self.aws_secret, date_stamp, service)

        headers = {
            AWS_HEADER_CONTENT_TYPE: AWS_CONTENT_TYPE,
            AWS_HEADER_HOST: DYNAMODB_HOST,
            AWS_HEADER_DATE: amz_date,
            AWS_HEADER_TARGET: AMZ_TARGET
        }

        aws_signed_header_keys = self._string_join(headers.keys(), ";")
        aws_header_items = []

        for key in headers:
            value = headers.get(key)
            aws_header_items.append(f"{key}:{value}")

        aws_headers_content = self._string_join(aws_header_items, "\n")
        aws_headers_data = f"{aws_headers_content}\n"

        payload_hash = self._hash_sha256(payload)

        canonical_request = f"{AWS_METHOD}\n{aws_headers_data}\n{aws_signed_header_keys}\n{payload_hash}"

        scope_data = [date_stamp, AWS_REGION, service, AWS_REQUEST_KEY]
        credential_scope = self._string_join(scope_data, "/")

        canonical_request_hash = self._hash_sha256(canonical_request)

        data_to_sign = [AWS_ALGORITHM, amz_date, credential_scope, canonical_request_hash]
        string_to_sign = self._string_join(data_to_sign, "\n")

        signature = self._sign_hex(signature_key, string_to_sign)

        authorization_header = (
            f"{AWS_ALGORITHM} Credential={self.aws_key}/{credential_scope}, "
            f"SignedHeaders={aws_signed_header_keys}, "
            f"Signature={signature}"
        )

        aws_headers = {
            "Content-Type": AWS_CONTENT_TYPE,
            "X-Amz-Date": amz_date,
            "X-Amz-Target": AMZ_TARGET,
            "Authorization": authorization_header,
            "X-Amz-Security-Token": self.aws_token
        }

        return aws_headers

    def _connect_aws_iot_client(self):
        if self.status != ConnectivityStatus.Connected:
            self.status = ConnectivityStatus.Failed
            return

        script_dir = os.path.dirname(__file__)
        ca_file_path = os.path.join(script_dir, CA_FILE_NAME)

        _LOGGER.debug(f"Loading CA file from {ca_file_path}")

        aws_client = AWSIoTMQTTClient(self.awsiot_id, useWebsocket=True)
        aws_client.configureEndpoint(IOT_URL, 443)
        aws_client.configureCredentials(ca_file_path)
        aws_client.configureIAMCredentials(self.aws_key, self.aws_secret, self.aws_token)
        aws_client.configureAutoReconnectBackoffTime(1, 32, 20)
        aws_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        aws_client.configureDrainingFrequency(2)  # Draining: 2 Hz
        aws_client.configureConnectDisconnectTimeout(10)
        aws_client.configureMQTTOperationTimeout(5)
        aws_client.enableMetricsCollection()

        _LOGGER.debug(f"Connecting to {IOT_URL}")
        connected = aws_client.connect()

        _LOGGER.debug("Connected!!!")

        if connected:
            self.awsiot_client = aws_client

        else:
            _LOGGER.error("Failed to connect to IOT client")
            self.status = ConnectivityStatus.Failed

    def _listen(self):
        if self.status != ConnectivityStatus.Connected:
            self.status = ConnectivityStatus.Failed
            return

        for topic in TOPICS:
            fixed_topic = topic.format(self.serial)

            self.awsiot_client.subscribe(fixed_topic, 0, self._internal_callback)

    def _publish(self, topic, message):
        if self.status == ConnectivityStatus.Connected:
            self.awsiot_client.publish(topic, message, 0)

        else:
            _LOGGER.error(f"Failed to publish message: {message} to {topic}")

    def _internal_callback(self, client, userdata, message):
        try:
            message_topic = message.topic
            message_payload = message.payload.decode("utf-8")

            payload = json.loads(message_payload)

            _LOGGER.info(f"Message received for device {self.serial}, Topic: {message_topic}")

            if message_topic.endswith("update/accepted"):
                self._refresh_details()

            elif message_topic.endswith("get/accepted"):
                now = datetime.now().timestamp()
                server_timestamp = payload.get("timestamp")

                self.server_version = payload.get("version")
                self.server_timestamp = server_timestamp
                self.server_time_diff = now - server_timestamp

                state = payload.get("state", {})
                reported = state.get("reported", {})

                for category in reported.keys():
                    category_data = reported.get(category)

                    if category_data is not None:
                        _LOGGER.debug(f"{category} - {category_data}")
                        self.data[category] = category_data

                if self.callback is not None:
                    _LOGGER.debug(f"Server Version: {self.server_version}")
                    _LOGGER.debug(f"Server Timestamp: {get_date_time_from_timestamp(self.server_timestamp)} [{self.server_timestamp}]")
                    _LOGGER.debug(f"Local Timestamp: {get_date_time_from_timestamp(now)} [{self.server_timestamp}]")
                    _LOGGER.debug(f"Diff: {self.server_time_diff}")

                    self.callback()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Callback parsing failed, Data: {message}, Error: {str(ex)}, Line: {line_number}")

    def _sign_hex(self, key, data):
        result = self._internal_sign(key, data).hexdigest()

        return result

    def _sign(self, key, data):
        result = self._internal_sign(key, data).digest()

        return result

    @staticmethod
    def _string_join(data_items, delimiter):
        return delimiter.join(data_items)

    @staticmethod
    def _internal_sign(key, data):
        result = hmac.new(key, data.encode("utf-8"), hashlib.sha256)

        return result

    @staticmethod
    def _hash_sha256(data):
        result = hashlib.sha256(data.encode('utf-8')).hexdigest()

        return result

    @staticmethod
    def _get_system_data_attribute(data, key):
        result = None

        system_data_attributes = data.get("L", [])
        if key in system_data_attributes:
            system_data_value = system_data_attributes[key]

            result = system_data_value.get("S")

        return result

    async def _send_desired_command(self, payload: dict | None):
        update_topic = TOPIC_UPDATE.replace("/#", "").replace("{}", self.serial)

        new_state = {
            "state": {
                "desired": payload
            }
        }

        request_data = json.dumps(new_state)

        if self.status == ConnectivityStatus.Connected:
            self.awsiot_client.publish(update_topic, request_data, 0)

        else:
            _LOGGER.error(f"Failed to publish message: {new_state} to {update_topic}")

    async def set_cleaning_mode(self, cleaning_mode):
        data = {
            "cycleInfo": {
                "cleaningMode": {
                    "mode": cleaning_mode
                }
            }
        }

        _LOGGER.info(f"Set cleaning mode, Desired: {data}")
        await self._send_desired_command(data)

    async def set_delay(self,
                        device: str,
                        enabled: bool | None = False,
                        mode: str | None = "all",
                        job_time: str | None = None):

        await self.set_schedule(device, "delay", enabled, mode, job_time)

    async def set_schedule(self,
                           device: str,
                           day: str,
                           enabled: bool | None = False,
                           mode: str | None = "all",
                           job_time: str | None = None):
        if device != self.serial:
            return

        hours = 255
        minutes = 255

        if enabled:
            job_time_parts = job_time.split(":")
            hours = int(job_time_parts[0])
            minutes = int(job_time_parts[1])

        request_data = {
            "weeklySettings": {
                "triggeredBy": 0,
                day: {
                    "isEnabled": enabled,
                    "cleaningMode": {
                        "mode": mode
                    },
                    "time": {
                        "hours": hours,
                        "minutes": minutes
                    }
                }
            }
        }

        _LOGGER.info(f"Set schedule, Desired: {request_data}")
        await self._send_desired_command(request_data)

    async def set_led_mode(self, mode: int):
        default_data = {
            "ledEnable": True,
            "ledIntensity": 80,
            "ledMode": mode
        }

        request_data = self.data.get("led", default_data)
        request_data["ledMode"] = int(mode)

        data = {
            "led": request_data
        }

        _LOGGER.info(f"Set led mode, Desired: {data}")
        await self._send_desired_command(data)

    async def set_led_intensity(self, intensity: int):
        default_data = {
            "ledEnable": True,
            "ledIntensity": intensity,
            "ledMode": 1
        }

        request_data = self.data.get("led", default_data)
        request_data["ledIntensity"] = intensity

        data = {
            "led": request_data
        }

        _LOGGER.info(f"Set led intensity, Desired: {data}")
        await self._send_desired_command(data)

    async def set_led_enabled(self, is_enabled: bool):
        default_data = {
            "ledEnable": is_enabled,
            "ledIntensity": 80,
            "ledMode": 1
        }

        request_data = self.data.get("led", default_data)
        request_data["ledEnable"] = is_enabled

        data = {
            "led": request_data
        }

        _LOGGER.info(f"Set led enabled mode, Desired: {data}")
        await self._send_desired_command(data)

    async def drive(self, device: str, direction: str):
        if device != self.serial:
            return

        _LOGGER.warning(f"Drive is not implemented yet, Value: {direction}")

        # await self._send_desired_command(None)

    async def pickup(self, device: str):
        if device != self.serial:
            return

        _LOGGER.warning(f"Pickup is not implemented yet")

        # await self._send_desired_command(None)

    async def set_power_state(self, is_on: bool):
        request_data = None

        if is_on:
            request_data = {
                "systemState": {
                    "pwsState": "on"
                }
            }

        _LOGGER.info(f"Set power state, Desired: {request_data}")
        await self._send_desired_command(request_data)
