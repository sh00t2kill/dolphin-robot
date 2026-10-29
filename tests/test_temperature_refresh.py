"""Temperature refresh and OTP profile regression tests."""

from types import SimpleNamespace

import pytest

from homeassistant.const import ATTR_STATE, Platform

from custom_components.mydolphin_plus.common.connectivity_status import (
    ConnectivityStatus,
)
from custom_components.mydolphin_plus.common.consts import (
    ATTR_ATTRIBUTES,
    DATA_SECTION_DYNAMIC,
    DYNAMIC_CONTENT,
    DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL,
    DYNAMIC_CONTENT_SERIAL_NUMBER,
    DYNAMIC_DESCRIPTION_TEMPERATURE,
    DYNAMIC_TYPE,
    DYNAMIC_TYPE_IOT_RESPONSE,
    WS_TEMPERATURE_LAST_UPDATE,
)
from custom_components.mydolphin_plus.common.entity_descriptions import (
    get_entity_descriptions,
)
from custom_components.mydolphin_plus.common.robot_family import RobotFamily
from custom_components.mydolphin_plus.managers.aws_client import AWSClient
from custom_components.mydolphin_plus.managers.coordinator import (
    MyDolphinPlusCoordinator,
)


def test_missing_family_keeps_temperature_controls_available():
    """The OTP profile omits RobotFamily even for an M700."""
    sensor_keys = {
        item.key
        for item in get_entity_descriptions(Platform.SENSOR, RobotFamily.ALL, True)
    }
    button_keys = {
        item.key
        for item in get_entity_descriptions(Platform.BUTTON, RobotFamily.ALL, True)
    }

    assert "temperature" in sensor_keys
    assert "refresh_temperature" in button_keys
    assert "refresh_temperature" not in {
        item.key
        for item in get_entity_descriptions(Platform.BUTTON, RobotFamily.ALL)
    }


def test_temperature_request_sends_only_dynamic_read_command():
    calls = []
    client = AWSClient.__new__(AWSClient)
    client._config_manager = SimpleNamespace(
        serial_number="robot-serial", motor_unit_serial="motor-serial"
    )
    client._send_dynamic_command = lambda description, payload: calls.append(
        (description, payload)
    )

    client.request_temperature()

    assert calls == [
        (
            DYNAMIC_DESCRIPTION_TEMPERATURE,
            {
                DYNAMIC_CONTENT_SERIAL_NUMBER: "robot-serial",
                DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL: "motor-serial",
            },
        )
    ]


def test_temperature_response_records_report_time():
    client = AWSClient.__new__(AWSClient)
    client._data = {}
    client._dynamic_message_handlers = {}
    client._on_data_update_callback = lambda: None

    client._on_dynamic_content_received(
        {
            DYNAMIC_TYPE: DYNAMIC_TYPE_IOT_RESPONSE,
            DYNAMIC_CONTENT: {DYNAMIC_DESCRIPTION_TEMPERATURE: 257},
        }
    )

    assert client.data[WS_TEMPERATURE_LAST_UPDATE].endswith("+00:00")


def test_temperature_is_unknown_until_reported():
    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(data={})

    assert coordinator._get_temperature_data(None) == {ATTR_STATE: None}

    coordinator._aws_client.data = {
        DATA_SECTION_DYNAMIC: {
            DYNAMIC_TYPE_IOT_RESPONSE: {DYNAMIC_DESCRIPTION_TEMPERATURE: 257}
        }
    }
    assert coordinator._get_temperature_data(None) == {ATTR_STATE: 25.7}

    coordinator._aws_client.data[WS_TEMPERATURE_LAST_UPDATE] = (
        "2026-10-26T00:00:00+00:00"
    )
    assert coordinator._get_temperature_data(None) == {
        ATTR_STATE: 25.7,
        ATTR_ATTRIBUTES: {WS_TEMPERATURE_LAST_UPDATE: "2026-10-26T00:00:00+00:00"},
    }


@pytest.mark.asyncio
async def test_button_request_rejects_disconnected_broker():
    from homeassistant.exceptions import HomeAssistantError

    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(status=None)

    with pytest.raises(HomeAssistantError):
        await coordinator.async_request_temperature()


