"""Tests for vacuum action semantics."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.mydolphin_plus.managers.coordinator import (
    MyDolphinPlusCoordinator,
)
from homeassistant.components.vacuum import VacuumActivity


@pytest.mark.asyncio
async def test_vacuum_pause_stops_active_robot():
    """Pause should send the power-off command when the robot is active."""
    calls = {"pause": 0}

    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(
        pause=lambda: calls.__setitem__("pause", calls["pause"] + 1)
    )

    await coordinator._vacuum_pause(None, VacuumActivity.CLEANING)

    assert calls["pause"] == 1


@pytest.mark.asyncio
async def test_vacuum_pause_ignores_docked_robot():
    """Pause should not send another power-off command while docked."""
    calls = {"pause": 0}

    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(
        pause=lambda: calls.__setitem__("pause", calls["pause"] + 1)
    )

    await coordinator._vacuum_pause(None, VacuumActivity.DOCKED)

    assert calls["pause"] == 0
