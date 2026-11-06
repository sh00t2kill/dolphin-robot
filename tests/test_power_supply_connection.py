"""Power Supply Connection shows whether the power supply is online."""

from types import SimpleNamespace

import pytest
from homeassistant.const import Platform
from homeassistant.util import slugify

from custom_components.mydolphin_plus.common.consts import (
    ATTR_IS_ON,
    DATA_KEY_POWER_SUPPLY_CONNECTION,
)
from custom_components.mydolphin_plus.common.entity_descriptions import (
    get_entity_descriptions,
)
from custom_components.mydolphin_plus.common.robot_family import RobotFamily
from custom_components.mydolphin_plus.managers.coordinator import (
    MyDolphinPlusCoordinator,
)


def _description() -> object:
    key = slugify(DATA_KEY_POWER_SUPPLY_CONNECTION)
    descriptions = get_entity_descriptions(Platform.BINARY_SENSOR, RobotFamily.ALL)

    return next(d for d in descriptions if d.key == key)


def _coordinator(aws_data: dict) -> MyDolphinPlusCoordinator:
    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator._aws_client = SimpleNamespace(data=aws_data)
    coordinator._system_details = SimpleNamespace(is_updated=True)
    coordinator._build_data_mapping()

    return coordinator


def test_power_supply_connection_is_on_power_supply_device() -> None:
    """The sensor belongs to the power supply, not the robot."""
    assert _description().power_supply


@pytest.mark.parametrize(
    ("aws_data", "is_on"),
    [
        ({"isConnected": {"connected": True}}, True),
        ({"isConnected": {"connected": False}}, False),
        ({}, None),
    ],
)
def test_power_supply_connection_reads_shadow(aws_data: dict, is_on: bool) -> None:  # noqa: FBT001
    """The state comes from isConnected, and is unknown when it is missing."""
    data = _coordinator(aws_data).get_data(_description())

    assert data[ATTR_IS_ON] is is_on
