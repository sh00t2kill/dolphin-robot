"""Tests for the reset filter indicator button semantics."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.mydolphin_plus.common.consts import (
    ATTR_ACTIONS,
    ATTR_ATTRIBUTES,
    ATTR_RESET_FBI,
    ATTR_STATUS,
    DATA_KEY_RESET_FILTER_INDICATOR,
    PLATFORMS,
)
from custom_components.mydolphin_plus.common.entity_descriptions import (
    get_entity_descriptions,
)
from custom_components.mydolphin_plus.common.robot_family import RobotFamily
from custom_components.mydolphin_plus.managers.coordinator import (
    MyDolphinPlusCoordinator,
)
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.const import Platform
from homeassistant.util import slugify


def _build_coordinator(filter_state: int = 100, reset_fbi: bool = False):
    calls = {"reset_filter_indicator": 0}

    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(
        data={"filterBagIndication": {"state": filter_state, "resetFBI": reset_fbi}},
        reset_filter_indicator=lambda: calls.__setitem__(
            "reset_filter_indicator", calls["reset_filter_indicator"] + 1
        ),
    )
    coordinator._system_details = SimpleNamespace(is_updated=True)
    coordinator._build_data_mapping()

    return coordinator, calls


def test_button_platform_is_registered():
    """The button platform must be forwarded so the entity gets created."""
    assert Platform.BUTTON in PLATFORMS

    descriptions = get_entity_descriptions(Platform.BUTTON, RobotFamily.ALL)

    assert [d.key for d in descriptions] == [slugify(DATA_KEY_RESET_FILTER_INDICATOR)]


def test_reset_filter_indicator_data_exposes_press_action():
    """The data handler exposes the filter indicator state and a press action."""
    coordinator, _ = _build_coordinator(filter_state=100, reset_fbi=False)
    description = get_entity_descriptions(Platform.BUTTON, RobotFamily.ALL)[0]

    data = coordinator.get_data(description)

    assert data[ATTR_ATTRIBUTES] == {ATTR_RESET_FBI: False, ATTR_STATUS: 100}
    assert SERVICE_PRESS in data[ATTR_ACTIONS]


@pytest.mark.asyncio
async def test_reset_filter_indicator_press_sends_reset():
    """Pressing the button sends the filter bag indicator reset to the robot."""
    coordinator, calls = _build_coordinator()
    description = get_entity_descriptions(Platform.BUTTON, RobotFamily.ALL)[0]

    action = coordinator.get_device_action(description, SERVICE_PRESS)
    await action(description)

    assert calls["reset_filter_indicator"] == 1
