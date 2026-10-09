"""Tests for auth headers and rate-limit semantics."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from aiohttp import ClientResponseError
import pytest

from custom_components.mydolphin_plus.common.connectivity_status import (
    ConnectivityStatus,
)
from custom_components.mydolphin_plus.common.consts import (
    API_TOKEN_FIELDS,
    AWS_CREDENTIALS_EXPIRY,
    STORAGE_DATA_ID_TOKEN,
    STORAGE_DATA_ID_TOKEN_EXPIRES_AT,
    STORAGE_DATA_LAST_AWS_CREDENTIALS_FETCH,
    STORAGE_DATA_LAST_TOKEN_FETCH,
    STORAGE_DATA_REFRESH_TOKEN,
)
from custom_components.mydolphin_plus.managers.config_manager import ConfigManager
import custom_components.mydolphin_plus.managers.rest_api as rest_api_module
from custom_components.mydolphin_plus.managers.rest_api import (
    RestAPI,
    _cognito_call,
    cognito_initiate_auth,
    fetch_aws_credentials,
    fetch_user_profile,
)
from custom_components.mydolphin_plus.models.exceptions import (
    CognitoAuthError,
    CognitoRequestError,
)


class DummyIntegrationInfo:
    """Simple user-agent provider used in tests."""

    def set_user_agent(self, headers: dict) -> None:
        headers["User-Agent"] = "HA-MyDolphin-Plus/test"


class FakeResponse:
    """Minimal async response object."""

    def __init__(self, payload: dict, status: int = 200):
        self._payload = payload
        self.status = status
        self.message = "error"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def text(self) -> str:
        import json

        return json.dumps(self._payload)

    async def json(self) -> dict:
        return self._payload

    def raise_for_status(self):
        if self.status >= 400:
            raise Exception("http failure")


class FakeSession:
    """Captures request headers for assertions."""

    def __init__(self, post_payload: dict | None = None, get_payload: dict | None = None):
        self._post_payload = post_payload or {}
        self._get_payload = get_payload or {}
        self.last_headers: dict | None = None

    def post(self, _url, headers=None, data=None):
        self.last_headers = headers
        return FakeResponse(self._post_payload)

    def get(self, _url, headers=None):
        self.last_headers = headers
        return FakeResponse(self._get_payload)


class DummyConfigManager:
    """Config manager surface needed by RestAPI for these tests."""

    def __init__(self):
        now = datetime.now().timestamp()
        self.id_token = "id-token"
        self.refresh_token = "refresh-token"
        self.id_token_expires_at = now + 3600
        self.serial_number = None
        self.motor_unit_serial = None
        self.aws_credentials_expiry = 0
        self.last_token_fetch = now
        self.last_aws_credentials_fetch = 0
        self.entry_id = "entry-id"
        self.updated_aws_fetch = None
        self.updated_aws_expiry = None

    @property
    def config_data(self):
        return None

    async def update_tokens(self, *_args, **_kwargs):
        return None

    async def reset_login_details(self):
        return None

    async def invalidate_id_token(self):
        self.id_token = None
        self.id_token_expires_at = 0

    async def update_serial_number(self, serial_number: str):
        self.serial_number = serial_number

    async def update_motor_unit_serial(self, motor_unit_serial: str):
        self.motor_unit_serial = motor_unit_serial

    async def update_last_aws_credentials_fetch(self, timestamp: float):
        self.updated_aws_fetch = timestamp
        self.last_aws_credentials_fetch = timestamp

    async def update_aws_credentials_expiry(self, expiry: float):
        self.updated_aws_expiry = expiry
        self.aws_credentials_expiry = expiry


class TokenStoringConfigManager(DummyConfigManager):
    """Stores and clears tokens the way ConfigManager does."""

    async def update_tokens(self, id_token, refresh_token, expires_at):
        self.id_token = id_token
        if refresh_token is not None:
            self.refresh_token = refresh_token
        self.id_token_expires_at = expires_at

    async def reset_login_details(self):
        self.id_token = None
        self.refresh_token = None
        self.id_token_expires_at = 0


class StatusResponse(FakeResponse):
    """Raises aiohttp's ClientResponseError on an error status, as aiohttp does."""

    def raise_for_status(self):
        if self.status >= 400:
            raise ClientResponseError(
                SimpleNamespace(real_url="https://example.invalid"),
                (),
                status=self.status,
                message="error",
            )


