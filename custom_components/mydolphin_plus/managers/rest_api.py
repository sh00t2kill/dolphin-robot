from __future__ import annotations

from datetime import datetime
import json
import logging
import sys
import time
from typing import Any

from aiohttp import ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET, METH_POST

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send

from ..common.connectivity_status import ConnectivityStatus
from ..common.consts import (
    API_RESPONSE_ALERT,
    API_RESPONSE_DATA,
    API_RESPONSE_UNIT_SERIAL_NUMBER,
    API_TOKEN_FIELDS,
    AUTHENTICATE_USER_URL,
    AWS_CREDENTIALS_TTL,
    AWS_STS_TOKEN_URL,
    BEARER_HEADERS_BASE,
    COGNITO_AUTH_FLOW_CUSTOM,
    COGNITO_AUTH_FLOW_REFRESH,
    COGNITO_CHALLENGE_NAME,
    COGNITO_CLIENT_ID,
    COGNITO_CONTENT_TYPE,
    COGNITO_ENDPOINT,
    COGNITO_HEADER_TARGET,
    COGNITO_TARGET_PREFIX,
    DATA_ROBOT_DETAILS,
    ID_TOKEN_REFRESH_WINDOW_SECONDS,
    MIN_TOKEN_FETCH_INTERVAL,
    RECONNECT_BACKOFF_MAX,
    SIGNAL_API_STATUS,
    SIGNAL_DEVICE_NEW,
)
from ..common.integration_info import IntegrationInfo
from ..models.config_data import ConfigData
from ..models.exceptions import LoginError
from .config_manager import ConfigManager

_LOGGER = logging.getLogger(__name__)


def _build_headers(
    base: dict | None = None,
    id_token: str | None = None,
    extra: dict | None = None,
    integration_info: IntegrationInfo | None = None,
) -> dict:
    headers = {}
    if base:
        headers.update(base)
    if id_token:
        headers["Authorization"] = f"Bearer {id_token}"
    if extra:
        headers.update(extra)
    if integration_info is not None:
        integration_info.set_user_agent(headers)
    return headers


async def _cognito_call(
    session: ClientSession,
    target: str,
    body: dict,
    integration_info: IntegrationInfo | None = None,
) -> dict:
    headers = _build_headers(
        base={
            "Content-Type": COGNITO_CONTENT_TYPE,
            COGNITO_HEADER_TARGET: f"{COGNITO_TARGET_PREFIX}{target}",
        },
        integration_info=integration_info,
    )
    try:
        async with session.post(
            COGNITO_ENDPOINT, headers=headers, data=json.dumps(body)
        ) as response:
            text = await response.text()
            if response.status >= 400:
                _LOGGER.debug(
                    f"Cognito {target} failed, Status: {response.status}, Body: {text}"
                )
                raise LoginError(f"Cognito {target} returned {response.status}")
            return json.loads(text)
    except LoginError:
        raise
    except Exception as ex:
        _LOGGER.debug(f"Cognito {target} request failed, Error: {ex}")
        raise LoginError(f"Cognito {target} request failed: {ex}") from ex


async def cognito_initiate_auth(
    session: ClientSession,
    email: str,
    integration_info: IntegrationInfo | None = None,
) -> dict:
    response = await _cognito_call(
        session,
        "InitiateAuth",
        {
            "AuthFlow": COGNITO_AUTH_FLOW_CUSTOM,
            "ClientId": COGNITO_CLIENT_ID,
            "AuthParameters": {"USERNAME": email},
            "ClientMetadata": {},
        },
        integration_info=integration_info,
    )
    if response.get("ChallengeName") != COGNITO_CHALLENGE_NAME:
        raise LoginError(
            f"Unexpected Cognito challenge: {response.get('ChallengeName')}"
        )
    return response


async def cognito_respond_otp(
    session: ClientSession,
    email: str,
    cognito_session: str,
    code: str,
    integration_info: IntegrationInfo | None = None,
) -> dict:
    response = await _cognito_call(
        session,
        "RespondToAuthChallenge",
        {
            "ChallengeName": COGNITO_CHALLENGE_NAME,
            "ClientId": COGNITO_CLIENT_ID,
            "Session": cognito_session,
            "ChallengeResponses": {"USERNAME": email, "ANSWER": code},
            "ClientMetadata": {},
        },
        integration_info=integration_info,
    )
    auth = response.get("AuthenticationResult")
    if not auth or "IdToken" not in auth:
        raise LoginError("OTP rejected by Cognito")
    return auth


