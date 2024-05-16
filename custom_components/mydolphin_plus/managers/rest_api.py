from __future__ import annotations

from base64 import b64encode
import hashlib
import logging
import secrets
import sys
from typing import Any

from aiohttp import ClientResponseError, ClientSession
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send

from ..common.connectivity_status import ConnectivityStatus
from ..common.consts import (
    API_DATA_LOGIN_TOKEN,
    API_DATA_MOTOR_UNIT_SERIAL,
    API_DATA_SERIAL_NUMBER,
    API_REQUEST_HEADER_TOKEN,
    API_REQUEST_SERIAL_EMAIL,
    API_REQUEST_SERIAL_NUMBER,
    API_REQUEST_SERIAL_PASSWORD,
    API_RESPONSE_ALERT,
    API_RESPONSE_DATA,
    API_RESPONSE_STATUS,
    API_RESPONSE_STATUS_FAILURE,
    API_RESPONSE_STATUS_SUCCESS,
    API_RESPONSE_UNIT_SERIAL_NUMBER,
    API_TOKEN_FIELDS,
    BLOCK_SIZE,
    DATA_ROBOT_DETAILS,
    DEFAULT_NAME,
    LOGIN_HEADERS,
    LOGIN_URL,
    MAXIMUM_ATTEMPTS_GET_AWS_TOKEN,
    ROBOT_DETAILS_BY_SN_URL,
    ROBOT_DETAILS_URL,
    SIGNAL_API_STATUS,
    SIGNAL_DEVICE_NEW,
    STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY,
    TOKEN_URL,
)
from ..models.config_data import ConfigData
from .config_manager import ConfigManager

_LOGGER = logging.getLogger(__name__)