class ScriptedSession:
    """Answers `status` to the first `times` requests (every request when None), then 200.

    Records each request's Authorization header, and refuses a sixth request so a
    retry loop fails fast instead of recursing.
    """

    def __init__(self, status: int, times: int | None):
        self.status = status
        self.times = times
        self.auth_headers: list[str | None] = []

    def post(self, _url, headers=None, data=None):
        self.auth_headers.append(headers.get("Authorization"))
        if len(self.auth_headers) > 5:
            raise RuntimeError("request loop")
        failing = self.times is None or len(self.auth_headers) <= self.times
        return StatusResponse(
            {"Data": {"Sernum": "123"}}, status=self.status if failing else 200
        )


class TextResponse(FakeResponse):
    """Response with a raw text body, such as an HTML error page."""

    def __init__(self, body: str, status: int):
        super().__init__({}, status=status)
        self._body = body

    async def text(self) -> str:
        return self._body


@pytest.mark.asyncio
async def test_cognito_initiate_auth_sets_user_agent():
    """Cognito initiate auth includes User-Agent headers."""
    session = FakeSession(post_payload={"ChallengeName": "CUSTOM_CHALLENGE", "Session": "x"})
    info = DummyIntegrationInfo()

    await cognito_initiate_auth(session, "user@example.com", integration_info=info)

    assert session.last_headers["User-Agent"] == "HA-MyDolphin-Plus/test"


@pytest.mark.asyncio
async def test_cognito_refresh_rejection_is_an_auth_error():
    """Only Cognito's explicit auth error invalidates a stored refresh token."""

    class RejectedSession:
        def post(self, *_args, **_kwargs):
            return FakeResponse({"__type": "NotAuthorizedException"}, status=400)

    with pytest.raises(CognitoAuthError):
        await _cognito_call(RejectedSession(), "InitiateAuth", {})


@pytest.mark.asyncio
async def test_cognito_transport_failure_is_not_an_auth_error():
    """Connectivity failures must remain retryable."""

    class UnreachableSession:
        def post(self, *_args, **_kwargs):
            raise OSError("DNS unavailable")

    with pytest.raises(CognitoRequestError):
        await _cognito_call(UnreachableSession(), "InitiateAuth", {})


@pytest.mark.asyncio
async def test_fetch_user_profile_sets_user_agent():
    """authenticate-user request includes User-Agent headers."""
    session = FakeSession(post_payload={"Data": {"Sernum": "123"}})
    info = DummyIntegrationInfo()

    await fetch_user_profile(session, "id-token", integration_info=info)

    assert session.last_headers["User-Agent"] == "HA-MyDolphin-Plus/test"
    assert session.last_headers["Authorization"] == "Bearer id-token"


@pytest.mark.asyncio
async def test_fetch_aws_credentials_sets_user_agent():
    """getToken request includes User-Agent headers."""
    session = FakeSession(get_payload={"Data": {"AccessKeyId": "AKIA"}})
    info = DummyIntegrationInfo()

    await fetch_aws_credentials(session, "id-token", integration_info=info)

    assert session.last_headers["User-Agent"] == "HA-MyDolphin-Plus/test"
    assert session.last_headers["Authorization"] == "Bearer id-token"


@pytest.mark.asyncio
async def test_update_tokens_does_not_touch_aws_fetch_timestamp():
    """Token refresh timestamp is decoupled from AWS fetch timestamp."""
    manager = ConfigManager(None)
    manager._data = {
        "last-token-fetch": 0,
        "last-aws-credentials-fetch": 99,
    }

    async def noop_save():
        return None

    manager._save = noop_save

    await manager.update_tokens("id", "refresh", 1234567890)

    assert manager.last_aws_credentials_fetch == 99


@pytest.mark.asyncio
async def test_stale_aws_cache_metadata_does_not_clear_login_tokens():
    """Expired AWS cache metadata on startup should not force Cognito reauth."""
    now = datetime.now().timestamp()
    manager = ConfigManager(None)
    manager._data = {
        STORAGE_DATA_ID_TOKEN: "id-token",
        STORAGE_DATA_REFRESH_TOKEN: "refresh-token",
        STORAGE_DATA_ID_TOKEN_EXPIRES_AT: now + 3600,
        STORAGE_DATA_LAST_TOKEN_FETCH: now,
        STORAGE_DATA_LAST_AWS_CREDENTIALS_FETCH: now - 7200,
        AWS_CREDENTIALS_EXPIRY: now - 60,
    }
    saved = {"called": False}

    async def mark_saved():
        saved["called"] = True

    manager._save = mark_saved

    await manager._validate_cached_credentials()

    assert manager.id_token == "id-token"
    assert manager.refresh_token == "refresh-token"
    assert manager.last_aws_credentials_fetch == 0
    assert manager.aws_credentials_expiry == 0
    assert saved["called"] is True


