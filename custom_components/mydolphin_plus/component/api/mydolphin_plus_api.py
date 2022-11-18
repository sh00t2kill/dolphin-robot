from __future__ import annotations

from base64 import b64encode
from collections.abc import Awaitable, Callable
import hashlib
import logging
import secrets
import sys

from aiohttp import ClientResponseError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from homeassistant.core import HomeAssistant

from ...configuration.models.config_data import ConfigData
from ...core.api.base_api import BaseAPI
from ...core.helpers.enums import ConnectivityStatus
from ..helpers.const import *

REQUIREMENTS = ["aiohttp"]

_LOGGER = logging.getLogger(__name__)


class IntegrationAPI(BaseAPI):
    hass: HomeAssistant | None
    config_data: ConfigData | None
    base_url: str | None
    aws_token_encrypted_key: str | None

    def __init__(self,
                 hass: HomeAssistant | None,
                 async_on_data_changed: Callable[[], Awaitable[None]] | None = None,
                 async_on_status_changed: Callable[[ConnectivityStatus], Awaitable[None]] | None = None
                 ):

        super().__init__(hass, async_on_data_changed, async_on_status_changed)

        try:
            self.hass = hass
            self.config_data = None
            self.base_url = None

            self.server_version = None
            self.server_timestamp = None
            self.server_time_diff = 0

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load MyDolphin Plus API, error: {ex}, line: {line_number}"
            )

    @property
    def aws_token_encrypted_key(self) -> str | None:
        key = self.data.get(STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY)

        return key

    async def initialize(self, config_data: ConfigData, aws_token_encrypted_key: str | None):
        _LOGGER.info("Initializing MyDolphin API")

        self.data[STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY] = aws_token_encrypted_key
        self.config_data = config_data

        await super().initialize_session()

        await self._login()

    async def validate(self, data: dict | None = None):
        config_data = ConfigData.from_dict(data)

        self.config_data = config_data

        await super().initialize_session()

        await self._service_login()

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
        if self.status == ConnectivityStatus.Failed:
            _LOGGER.debug("Connection failed. Reinitialize")
            await self.initialize(self.config_data, self.aws_token_encrypted_key)

        if self.status == ConnectivityStatus.Connected:
            _LOGGER.debug("Connected. Refresh details")
            await self._load_details()

            for key in self.data:
                _LOGGER.info(f"{key}: {self.data[key]}")

    async def _login(self):
        await self._service_login()
        await self._generate_token()

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

                self.data[API_DATA_MOTOR_UNIT_SERIAL] = actual_motor_unit_serial
                self.data[API_DATA_SERIAL_NUMBER] = motor_unit_serial
                self.data[API_DATA_LOGIN_TOKEN] = token

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
            get_token_attempts = 0
            motor_unit_serial = self.data.get(API_DATA_MOTOR_UNIT_SERIAL)
            login_token = self.data.get(API_DATA_LOGIN_TOKEN)

            headers = {
                API_REQUEST_HEADER_TOKEN: login_token
            }

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            while get_token_attempts < MAXIMUM_ATTEMPTS_GET_AWS_TOKEN:
                if self.aws_token_encrypted_key is None:
                    self._generate_aws_token_encrypted_key(motor_unit_serial)

                request_data = f"{API_REQUEST_SERIAL_NUMBER}={self.aws_token_encrypted_key}"

                payload = await self._async_post(TOKEN_URL, headers, request_data)

                data = payload.get(API_RESPONSE_DATA, {})
                alert = payload.get(API_RESPONSE_ALERT, {})
                status = payload.get(API_RESPONSE_STATUS, API_RESPONSE_STATUS_FAILURE)

                if status == API_RESPONSE_STATUS_SUCCESS:
                    for field in API_TOKEN_FIELDS:
                        self.data[field] = data.get(field)

                    await self.set_status(ConnectivityStatus.Connected)

                    _LOGGER.debug(f"Retrieved AWS token after {get_token_attempts} attempts")

                    get_token_attempts = MAXIMUM_ATTEMPTS_GET_AWS_TOKEN

                else:
                    self.data[STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY] = None

                    if get_token_attempts + 1 >= MAXIMUM_ATTEMPTS_GET_AWS_TOKEN:
                        _LOGGER.error(f"Failed to retrieve AWS token after {get_token_attempts} attempts, Error: {alert}")

                        await self.set_status(ConnectivityStatus.Failed)

                get_token_attempts += 1

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to retrieve AWS token from service, Error: {str(ex)}, Line: {line_number}")
            await self.set_status(ConnectivityStatus.Failed)

    async def _load_details(self):
        if self.status != ConnectivityStatus.Connected:
            await self.set_status(ConnectivityStatus.Failed)
            return

        try:
            motor_unit_serial = self.data.get(API_DATA_MOTOR_UNIT_SERIAL)
            login_token = self.data.get(API_DATA_LOGIN_TOKEN)

            headers = {
                API_REQUEST_HEADER_TOKEN: login_token
            }

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = f"{API_REQUEST_SERIAL_NUMBER}={motor_unit_serial}"

            payload = await self._async_post(ROBOT_DETAILS_URL, headers, request_data)

            response_status = payload.get(API_RESPONSE_STATUS, API_RESPONSE_STATUS_FAILURE)
            alert = payload.get(API_RESPONSE_STATUS, API_RESPONSE_ALERT)

            if response_status == API_RESPONSE_STATUS_SUCCESS:

                data = payload.get(API_RESPONSE_DATA, {})

                for key in DATA_ROBOT_DETAILS:
                    new_key = DATA_ROBOT_DETAILS.get(key)

                    self.data[new_key] = data.get(key)

            else:
                _LOGGER.error(f"Failed to reload details, Error: {alert}")

            await self.fire_data_changed_event()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to retrieve Robot Details, Error: {str(ex)}, Line: {line_number}")

    def _generate_aws_token_encrypted_key(self, sn: str):
        _LOGGER.debug(f"ENCRYPT: Serial number: {sn}")

        backend = default_backend()
        iv = secrets.token_bytes(BLOCK_SIZE)
        mode = modes.CBC(iv)
        aes_key = self._get_aes_key()

        cipher = Cipher(algorithms.AES(aes_key), mode, backend=backend)
        encryptor = cipher.encryptor()

        data = self._pad(sn).encode()
        ct = encryptor.update(data) + encryptor.finalize()

        result_b64 = iv + ct

        result = b64encode(result_b64).decode()

        self.data[STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY] = result

    @staticmethod
    def _pad(text) -> str:
        text_length = len(text)
        amount_to_pad = BLOCK_SIZE - (text_length % BLOCK_SIZE)

        if amount_to_pad == 0:
            amount_to_pad = BLOCK_SIZE

        pad = chr(amount_to_pad)

        result = text + pad * amount_to_pad

        return result

    def _get_aes_key(self):
        email_beginning = self.config_data.username[:2]

        password = f"{email_beginning}ha".lower()

        password_bytes = password.encode()

        encryption_hash = hashlib.md5(password_bytes)
        encryption_key = encryption_hash.digest()

        return encryption_key
