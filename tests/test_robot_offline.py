"""Entities go unavailable and commands fail while the power supply is offline."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.components.vacuum import SERVICE_START
from homeassistant.const import Platform
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import slugify

from custom_components.mydolphin_plus.common.base_entity import (
    MyDolphinPlusBaseEntity,
)
from custom_components.mydolphin_plus.common.consts import (
    DATA_KEY_AWS_BROKER,
    DATA_KEY_POWER_SUPPLY_CONNECTION,
    DATA_KEY_VACUUM,
    PLATFORMS,
)
from custom_components.mydolphin_plus.common.entity_descriptions import (
    MyDolphinPlusEntityDescription,
    get_entity_descriptions,
)
from custom_components.mydolphin_plus.common.robot_family import RobotFamily
from custom_components.mydolphin_plus.managers.coordinator import (
    MyDolphinPlusCoordinator,
)

ONLINE = {"isConnected": {"connected": True}}
OFFLINE = {"isConnected": {"connected": False}}


def _description(platform: Platform, key: str) -> MyDolphinPlusEntityDescription:
    descriptions = get_entity_descriptions(platform, RobotFamily.ALL)

    return next(d for d in descriptions if d.key == slugify(key))


def _coordinator(aws_data: dict) -> MyDolphinPlusCoordinator:
    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(data=aws_data)
    coordinator.last_update_success = True

    return coordinator


def _entity(
    coordinator: MyDolphinPlusCoordinator,
    description: MyDolphinPlusEntityDescription,
) -> MyDolphinPlusBaseEntity:
    # Skip __init__, which needs the device registry
    entity = MyDolphinPlusBaseEntity.__new__(MyDolphinPlusBaseEntity)
    entity.coordinator = coordinator
    entity.entity_description = description
    entity._local_entity_description = description
    entity._data = {}
    entity._last_available = None

    return entity


@pytest.mark.parametrize(
    ("aws_data", "is_online"),
    [(ONLINE, True), (OFFLINE, False), ({}, True)],
)
def test_power_supply_online_reads_shadow(aws_data: dict, is_online: bool) -> None:  # noqa: FBT001
    """Online unless the robot's state says it is not."""
    assert _coordinator(aws_data).is_power_supply_online is is_online


def test_robot_entities_unavailable_while_offline() -> None:
    """No entity besides the two connectivity sensors stays available offline."""
    kept = {
        slugify(DATA_KEY_AWS_BROKER),
        slugify(DATA_KEY_POWER_SUPPLY_CONNECTION),
    }
    coordinator = _coordinator(OFFLINE)

    for platform in PLATFORMS:
        for description in get_entity_descriptions(platform, RobotFamily.ALL):
            entity = _entity(coordinator, description)

            assert entity.available is (description.key in kept), description.key


def test_robot_entities_available_while_online() -> None:
    """Every entity is available while the power supply is online."""
    coordinator = _coordinator(ONLINE)
    description = _description(Platform.VACUUM, DATA_KEY_VACUUM)

    assert _entity(coordinator, description).available


def test_connectivity_sensor_unavailable_when_update_fails() -> None:
    """A failed coordinator update still makes every entity unavailable."""
    coordinator = _coordinator(ONLINE)
    coordinator.last_update_success = False
    description = _description(Platform.BINARY_SENSOR, DATA_KEY_POWER_SUPPLY_CONNECTION)

    assert not _entity(coordinator, description).available


@pytest.mark.asyncio
async def test_command_fails_while_offline() -> None:
    """A command raises instead of waiting in AWS for the robot."""
    calls = []
    coordinator = _coordinator(OFFLINE)
    coordinator.get_device_action = lambda *args: calls.append(args)
    entity = _entity(coordinator, _description(Platform.VACUUM, DATA_KEY_VACUUM))

    with pytest.raises(HomeAssistantError) as err:
        await entity.async_execute_device_action(SERVICE_START)

    assert err.value.translation_key == "robot_offline"
    assert calls == []


def test_state_written_when_robot_goes_offline() -> None:
    """Going offline updates the entity even if its data stays the same."""
    data = {"state": "docked"}
    writes = []
    coordinator = _coordinator(ONLINE)
    coordinator.get_data = lambda _: dict(data)
    entity = _entity(coordinator, _description(Platform.VACUUM, DATA_KEY_VACUUM))
    entity.async_write_ha_state = lambda: writes.append(entity.available)

    entity._handle_coordinator_update()
    entity._handle_coordinator_update()
    coordinator._aws_client.data = OFFLINE
    entity._handle_coordinator_update()

    assert writes == [True, False]
