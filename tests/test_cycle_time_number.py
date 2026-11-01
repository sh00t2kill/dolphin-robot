"""Cycle Time shows and changes the time of the current clean."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mydolphin_plus import _remove_old_cycle_time_entities
from custom_components.mydolphin_plus.common.calculated_state import CalculatedState
from custom_components.mydolphin_plus.common.consts import (
    ATTR_ACTIONS,
    DATA_KEY_CYCLE_TIME,
    DOMAIN,
)
from custom_components.mydolphin_plus.common.entity_descriptions import (
    get_entity_descriptions,
)
from custom_components.mydolphin_plus.common.robot_family import RobotFamily
from custom_components.mydolphin_plus.managers.coordinator import (
    MyDolphinPlusCoordinator,
)
from homeassistant.components.number.const import SERVICE_SET_VALUE
from homeassistant.const import ATTR_STATE, Platform
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

pytest_plugins = "pytest_homeassistant_custom_component"


def _description():
    key = slugify(DATA_KEY_CYCLE_TIME)
    descriptions = get_entity_descriptions(Platform.NUMBER, RobotFamily.ALL)

    return next(d for d in descriptions if d.key == key)


def _coordinator(calculated_state, cycle_time=95):
    sent = []
    cleaning_mode = {"mode": "all"}

    if cycle_time is not None:
        cleaning_mode["cycleTime"] = cycle_time

    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(
        data={
            "cycleInfo": {
                "cleaningMode": cleaning_mode,
                "cycleStartTimeUTC": 1793160320,
            }
        },
        set_cycle_time=sent.append,
    )
    coordinator._system_details = SimpleNamespace(
        is_updated=True, calculated_state=calculated_state
    )
    coordinator._build_data_mapping()

    return coordinator, sent


def test_cycle_time_is_the_only_cycle_time_number():
    """The cycle time presets for each clean mode are gone."""
    descriptions = get_entity_descriptions(Platform.NUMBER, RobotFamily.ALL)

    assert [d.key for d in descriptions if "cycle_time" in d.key] == ["cycle_time"]


def test_cycle_time_shows_robot_cycle_time():
    """The state is the cycle time the robot reports."""
    coordinator, _ = _coordinator(CalculatedState.OFF)

    assert coordinator.get_data(_description())[ATTR_STATE] == 95


def test_cycle_time_is_unknown_without_report():
    """The state is unknown until the robot reports a cycle time."""
    coordinator, _ = _coordinator(CalculatedState.OFF, cycle_time=None)

    assert coordinator.get_data(_description())[ATTR_STATE] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [CalculatedState.CLEANING, CalculatedState.INIT])
async def test_set_cycle_time_while_running(state):
    """A new cycle time goes to the robot while it cleans."""
    coordinator, sent = _coordinator(state)
    action = coordinator.get_data(_description())[ATTR_ACTIONS][SERVICE_SET_VALUE]

    await action(_description(), 90.0)

    assert sent == [90]


@pytest.mark.asyncio
async def test_set_cycle_time_while_idle_fails():
    """The robot ignores a new cycle time while idle, so say so."""
    coordinator, sent = _coordinator(CalculatedState.OFF)
    action = coordinator.get_data(_description())[ATTR_ACTIONS][SERVICE_SET_VALUE]

    with pytest.raises(ServiceValidationError):
        await action(_description(), 90.0)

    assert sent == []


@pytest.mark.asyncio
async def test_old_cycle_time_entities_are_removed(hass):
    """The old Cycle Time sensor and per-mode numbers go; the rest stay."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    entity_registry = er.async_get(hass)

    def add(domain, translation_key):
        return entity_registry.async_get_or_create(
            domain,
            DOMAIN,
            f"{domain}_{translation_key}",
            config_entry=entry,
            translation_key=translation_key,
        ).entity_id

    old_sensor = add("sensor", "cycle_time")
    old_presets = [add("number", f"cycle_time_{mode}") for mode in ("all", "pickup")]
    kept = [
        add("number", "cycle_time"),
        add("number", "led_intensity"),
        add("sensor", "cycle_time_left"),
    ]

    _remove_old_cycle_time_entities(hass, entry)

    for entity_id in [old_sensor, *old_presets]:
        assert entity_registry.async_get(entity_id) is None

    for entity_id in kept:
        assert entity_registry.async_get(entity_id) is not None