@pytest.mark.asyncio
async def test_refresh_aws_credentials_uses_aws_fetch_timestamp(monkeypatch):
    """Recent token refresh should not throttle AWS credential fetch."""
    cfg = DummyConfigManager()
    cfg.last_token_fetch = datetime.now().timestamp()
    cfg.last_aws_credentials_fetch = 0
    api = RestAPI(None, cfg)
    api._session = object()
    api.set_local_async_dispatcher_send(lambda *_args: None)

    called = {"fetch": False}

    async def fake_fetch_aws_credentials(_session, _id_token, integration_info=None):
        called["fetch"] = True
        assert integration_info is not None
        return {
            "Token": "t",
            "AccessKeyId": "ak",
            "SecretAccessKey": "sk",
        }

    monkeypatch.setattr(rest_api_module, "fetch_aws_credentials", fake_fetch_aws_credentials)

    await api._refresh_aws_credentials()

    assert called["fetch"] is True
    assert cfg.updated_aws_fetch is not None


@pytest.mark.asyncio
async def test_rate_limited_with_expired_cache_sets_failed():
    """Rate-limited path should not claim connected with expired cache."""
    cfg = DummyConfigManager()
    now = datetime.now().timestamp()
    cfg.last_aws_credentials_fetch = now
    cfg.aws_credentials_expiry = now - 60
    api = RestAPI(None, cfg)
    api._session = object()
    api.set_local_async_dispatcher_send(lambda *_args: None)
    for field in API_TOKEN_FIELDS:
        api.data[field] = f"cached-{field}"

    await api._refresh_aws_credentials()

    assert api.status == ConnectivityStatus.FAILED


@pytest.mark.asyncio
async def test_cognito_refresh_transport_failure_retains_tokens(monkeypatch):
    """A transport failure must not be treated as a rejected refresh token."""
    cfg = TokenStoringConfigManager()
    api = RestAPI(None, cfg)
    api._session = object()
    api.set_local_async_dispatcher_send(lambda *_args: None)

    async def transport_failure(*_args, **_kwargs):
        raise CognitoRequestError("DNS unavailable")

    monkeypatch.setattr(rest_api_module, "cognito_refresh", transport_failure)

    assert await api._ensure_id_token_valid() is True
    cfg.id_token_expires_at = 0
    assert await api._ensure_id_token_valid() is False
    assert cfg.refresh_token == "refresh-token"
    assert api.status == ConnectivityStatus.FAILED


@pytest.mark.asyncio
async def test_cognito_refresh_auth_failure_clears_tokens(monkeypatch):
    """Only an explicit Cognito auth rejection requires reauthentication."""
    cfg = DummyConfigManager()
    cfg.id_token_expires_at = 0
    cleared = {"called": False}

    async def reset_login_details():
        cleared["called"] = True

    cfg.reset_login_details = reset_login_details
    api = RestAPI(None, cfg)
    api._session = object()
    api.set_local_async_dispatcher_send(lambda *_args: None)

    async def auth_failure(*_args, **_kwargs):
        raise CognitoAuthError("Refresh rejected")

    monkeypatch.setattr(rest_api_module, "cognito_refresh", auth_failure)

    assert await api._ensure_id_token_valid() is False
    assert cleared["called"] is True
    assert api.status == ConnectivityStatus.EXPIRED_TOKEN


@pytest.mark.asyncio
async def test_invalidate_id_token_keeps_refresh_token():
    """Invalidating the IdToken keeps the refresh token, so no new OTP is needed."""
    manager = ConfigManager(None)
    manager._data = {
        STORAGE_DATA_ID_TOKEN: "id-token",
        STORAGE_DATA_ID_TOKEN_EXPIRES_AT: 1234567890,
        STORAGE_DATA_REFRESH_TOKEN: "refresh-token",
    }
    saved = {"called": False}

    async def mark_saved():
        saved["called"] = True

    manager._save = mark_saved

    await manager.invalidate_id_token()

    assert manager.id_token is None
    assert manager.id_token_expires_at == 0
    assert manager.refresh_token == "refresh-token"
    assert saved["called"] is True