class RestAPI:
    data: dict

    _hass: HomeAssistant | None
    _base_url: str | None
    _status: ConnectivityStatus | None
    _session: ClientSession | None
    _config_manager: ConfigManager

    _device_loaded: bool

    def __init__(self, hass: HomeAssistant | None, config_manager: ConfigManager):
        try:
            self._hass = hass

            self.data = {}

            self._config_manager = config_manager

            self._status = None

            self._session = None
            self._device_loaded = False

            self._local_async_dispatcher_send = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load MyDolphin Plus API, error: {ex}, line: {line_number}"
            )

    @property
    def is_connected(self):
        result = self._session is not None

        return result

    @property
    def config_data(self) -> ConfigData:
        result = self._config_manager.config_data

        return result

    @property
    def aws_token_encrypted_key(self) -> str | None:
        key = self.data.get(STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY)

        return key

    @property
    def _login_token(self) -> str | None:
        login_token = self.data.get(API_DATA_LOGIN_TOKEN)

        return login_token

    @property
    def _motor_unit_serial(self):
        motor_unit_serial = self.data.get(API_DATA_MOTOR_UNIT_SERIAL)

        return motor_unit_serial

    @property
    def status(self) -> str | None:
        status = self._status

        return status

    @property
    def _is_home_assistant(self):
        return self._hass is not None

    async def initialize(self, aws_token_encrypted_key: str | None):
        _LOGGER.info("Initializing MyDolphin API")

        self.data[STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY] = aws_token_encrypted_key

        await self._initialize_session()
        await self._login()

    async def terminate(self):
        if self._session is not None:
            await self._session.close()

            self._set_status(ConnectivityStatus.Disconnected)

    async def _initialize_session(self):
        try:
            if self._is_home_assistant:
                self._session = async_create_clientsession(hass=self._hass)

            else:
                self._session = ClientSession()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(
                f"Failed to initialize session, Error: {str(ex)}, Line: {line_number}"
            )

            self._set_status(ConnectivityStatus.Failed)

    async def validate(self):
        await self._initialize_session()
        await self._service_login()

    async def _async_post(self, url, headers: dict, request_data: str | dict | None):
        result = None

        try:
            async with self._session.post(
                url, headers=headers, data=request_data, ssl=False
            ) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                _LOGGER.debug(
                    f"POST request [{url}] completed successfully, Result: {result}"
                )

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to post JSON to {url}, HTTP Status: {crex.message} ({crex.status})"
            )

            if crex.status in [401, 403]:
                self._set_status(ConnectivityStatus.Failed)

            elif crex.status in [404, 405]:
                self._set_status(ConnectivityStatus.NotFound)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to post JSON to {url}, Error: {ex}, Line: {line_number}"
            )

            self._set_status(ConnectivityStatus.Failed)

        return result

    async def _async_get(self, url, headers: dict):
        result = None

        try:
            async with self._session.get(url, headers=headers, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                _LOGGER.debug(
                    f"GET request [{url}] completed successfully, Result: {result}"
                )

        except ClientResponseError as crex:
            _LOGGER.error(
                f"Failed to get data from {url}, HTTP Status: {crex.message} ({crex.status})"
            )

            if crex.status in [404, 405]:
                self._set_status(ConnectivityStatus.NotFound)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {url}, Error: {ex}, Line: {line_number}"
            )

            self._set_status(ConnectivityStatus.Failed)

        return result

    async def update(self):
        if self._status == ConnectivityStatus.Failed:
            _LOGGER.debug("Connection failed. Reinitialize")
            await self.initialize(self.aws_token_encrypted_key)

        if self._status == ConnectivityStatus.Connected:
            _LOGGER.debug("Connected. Refresh details")
            await self._load_details()

            if not self._device_loaded:
                self._device_loaded = True

                self._async_dispatcher_send(
                    SIGNAL_DEVICE_NEW, self._config_manager.entry_id
                )

            _LOGGER.debug(f"API Data updated: {self.data}")

    async def _login(self):
        await self._service_login()

        if self._status == ConnectivityStatus.TemporaryConnected:
            await self._generate_token()

        elif self._status == ConnectivityStatus.InvalidCredentials:
            return

        else:
            self._set_status(ConnectivityStatus.Failed)

    async def _service_login(self):
        try:
            self._set_status(ConnectivityStatus.Connecting)

            username = self.config_data.username
            password = self.config_data.password

            request_data = f"{API_REQUEST_SERIAL_EMAIL}={username}&{API_REQUEST_SERIAL_PASSWORD}={password}"

            payload = await self._async_post(LOGIN_URL, LOGIN_HEADERS, request_data)

            if payload is None:
                payload = {}

            data = payload.get(API_RESPONSE_DATA, {})
            if data:
                _LOGGER.info(f"Logged in to user {username}")

                motor_unit_serial = data.get(API_REQUEST_SERIAL_NUMBER)
                token = data.get(API_REQUEST_HEADER_TOKEN)

                self.data[API_DATA_SERIAL_NUMBER] = motor_unit_serial
                self.data[API_DATA_LOGIN_TOKEN] = token

                await self._set_actual_motor_unit_serial()

            else:
                self._set_status(ConnectivityStatus.InvalidCredentials)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to login into {DEFAULT_NAME} service, Error: {str(ex)}, Line: {line_number}"
            )
            self._set_status(ConnectivityStatus.Failed)

    async def _set_actual_motor_unit_serial(self):
        try:
            serial_serial = self.data.get(API_DATA_SERIAL_NUMBER)

            headers = {API_REQUEST_HEADER_TOKEN: self._login_token}

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = f"{API_REQUEST_SERIAL_NUMBER}={serial_serial}"

            payload = await self._async_post(
                ROBOT_DETAILS_BY_SN_URL, headers, request_data
            )

            if payload is None:
                payload = {}

            data: dict = payload.get(API_RESPONSE_DATA, {})

            if data is not None:
                _LOGGER.info(
                    f"Successfully retrieved details for device {serial_serial}"
                )

                self.data[API_DATA_MOTOR_UNIT_SERIAL] = data.get(
                    API_RESPONSE_UNIT_SERIAL_NUMBER
                )

                self._set_status(ConnectivityStatus.TemporaryConnected)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to login into {DEFAULT_NAME} service, Error: {str(ex)}, Line: {line_number}"
            )
            self._set_status(ConnectivityStatus.Failed)

    async def _generate_token(self):
        try:
            get_token_attempts = 0

            headers = {API_REQUEST_HEADER_TOKEN: self._login_token}

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            while get_token_attempts < MAXIMUM_ATTEMPTS_GET_AWS_TOKEN:
                if self.aws_token_encrypted_key is None:
                    self._generate_aws_token_encrypted_key()

                request_data = (
                    f"{API_REQUEST_SERIAL_NUMBER}={self.aws_token_encrypted_key}"
                )

                payload = await self._async_post(TOKEN_URL, headers, request_data)

                data = payload.get(API_RESPONSE_DATA, {})
                alert = payload.get(API_RESPONSE_ALERT, {})
                status = payload.get(API_RESPONSE_STATUS, API_RESPONSE_STATUS_FAILURE)

                if status == API_RESPONSE_STATUS_SUCCESS:
                    for field in API_TOKEN_FIELDS:
                        self.data[field] = data.get(field)

                    self._set_status(ConnectivityStatus.Connected)

                    if get_token_attempts > 0:
                        _LOGGER.debug(
                            f"Retrieved AWS token after {get_token_attempts} attempts"
                        )

                    get_token_attempts = MAXIMUM_ATTEMPTS_GET_AWS_TOKEN

                else:
                    self.data[STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY] = None

                    if get_token_attempts + 1 >= MAXIMUM_ATTEMPTS_GET_AWS_TOKEN:
                        _LOGGER.error(
                            f"Failed to retrieve AWS token after {get_token_attempts} attempts, Error: {alert}"
                        )

                        self._set_status(ConnectivityStatus.Failed)

                get_token_attempts += 1

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to retrieve AWS token from service, Error: {str(ex)}, Line: {line_number}"
            )
            self._set_status(ConnectivityStatus.Failed)

    async def _load_details(self):
        if self._status != ConnectivityStatus.Connected:
            self._set_status(ConnectivityStatus.Failed)
            return

        try:
            headers = {API_REQUEST_HEADER_TOKEN: self._login_token}

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = f"{API_REQUEST_SERIAL_NUMBER}={self._motor_unit_serial}"

            payload = await self._async_post(ROBOT_DETAILS_URL, headers, request_data)

            if payload is not None:
                response_status = payload.get(
                    API_RESPONSE_STATUS, API_RESPONSE_STATUS_FAILURE
                )
                alert = payload.get(API_RESPONSE_STATUS, API_RESPONSE_ALERT)

                if response_status == API_RESPONSE_STATUS_SUCCESS:
                    data = payload.get(API_RESPONSE_DATA, {})

                    for key in DATA_ROBOT_DETAILS:
                        new_key = DATA_ROBOT_DETAILS.get(key)

                        self.data[new_key] = data.get(key)

                else:
                    _LOGGER.error(f"Failed to reload details, Error: {alert}")

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to retrieve Robot Details, Error: {str(ex)}, Line: {line_number}"
            )

    def _generate_aws_token_encrypted_key(self):
        _LOGGER.debug(f"ENCRYPT: Serial number: {self._motor_unit_serial}")

        backend = default_backend()
        iv = secrets.token_bytes(BLOCK_SIZE)
        mode = modes.CBC(iv)
        aes_key = self._get_aes_key()

        cipher = Cipher(algorithms.AES(aes_key), mode, backend=backend)
        encryptor = cipher.encryptor()

        data = self._pad(self._motor_unit_serial).encode()
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

    def _set_status(self, status: ConnectivityStatus):
        if status != self._status:
            log_level = ConnectivityStatus.get_log_level(status)

            _LOGGER.log(
                log_level,
                f"Status changed from '{self._status}' to '{status}'",
            )

            self._status = status

            self._async_dispatcher_send(
                SIGNAL_API_STATUS, self._config_manager.entry_id, status
            )

    def set_local_async_dispatcher_send(self, callback):
        self._local_async_dispatcher_send = callback

    def _async_dispatcher_send(self, signal: str, *args: Any) -> None:
        if self._hass is None:
            self._local_async_dispatcher_send(signal, *args)

        else:
            dispatcher_send(self._hass, signal, *args)