@pytest.mark.asyncio
async def test_button_request_publishes_when_connected():
    requests = []
    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(
        status=ConnectivityStatus.CONNECTED,
        request_temperature=lambda: requests.append("temperature"),
    )

    await coordinator.async_request_temperature()

    assert requests == ["temperature"]


@pytest.mark.asyncio
async def test_missing_family_enables_automatic_temperature_requests():
    """A missing OTP RobotFamily should still request temperature on each poll."""
    client = AWSClient.__new__(AWSClient)

    await client.update_api_data({})
    assert client._robot_family == RobotFamily.ALL
    assert client._robot_family_missing is True

    await client.update_api_data({"Robot Family": "M700"})
    assert client._robot_family == RobotFamily.M700
    assert client._robot_family_missing is False

    await client.update_api_data(None)
    assert client._robot_family_missing is False


def test_empty_iot_response_is_unknown():
    """An iotResponse message without content must not break the sensor."""
    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(
        data={DATA_SECTION_DYNAMIC: {DYNAMIC_TYPE_IOT_RESPONSE: None}}
    )
    assert coordinator._get_temperature_data(None) == {ATTR_STATE: None}

    coordinator._aws_client.data = {DATA_SECTION_DYNAMIC: None}
    assert coordinator._get_temperature_data(None) == {ATTR_STATE: None}


def test_automatic_temperature_requests_are_limited(monkeypatch):
    """Polling every 30 seconds should request temperature at most every 10 minutes."""
    import custom_components.mydolphin_plus.managers.aws_client as aws_module

    now = [1000.0]
    monkeypatch.setattr(aws_module, "monotonic", lambda: now[0])
    client = AWSClient.__new__(AWSClient)
    client._config_manager = SimpleNamespace(
        serial_number="robot-serial", motor_unit_serial="motor-serial"
    )
    client._send_dynamic_command = lambda description, payload: None
    client._last_temperature_request = None

    assert client._is_temperature_request_due()
    client.request_temperature()
    now[0] += 30
    assert not client._is_temperature_request_due()
    now[0] += 570
    assert client._is_temperature_request_due()


def test_report_time_uses_power_supply_measurement_time():
    """A resent reading keeps the time the power supply measured it."""
    client = AWSClient.__new__(AWSClient)
    client._data = {"systemState": {"timeZone": 660}}
    client._dynamic_message_handlers = {}
    client._on_data_update_callback = lambda: None

    # 21:56:16 local (UTC+11) on 28 October 2026, sent as local-time epoch.
    client._on_dynamic_content_received(
        {
            DYNAMIC_TYPE: DYNAMIC_TYPE_IOT_RESPONSE,
            DYNAMIC_CONTENT: {
                DYNAMIC_DESCRIPTION_TEMPERATURE: 241,
                "timeStamp": 1793224576,
            },
        }
    )

    assert client.data[WS_TEMPERATURE_LAST_UPDATE] == "2026-10-28T10:56:16+00:00"


def test_report_time_falls_back_to_receive_time():
    """Missing time zone or a future device clock uses the receive time."""
    from datetime import UTC, datetime, timedelta

    client = AWSClient.__new__(AWSClient)
    client._data = {}
    client._dynamic_message_handlers = {}
    client._on_data_update_callback = lambda: None
    future = int((datetime.now(UTC) + timedelta(days=2)).timestamp())

    for system_state, device_time in (({}, 1793224576), ({"timeZone": 0}, future)):
        client._data = {"systemState": system_state}
        before = datetime.now(UTC)
        client._on_dynamic_content_received(
            {
                DYNAMIC_TYPE: DYNAMIC_TYPE_IOT_RESPONSE,
                DYNAMIC_CONTENT: {
                    DYNAMIC_DESCRIPTION_TEMPERATURE: 241,
                    "timeStamp": device_time,
                },
            }
        )
        reported = datetime.fromisoformat(client.data[WS_TEMPERATURE_LAST_UPDATE])
        assert before <= reported <= datetime.now(UTC)