async def cognito_refresh(
    session: ClientSession,
    refresh_token: str,
    integration_info: IntegrationInfo | None = None,
) -> dict:
    response = await _cognito_call(
        session,
        "InitiateAuth",
        {
            "AuthFlow": COGNITO_AUTH_FLOW_REFRESH,
            "ClientId": COGNITO_CLIENT_ID,
            "AuthParameters": {"REFRESH_TOKEN": refresh_token},
            "ClientMetadata": {},
        },
        integration_info=integration_info,
    )
    auth = response.get("AuthenticationResult")
    if not auth or "IdToken" not in auth:
        raise LoginError("Refresh token rejected by Cognito")
    return auth


async def fetch_user_profile(
    session: ClientSession,
    id_token: str,
    integration_info: IntegrationInfo | None = None,
) -> dict:
    headers = _build_headers(
        base=BEARER_HEADERS_BASE,
        id_token=id_token,
        extra={"Content-Type": "application/x-www-form-urlencoded"},
        integration_info=integration_info,
    )
    try:
        async with session.post(
            AUTHENTICATE_USER_URL, headers=headers, data=""
        ) as response:
            response.raise_for_status()
            payload = await response.json()
    except ClientResponseError as ex:
        raise LoginError(f"authenticate-user failed: HTTP {ex.status}") from ex
    except Exception as ex:
        raise LoginError(f"authenticate-user request failed: {ex}") from ex

    data = payload.get(API_RESPONSE_DATA) or {}
    if not data:
        raise LoginError(
            f"authenticate-user returned empty data, Alert: {payload.get(API_RESPONSE_ALERT)}"
        )
    return data


async def fetch_aws_credentials(
    session: ClientSession,
    id_token: str,
    integration_info: IntegrationInfo | None = None,
) -> dict:
    headers = _build_headers(
        base=BEARER_HEADERS_BASE,
        id_token=id_token,
        integration_info=integration_info,
    )
    try:
        async with session.get(AWS_STS_TOKEN_URL, headers=headers) as response:
            response.raise_for_status()
            payload = await response.json()
    except ClientResponseError as ex:
        raise LoginError(f"getToken failed: HTTP {ex.status}") from ex
    except Exception as ex:
        raise LoginError(f"getToken request failed: {ex}") from ex

    data = payload.get(API_RESPONSE_DATA) or {}
    if not data.get("AccessKeyId"):
        raise LoginError(
            f"getToken returned no credentials, Alert: {payload.get(API_RESPONSE_ALERT)}"
        )
    return data


