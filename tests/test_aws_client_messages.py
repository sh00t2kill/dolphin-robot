"""Tests for MQTT message handling in the AWS client."""

from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest

from custom_components.mydolphin_plus.common.clean_modes import CleanModes
import custom_components.mydolphin_plus.managers.aws_client as aws_client_module
from custom_components.mydolphin_plus.managers.aws_client import AWSClient
from custom_components.mydolphin_plus.models.topic_data import TopicData

pytest_plugins = "pytest_homeassistant_custom_component"

SERIAL = "serial"


def _client(hass):
    sent = []

    client = AWSClient.__new__(AWSClient)
    client._loop = hass.loop
    client._config_manager = SimpleNamespace(motor_unit_serial=SERIAL)
    client._topic_data = TopicData(SERIAL)
    client._data = {"cleaningModes": {"all": 120, "short": 60, "pickup": 5}}
    client._robot_family = None
    client._started_mode = None
    client._started_at = 0.0
    client._on_data_update_callback = lambda: None
    client._send_desired_command = sent.append

    return client, sent


async def _report_robot_state(hass, client, robot_state):
    payload = json.dumps(
        {
            "state": {"reported": {"systemState": {"robotState": robot_state}}},
            "version": 1,
            "timestamp": int(time.time()),
        }
    ).encode()

    # The MQTT client calls back on its own thread
    await hass.async_add_executor_job(
        lambda: client._message_callback(
            client._topic_data.update_accepted,
            payload,
            dup=False,
            qos=0,
            retain=False,
        )
    )


@pytest.mark.asyncio
async def test_start_sends_mode_cycle_time_once_robot_starts_up(hass):
    """A start from Home Assistant sends the robot's own time for that mode."""
    client, sent = _client(hass)

    client.set_cleaning_mode(CleanModes.FAST_MODE)
    await _report_robot_state(hass, client, "notConnected")

    assert sent == [{"cleaningMode": {"mode": "short"}}]

    await _report_robot_state(hass, client, "init")
    await _report_robot_state(hass, client, "init")

    assert sent == [
        {"cleaningMode": {"mode": "short"}},
        {"cycleInfo": {"cycleTime": 60}},
    ]


@pytest.mark.asyncio
async def test_start_from_elsewhere_keeps_its_cycle_time(hass):
    """A start from the app or a schedule keeps the time it chose."""
    client, sent = _client(hass)

    await _report_robot_state(hass, client, "init")

    assert sent == []


@pytest.mark.asyncio
async def test_old_start_does_not_send_cycle_time(hass):
    """A start the robot never acted on does not change a later clean."""
    client, sent = _client(hass)

    client.set_cleaning_mode(CleanModes.REGULAR)
    client._started_at -= aws_client_module.CYCLE_TIME_AFTER_START_TIMEOUT_SECONDS + 1
    await _report_robot_state(hass, client, "init")

    assert sent == [{"cleaningMode": {"mode": "all"}}]


@pytest.mark.asyncio
async def test_set_cycle_time_wins_over_start(hass):
    """A time set during start up is not replaced by the mode's own time."""
    client, sent = _client(hass)

    client.set_cleaning_mode(CleanModes.REGULAR)
    client.set_cycle_time(45)
    await _report_robot_state(hass, client, "init")

    assert sent == [
        {"cleaningMode": {"mode": "all"}},
        {"cycleInfo": {"cycleTime": 45}},
    ]
