"""Tests for auth headers and rate-limit semantics."""

from __future__ import annotations

from datetime import datetime

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
    cognito_initiate_auth,
    fetch_aws_credentials,
    fetch_user_profile,
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


@pytest.mark.asyncio
async def test_cognito_initiate_auth_sets_user_agent():
    """Cognito initiate auth includes User-Agent headers."""
    session = FakeSession(post_payload={"ChallengeName": "CUSTOM_CHALLENGE", "Session": "x"})
    info = DummyIntegrationInfo()

    await cognito_initiate_auth(session, "user@example.com", integration_info=info)

    assert session.last_headers["User-Agent"] == "HA-MyDolphin-Plus/test"


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
