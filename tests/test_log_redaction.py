"""Tokens and AWS credentials stay out of the log."""

import logging

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mydolphin_plus.common.connectivity_status import (
    ConnectivityStatus,
)
from custom_components.mydolphin_plus.common.consts import DOMAIN
from custom_components.mydolphin_plus.managers.aws_client import AWSClient
from custom_components.mydolphin_plus.managers.config_manager import ConfigManager
from custom_components.mydolphin_plus.managers.rest_api import RestAPI

pytest_plugins = "pytest_homeassistant_custom_component"

SECRETS = {
    "id-token": "secret-id-token",
    "refresh-token": "secret-refresh-token",
    "Token": "secret-aws-session-token",
    "AccessKeyId": "secret-access-key-id",
    "SecretAccessKey": "secret-access-key",
}


def _integration_log(caplog):
    return "\n".join(
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("custom_components.mydolphin_plus")
    )


async def test_config_manager_logs_no_tokens(hass, caplog):
    """Loading and saving the stored config logs no tokens."""
    caplog.set_level(logging.DEBUG)

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    config_manager = ConfigManager(hass, entry)
    await config_manager._store.async_save({entry.entry_id: dict(SECRETS)})

    await config_manager._load()
    await config_manager.update_tokens("new-secret-id-token", None, 0)

    log = _integration_log(caplog)
    assert "loaded:" in log
    assert "Storing config data" in log
    assert "secret" not in log


async def test_rest_api_logs_no_credentials(caplog, monkeypatch):
    """The API data debug line logs no AWS credentials."""
    caplog.set_level(logging.DEBUG)

    async def succeed():
        return True

    api = RestAPI(None, None)
    api._status = ConnectivityStatus.CONNECTED
    api.data.update(SECRETS)
    monkeypatch.setattr(api, "_ensure_id_token_valid", succeed)
    monkeypatch.setattr(api, "_authenticate_user", succeed)
    monkeypatch.setattr(api, "_async_dispatcher_send", lambda *_args: None)
    api._config_manager = type("ConfigManager", (), {"entry_id": "entry-id"})()

    await api.update()

    log = _integration_log(caplog)
    assert "API Data updated" in log
    assert "secret" not in log


async def test_aws_client_logs_no_credentials(caplog, monkeypatch):
    """Starting the AWS IoT client logs no AWS credentials."""
    caplog.set_level(logging.DEBUG)

    async def stop():
        raise RuntimeError("stop before connecting")

    config_manager = type(
        "ConfigManager", (), {"entry_id": "entry-id", "motor_unit_serial": "unit"}
    )()
    client = AWSClient(None, config_manager, lambda: None)
    client._api_data = dict(SECRETS)
    monkeypatch.setattr(client, "_get_certificate", stop)
    monkeypatch.setattr(client, "_set_status", lambda *_args: None)

    await client.initialize()

    log = _integration_log(caplog)
    assert "AWS IAM Credentials" in log
    assert "secret" not in log
