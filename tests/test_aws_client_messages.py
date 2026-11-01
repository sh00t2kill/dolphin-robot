"""Tests for MQTT message handling in the AWS client."""

from __future__ import annotations

import asyncio
import json
import time
from types import SimpleNamespace

import pytest

import custom_components.mydolphin_plus.managers.aws_client as aws_client_module
from custom_components.mydolphin_plus.managers.aws_client import AWSClient
from custom_components.mydolphin_plus.models.topic_data import TopicData

pytest_plugins = "pytest_homeassistant_custom_component"

SERIAL = "serial"


@pytest.mark.asyncio
async def test_mode_change_sets_cycle_time_without_blocking(hass, monkeypatch):
    """A clean mode change sets the cycle time later, without holding up MQTT."""
    monkeypatch.setattr(aws_client_module, "CYCLE_TIME_DELAY_SECONDS", 0.05)

    cycle_time_set = asyncio.Event()
    modes = []

    def set_cycle_time(mode):
        modes.append(mode)
        cycle_time_set.set()

    client = AWSClient.__new__(AWSClient)
    client._loop = hass.loop
    client._config_manager = SimpleNamespace(motor_unit_serial=SERIAL)
    client._topic_data = TopicData(SERIAL)
    client._data = {}
    client._robot_family = None
    client._on_data_update_callback = lambda: None
    client._set_cycle_time = set_cycle_time

    payload = json.dumps(
        {
            "state": {"desired": {"cleaningMode": {"mode": "all"}}},
            "version": 1,
            "timestamp": int(time.time()),
        }
    ).encode()

    started = time.monotonic()

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

    assert time.monotonic() - started < aws_client_module.CYCLE_TIME_DELAY_SECONDS
    assert modes == []

    await asyncio.wait_for(cycle_time_set.wait(), timeout=1)

    assert modes == ["all"]