class RestAPI:
    data: dict

    _hass: HomeAssistant | None
    _status: ConnectivityStatus | None
    _session: ClientSession | None
    _config_manager: ConfigManager
    _integration_info: IntegrationInfo

    _device_loaded: bool

    def __init__(self, hass: HomeAssistant | None, config_manager: ConfigManager):
        try:
            self._hass = hass
            self.data = {}
            self._config_manager = config_manager
            self._integration_info = IntegrationInfo()
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
        return self._session is not None

    @property
    def config_data(self) -> ConfigData:
        return self._config_manager.config_data

    @property
    def status(self) -> str | None:
        return self._status

    @property
    def _is_home_assistant(self):
        return self._hass is not None

    async def initialize(self):
        _LOGGER.info("Initializing MyDolphin API")

        await self._integration_info.initialize(self._hass)
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

    async def update(self):
        if self._status != ConnectivityStatus.CONNECTED:
            return

        if self._device_loaded:
            return

        _LOGGER.debug("Connected. Refresh details")

        if not await self._ensure_id_token_valid():
            return

        if not await self._authenticate_user():
            return

        self._device_loaded = True

        self._async_dispatcher_send(SIGNAL_DEVICE_NEW, self._config_manager.entry_id)

        _LOGGER.debug(f"API Data updated: {self.data}")

    async def _login(self):
        if self._config_manager.refresh_token is None:
            self._set_status(
                ConnectivityStatus.EXPIRED_TOKEN,
                "no refresh token stored — reauthentication required",
            )
            return

        if not await self._ensure_id_token_valid():
            return

        if not await self._authenticate_user():
            return

        self._set_status(
            ConnectivityStatus.TEMPORARY_CONNECTED,
            f"profile loaded for {self._config_manager.serial_number}",
        )

        await self._refresh_aws_credentials()

    async def _ensure_id_token_valid(self) -> bool:
        expires_at = self._config_manager.id_token_expires_at or 0
        id_token = self._config_manager.id_token
        now = time.time()

        if id_token and (expires_at - now) > ID_TOKEN_REFRESH_WINDOW_SECONDS:
            return True

        refresh_token = self._config_manager.refresh_token
        if not refresh_token:
            self._set_status(
                ConnectivityStatus.EXPIRED_TOKEN,
                "no refresh token available — reauthentication required",
            )
            return False

        try:
            auth = await cognito_refresh(
                self._session,
                refresh_token,
                integration_info=self._integration_info,
            )
        except LoginError as ex:
            await self._config_manager.reset_login_details()
            self._set_status(
                ConnectivityStatus.EXPIRED_TOKEN,
                f"refresh failed ({ex}) — reauthentication required",
            )
            return False

        new_expires = time.time() + int(auth.get("ExpiresIn", 3600))
        await self._config_manager.update_tokens(
            auth["IdToken"],
            auth.get("RefreshToken"),
            new_expires,
        )
        _LOGGER.debug("Refreshed Cognito IdToken")
        return True

    async def _bearer_post(
        self, url: str, body: str | dict | None = None
    ) -> dict | None:
        headers = _build_headers(
            base=BEARER_HEADERS_BASE,
            id_token=self._config_manager.id_token,
            extra={"Content-Type": "application/x-www-form-urlencoded"},
            integration_info=self._integration_info,
        )
        return await self._async_send(METH_POST, url, headers, data=body or "")

    async def _bearer_get(self, url: str) -> dict | None:
        headers = _build_headers(
            base=BEARER_HEADERS_BASE,
            id_token=self._config_manager.id_token,
            integration_info=self._integration_info,
        )
        return await self._async_send(METH_GET, url, headers)

    async def _async_send(
        self,
        method: str,
        url: str,
        headers: dict,
        data: str | dict | None = None,
    ) -> dict | None:
        try:
            _LOGGER.debug(f"Sending {method} {url}")
            if method == METH_POST:
                async with self._session.post(
                    url, headers=headers, data=data
                ) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                async with self._session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientResponseError as crex:
            await self._handle_client_error(url, method, crex)
        except TimeoutError:
            self._handle_server_timeout(url, method)
        except Exception as ex:
            self._handle_general_request_failure(url, method, ex)
        return None

    async def _authenticate_user(self) -> bool:
        try:
            payload = await self._bearer_post(AUTHENTICATE_USER_URL, body="")
        except Exception as ex:
            self._set_status(ConnectivityStatus.FAILED, f"authenticate-user: {ex}")
            return False

        if payload is None:
            return False

        data = payload.get(API_RESPONSE_DATA) or {}
        if not data:
            alert = payload.get(API_RESPONSE_ALERT)
            self._set_status(
                ConnectivityStatus.FAILED,
                f"authenticate-user empty data, Alert: {alert}",
            )
            return False

        serial_number = data.get("Sernum")
        motor_unit_serial = data.get(API_RESPONSE_UNIT_SERIAL_NUMBER)

        if serial_number and serial_number != self._config_manager.serial_number:
            await self._config_manager.update_serial_number(serial_number)

        if (
            motor_unit_serial
            and motor_unit_serial != self._config_manager.motor_unit_serial
        ):
            await self._config_manager.update_motor_unit_serial(motor_unit_serial)

        for key, mapped in DATA_ROBOT_DETAILS.items():
            if key in data:
                self.data[mapped] = data.get(key)

        return True

    async def _refresh_aws_credentials(self):
        # Use cached creds when still valid
        if await self._are_cached_credentials_valid():
            _LOGGER.info("Using cached AWS IoT credentials (still valid)")
            self._set_status(ConnectivityStatus.CONNECTED)
            return

        # Rate limit fresh fetches; fall back to (potentially stale) cache when limited
        now = datetime.now().timestamp()
        last_fetch = self._config_manager.last_aws_credentials_fetch or 0
        time_since_last = now - last_fetch

        if (
            last_fetch > 0
            and time_since_last < MIN_TOKEN_FETCH_INTERVAL.total_seconds()
        ):
            wait_time = MIN_TOKEN_FETCH_INTERVAL.total_seconds() - time_since_last
            _LOGGER.warning(
                f"Token fetch rate limited. Last fetch was {time_since_last:.0f}s ago. "
                f"Need to wait {wait_time:.0f}s more."
            )
            if self._has_cached_credentials():
                if await self._are_cached_credentials_valid():
                    _LOGGER.info("Using cached AWS IoT credentials due to rate limit")
                    self._set_status(ConnectivityStatus.CONNECTED)
                    return
                _LOGGER.info(
                    "Cached AWS credentials are expired and refresh is rate limited"
                )
                self._set_status(
                    ConnectivityStatus.FAILED,
                    "AWS credentials expired and refresh is rate-limited",
                )
                return
            _LOGGER.warning(
                "No cached credentials available, attempting fetch despite rate limit"
            )

        _LOGGER.info("Fetching fresh AWS IoT credentials from getToken endpoint")

        try:
            data = await fetch_aws_credentials(
                self._session,
                self._config_manager.id_token,
                integration_info=self._integration_info,
            )
        except LoginError as ex:
            self._set_status(ConnectivityStatus.FAILED, f"getToken: {ex}")
            return

        for field in API_TOKEN_FIELDS:
            self.data[field] = data.get(field)

        now = datetime.now().timestamp()
        expiry = now + AWS_CREDENTIALS_TTL.total_seconds()
        await self._config_manager.update_last_aws_credentials_fetch(now)
        await self._config_manager.update_aws_credentials_expiry(expiry)

        _LOGGER.info(
            f"Successfully fetched AWS IoT credentials. "
            f"Valid until {datetime.fromtimestamp(expiry).isoformat()}"
        )

        self._set_status(ConnectivityStatus.CONNECTED)

    async def _are_cached_credentials_valid(self) -> bool:
        """Check if cached AWS IoT credentials are still valid."""
        if not self._has_cached_credentials():
            return False

        expiry = self._config_manager.aws_credentials_expiry
        now = datetime.now().timestamp()

        is_valid = expiry > now

        if is_valid:
            remaining_hours = (expiry - now) / 3600
            _LOGGER.debug(
                f"Cached credentials valid for {remaining_hours:.1f} more hours"
            )
        else:
            _LOGGER.debug("Cached credentials have expired")

        return is_valid

    def _has_cached_credentials(self) -> bool:
        """Check if AWS IoT credentials exist in memory cache."""
        return all(self.data.get(field) is not None for field in API_TOKEN_FIELDS)

    def _set_status(
        self,
        status: ConnectivityStatus,
        message: str | None = None,
        force_log_level: int | None = None,
    ):
        log_level = (
            ConnectivityStatus.get_log_level(status)
            if force_log_level is None
            else force_log_level
        )

        if status != self._status:
            log_message = f"Status update {self._status} --> {status}"

            if message is not None:
                log_message = f"{log_message}, {message}"

            _LOGGER.log(log_level, log_message)

            if status.is_disconnected():
                self._device_loaded = False

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
        status = ConnectivityStatus.FAILED
        forced_log_level: int | None = None

        if crex.status == 401:
            # The IdToken is rejected. If the cached token is older than the
            # backoff window, blow it away and force re-auth so we don't hammer
            # the API with bad credentials. Otherwise, log quietly and let
            # _ensure_id_token_valid try a refresh on the next iteration.
            flow = "No id token present"

            has_id_token = self._config_manager.id_token is not None
            last_fetch = self._config_manager.last_token_fetch

            if has_id_token:
                if last_fetch > 0:
                    token_age_seconds = datetime.now().timestamp() - last_fetch

                    if token_age_seconds >= RECONNECT_BACKOFF_MAX.total_seconds():
                        await self._config_manager.reset_login_details()
                        flow = "Old token, cleared for re-auth"
                        status = ConnectivityStatus.EXPIRED_TOKEN
                    else:
                        flow = "Fresh token within window"
                        forced_log_level = logging.DEBUG
                else:
                    flow = "Token exists but no timestamp"
                    forced_log_level = logging.DEBUG

            message = f"{message}, flow: {flow}"

        elif crex.status in [404, 405]:
            status = ConnectivityStatus.API_NOT_FOUND

        self._set_status(status, message, forced_log_level)

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