def _api_on_session(monkeypatch, status: int, times: int | None, refresh_error=None):
    """RestAPI on a ScriptedSession, with the Cognito refresh stubbed and counted.

    The stubbed refresh returns a new IdToken, or raises `refresh_error` when given.
    """
    cfg = TokenStoringConfigManager()
    api = RestAPI(None, cfg)
    api._session = ScriptedSession(status, times)
    api.set_local_async_dispatcher_send(lambda *_args: None)
    refreshes: list[str] = []

    async def fake_refresh(_session, refresh_token, integration_info=None):
        refreshes.append(refresh_token)
        if refresh_error is not None:
            raise refresh_error
        return {"IdToken": f"new-id-token-{len(refreshes)}", "ExpiresIn": 3600}

    monkeypatch.setattr(rest_api_module, "cognito_refresh", fake_refresh)
    return api, cfg, refreshes


@pytest.mark.asyncio
async def test_http_401_refreshes_id_token_and_retries_once(monkeypatch):
    """A 401 renews only the IdToken and repeats the request with the new one."""
    api, cfg, refreshes = _api_on_session(monkeypatch, 401, times=1)

    payload = await api._bearer_post("https://example.invalid")

    assert payload == {"Data": {"Sernum": "123"}}
    assert refreshes == ["refresh-token"]
    assert api._session.auth_headers == ["Bearer id-token", "Bearer new-id-token-1"]
    assert cfg.refresh_token == "refresh-token"


@pytest.mark.asyncio
async def test_http_401_retry_is_bounded(monkeypatch):
    """A persistent 401 costs one refresh and one retry, then reports FAILED."""
    api, cfg, refreshes = _api_on_session(monkeypatch, 401, times=None)

    payload = await api._bearer_post("https://example.invalid")

    assert payload is None
    assert len(refreshes) == 1
    assert len(api._session.auth_headers) == 2
    assert api.status == ConnectivityStatus.FAILED
    assert cfg.refresh_token == "refresh-token"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("refresh_error", "status", "refresh_token"),
    [
        (CognitoAuthError("rejected"), ConnectivityStatus.EXPIRED_TOKEN, None),
        (
            CognitoRequestError("DNS unavailable"),
            ConnectivityStatus.FAILED,
            "refresh-token",
        ),
    ],
    ids=["refresh-rejected", "refresh-unreachable"],
)
async def test_http_401_with_failed_refresh_is_not_retried(
    monkeypatch, refresh_error, status, refresh_token
):
    """When the refresh after a 401 fails, the request is not repeated.

    Only a rejected refresh token clears the login; an unreachable Cognito keeps it.
    """
    api, cfg, refreshes = _api_on_session(
        monkeypatch, 401, times=None, refresh_error=refresh_error
    )

    payload = await api._bearer_post("https://example.invalid")

    assert payload is None
    assert len(refreshes) == 1
    assert len(api._session.auth_headers) == 1
    assert api.status == status
    assert cfg.refresh_token == refresh_token


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("http_status", "status"),
    [(500, ConnectivityStatus.FAILED), (404, ConnectivityStatus.API_NOT_FOUND)],
    ids=["http-500", "http-404"],
)
async def test_http_error_other_than_401_is_not_refreshed(
    monkeypatch, http_status, status
):
    """Only a 401 triggers the refresh-and-retry; other errors just set the status."""
    api, cfg, refreshes = _api_on_session(monkeypatch, http_status, times=None)

    payload = await api._bearer_post("https://example.invalid")

    assert payload is None
    assert refreshes == []
    assert len(api._session.auth_headers) == 1
    assert api.status == status
    assert cfg.refresh_token == "refresh-token"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "body", "expected"),
    [
        (
            400,
            '{"__type": "com.amazonaws.cognito#NotAuthorizedException"}',
            CognitoAuthError,
        ),
        (400, '{"__type": "TooManyRequestsException"}', CognitoRequestError),
        (500, '{"__type": "InternalErrorException"}', CognitoRequestError),
        (502, "<html>502 Bad Gateway</html>", CognitoRequestError),
    ],
    ids=["namespaced-not-authorized", "throttled", "server-error", "html-error-page"],
)
async def test_cognito_error_classification(status, body, expected):
    """Only NotAuthorizedException, namespaced or not, is an auth rejection."""

    class ErrorSession:
        def post(self, *_args, **_kwargs):
            return TextResponse(body, status)

    # Match the message too, so each case is proven to take its own branch rather
    # than the generic "request failed" handler.
    message = (
        "rejected authentication"
        if expected is CognitoAuthError
        else f"returned {status}"
    )
    with pytest.raises(expected, match=message):
        await _cognito_call(ErrorSession(), "InitiateAuth", {})
