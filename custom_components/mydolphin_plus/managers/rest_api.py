from __future__ import annotations

from asyncio import sleep
from base64 import b64encode
import hashlib
import logging
import secrets
import sys
from typing import Any

from aiohttp import ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET, METH_POST
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send

from ..common.connectivity_status import ConnectivityStatus
from ..common.consts import (
    API_REQUEST_HEADER_TOKEN,
    API_REQUEST_SERIAL_EMAIL,
    API_REQUEST_SERIAL_NUMBER,
    API_REQUEST_SERIAL_PASSWORD,
    API_RESPONSE_ALERT,
    API_RESPONSE_DATA,
    API_RESPONSE_IS_EMAIL_EXISTS,
    API_RESPONSE_STATUS,
    API_RESPONSE_STATUS_FAILURE,
    API_RESPONSE_STATUS_SUCCESS,
    API_RESPONSE_UNIT_SERIAL_NUMBER,
    API_TOKEN_FIELDS,
    BLOCK_SIZE,
    DATA_ROBOT_DETAILS,
    DEFAULT_NAME,
    EMAIL_VALIDATION_URL,
    FORGOT_PASSWORD_URL,
    LOGIN_HEADERS,
    LOGIN_URL,
    ROBOT_DETAILS_BY_SN_URL,
    ROBOT_DETAILS_URL,
    SIGNAL_API_STATUS,
    SIGNAL_DEVICE_NEW,
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
    def status(self) -> str | None:
        status = self._status

        return status

    @property
    def _is_home_assistant(self):
        return self._hass is not None

    async def initialize(self):
        _LOGGER.info("Initializing MyDolphin API")

        await self._initialize_session()

        await self._login()

    async def terminate(self):
        if self._session is not None:
            await self._session.close()

            self._set_status(ConnectivityStatus.DISCONNECTED, "terminate requested")

    async def _initialize_session(self):
        try:
            if self._is_home_assistant:
                self._session = async_create_clientsession(hass=self._hass)

            else:
                self._session = ClientSession()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            message = (
                f"Failed to initialize session, Error: {str(ex)}, Line: {line_number}"
            )

            self._set_status(ConnectivityStatus.FAILED, message)

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
            await self._handle_client_error(url, METH_POST, crex)

        except TimeoutError:
            self._handle_server_timeout(url, METH_POST)

        except Exception as ex:
            self._handle_general_request_failure(url, METH_POST, ex)

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
            await self._handle_client_error(url, METH_GET, crex)

        except TimeoutError:
            self._handle_server_timeout(url, METH_GET)

        except Exception as ex:
            self._handle_general_request_failure(url, METH_GET, ex)

        return result

    async def update(self):
        if self._status == ConnectivityStatus.CONNECTED:
            _LOGGER.debug("Connected. Refresh details")
            await self._load_details()

            if not self._device_loaded:
                self._device_loaded = True

                self._async_dispatcher_send(
                    SIGNAL_DEVICE_NEW, self._config_manager.entry_id
                )

            _LOGGER.debug(f"API Data updated: {self.data}")

    async def _clean_login_details(self):
        await self._config_manager.reset_login_details()

    async def _login(self):
        if self._config_manager.api_token is None:
            await self._service_login()

        else:
            self._set_status(
                ConnectivityStatus.TEMPORARY_CONNECTED, "API Token available"
            )

        if self._status == ConnectivityStatus.TEMPORARY_CONNECTED:
            await self._generate_aws_token()

        elif self._status in [
            ConnectivityStatus.INVALID_CREDENTIALS,
            ConnectivityStatus.INVALID_ACCOUNT,
        ]:
            return

        else:
            self._set_status(ConnectivityStatus.FAILED, "general failure of login")

    async def reset_password(self):
        _LOGGER.debug("Starting reset password process")

        if self._session is None:
            await self._initialize_session()

        is_valid_email = await self._email_validation()

        if is_valid_email:
            username = self.config_data.username

            request_data = f"{API_REQUEST_SERIAL_EMAIL}={username}"

            payload = await self._async_post(
                FORGOT_PASSWORD_URL, LOGIN_HEADERS, request_data
            )

            if payload is None:
                _LOGGER.error("Empty response of reset password")

            else:
                data = payload.get(API_RESPONSE_DATA)

                if data is None:
                    _LOGGER.error("Empty response payload of reset password")

                else:
                    _LOGGER.info(f"Reset password response: {data}")

    async def _email_validation(self) -> bool:
        _LOGGER.debug("Validating account email")

        if self._status != ConnectivityStatus.INVALID_ACCOUNT:
            username = self.config_data.username

            request_data = f"{API_REQUEST_SERIAL_EMAIL}={username}"

            payload = await self._async_post(
                EMAIL_VALIDATION_URL, LOGIN_HEADERS, request_data
            )

            if payload is None:
                self._set_status(
                    ConnectivityStatus.INVALID_ACCOUNT,
                    "empty response of email validation",
                )

            else:
                data = payload.get(API_RESPONSE_DATA)

                if data is None:
                    self._set_status(
                        ConnectivityStatus.INVALID_ACCOUNT,
                        "empty response payload of email validation",
                    )

                else:
                    status = data.get(API_RESPONSE_IS_EMAIL_EXISTS, False)

                    if not status:
                        self._set_status(
                            ConnectivityStatus.INVALID_ACCOUNT,
                            f"account [{username}] is not valid",
                        )

        is_valid_account = self._status != ConnectivityStatus.INVALID_ACCOUNT

        return is_valid_account

    async def _service_login(self):
        try:
            is_valid_account = await self._email_validation()

            if not is_valid_account:
                return

            self._set_status(ConnectivityStatus.CONNECTING)

            username = self.config_data.username
            password = self.config_data.password

            request_data = f"{API_REQUEST_SERIAL_EMAIL}={username}&{API_REQUEST_SERIAL_PASSWORD}={password}"

            payload = await self._async_post(LOGIN_URL, LOGIN_HEADERS, request_data)

            if payload is None:
                self._set_status(ConnectivityStatus.FAILED, "empty response of login")

            else:
                data = payload.get(API_RESPONSE_DATA)

                if data is None:
                    self._set_status(
                        ConnectivityStatus.INVALID_CREDENTIALS,
                        "empty response payload of login",
                    )

                else:
                    _LOGGER.info(f"Logged in to user {username}")

                    serial_number = data.get(API_REQUEST_SERIAL_NUMBER)
                    api_token = data.get(API_REQUEST_HEADER_TOKEN)

                    await self._config_manager.update_login_details(
                        api_token, serial_number
                    )

                    await self._set_actual_motor_unit_serial()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            message = f"Failed to login into {DEFAULT_NAME} service, Error: {str(ex)}, Line: {line_number}"

            self._set_status(ConnectivityStatus.FAILED, message)

    async def _set_actual_motor_unit_serial(self):
        try:
            headers = {API_REQUEST_HEADER_TOKEN: self._config_manager.api_token}

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = (
                f"{API_REQUEST_SERIAL_NUMBER}={self._config_manager.serial_number}"
            )

            payload = await self._async_post(
                ROBOT_DETAILS_BY_SN_URL, headers, request_data
            )

            if payload is None:
                payload = {}

            data: dict = payload.get(API_RESPONSE_DATA, {})

            if data is not None:
                message = f"Successfully retrieved details for device {self._config_manager.serial_number}"

                motor_unit_serial = data.get(API_RESPONSE_UNIT_SERIAL_NUMBER)

                await self._config_manager.update_motor_unit_serial(motor_unit_serial)

                self._set_status(ConnectivityStatus.TEMPORARY_CONNECTED, message)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            message = f"Failed to login into {DEFAULT_NAME} service, Error: {str(ex)}, Line: {line_number}"

            self._set_status(ConnectivityStatus.FAILED, message)

    async def _generate_aws_token(self):
        try:
            headers = {API_REQUEST_HEADER_TOKEN: self._config_manager.api_token}

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            aws_token = self._config_manager.aws_token

            if aws_token is None:
                aws_token = await self._get_aws_token()

                await self._config_manager.update_aws_token(aws_token)

            request_data = f"{API_REQUEST_SERIAL_NUMBER}={aws_token}"

            payload = await self._async_post(TOKEN_URL, headers, request_data)

            if self._status == ConnectivityStatus.TEMPORARY_CONNECTED:
                data = payload.get(API_RESPONSE_DATA, {})
                alert = payload.get(API_RESPONSE_ALERT, {})
                status = payload.get(API_RESPONSE_STATUS, API_RESPONSE_STATUS_FAILURE)

                if status == API_RESPONSE_STATUS_SUCCESS:
                    for field in API_TOKEN_FIELDS:
                        self.data[field] = data.get(field)

                    self._set_status(ConnectivityStatus.CONNECTED)

                else:
                    message = f"Failed to retrieve AWS token, Error: {alert}"

                    self._set_status(ConnectivityStatus.FAILED, message)

                    await self._config_manager.update_aws_token(None)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            message = f"Failed to retrieve AWS token from service, Error: {str(ex)}, Line: {line_number}"

            self._set_status(ConnectivityStatus.FAILED, message)

    async def _load_details(self):
        if self._status != ConnectivityStatus.CONNECTED:
            return

        try:
            headers = {API_REQUEST_HEADER_TOKEN: self._config_manager.api_token}

            for key in LOGIN_HEADERS:
                headers[key] = LOGIN_HEADERS[key]

            request_data = (
                f"{API_REQUEST_SERIAL_NUMBER}={self._config_manager.motor_unit_serial}"
            )

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

    async def _get_aws_token(self) -> str | None:
        _LOGGER.debug(
            f"ENCRYPT: Motor Unit Serial: {self._config_manager.motor_unit_serial}"
        )

        for i in range(0, 10):
            backend = default_backend()
            iv = secrets.token_bytes(BLOCK_SIZE)
            mode = modes.CBC(iv)
            aes_key = self._get_aes_key()

            aes = algorithms.AES(aes_key)
            cipher = Cipher(aes, mode, backend=backend)

            encryptor = cipher.encryptor()

            data = self._pad(self._config_manager.motor_unit_serial).encode()
            ct = encryptor.update(data) + encryptor.finalize()

            result_b64 = iv + ct

            result = b64encode(result_b64).decode()

            if "+" not in result:
                return result

            await sleep(0.5)

        raise ValueError("Invalid AWS Token generated")

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

    def _set_status(self, status: ConnectivityStatus, message: str | None = None):
        log_level = ConnectivityStatus.get_log_level(status)

        if status != self._status:
            log_message = f"Status update {self._status} --> {status}"

            if message is not None:
                log_message = f"{log_message}, {message}"

            _LOGGER.log(log_level, log_message)

            self._status = status

            self._async_dispatcher_send(
                SIGNAL_API_STATUS, self._config_manager.entry_id, status
            )

        else:
            log_message = f"Status is {status}"

            if message is None:
                log_message = f"{log_message}, {message}"

            _LOGGER.log(log_level, log_message)

    async def _handle_client_error(
        self, endpoint: str, method: str, crex: ClientResponseError
    ):
        message = (
            "Failed to send HTTP request, "
            f"Endpoint: {endpoint}, "
            f"Method: {method}, "
            f"HTTP Status: {crex.message} ({crex.status})"
        )

        if crex.status in [401]:
            await self._clean_login_details()

            self._set_status(ConnectivityStatus.EXPIRED_TOKEN, message)

        if crex.status in [404, 405]:
            self._set_status(ConnectivityStatus.API_NOT_FOUND, message)

        else:
            self._set_status(ConnectivityStatus.FAILED, message)

    def _handle_server_timeout(self, endpoint: str, method: str):
        message = (
            "Failed to send HTTP request due to timeout, "
            f"Endpoint: {endpoint}, "
            f"Method: {method}"
        )

        self._set_status(ConnectivityStatus.FAILED, message)

    def _handle_general_request_failure(
        self, endpoint: str, method: str, ex: Exception
    ):
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        message = (
            "Failed to send HTTP request, "
            f"Endpoint: {endpoint}, "
            f"Method: {method}, "
            f"Error: {ex}, "
            f"Line: {line_number}"
        )

        self._set_status(ConnectivityStatus.FAILED, message)

    def set_local_async_dispatcher_send(self, callback):
        self._local_async_dispatcher_send = callback

    def _async_dispatcher_send(self, signal: str, *args: Any) -> None:
        if self._hass is None:
            self._local_async_dispatcher_send(signal, *args)

        else:
            dispatcher_send(self._hass, signal, *args)
