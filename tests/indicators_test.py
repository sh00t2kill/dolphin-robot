"""Test file for indicators."""
from copy import copy

from custom_components.mydolphin_plus.common.consts import (
    DATA_SECTION_SYSTEM_STATE,
    DATA_SYSTEM_STATE_IS_BUSY,
    DATA_SYSTEM_STATE_PWS_STATE,
    DATA_SYSTEM_STATE_ROBOT_STATE,
    DATA_SYSTEM_STATE_ROBOT_TYPE,
    DATA_SYSTEM_STATE_TIME_ZONE,
    DATA_SYSTEM_STATE_TIME_ZONE_NAME,
    DATA_SYSTEM_STATE_TURN_ON_COUNT,
    DEFAULT_TIME_ZONE_NAME,
)
from custom_components.mydolphin_plus.common.power_supply_state import PowerSupplyState
from custom_components.mydolphin_plus.common.robot_state import RobotState
from custom_components.mydolphin_plus.models.system_details import SystemDetails

DEVICE_DATA = {
    DATA_SECTION_SYSTEM_STATE: {
        DATA_SYSTEM_STATE_PWS_STATE: PowerSupplyState.OFF,
        DATA_SYSTEM_STATE_ROBOT_STATE: RobotState.NOT_CONNECTED,
        DATA_SYSTEM_STATE_ROBOT_TYPE: None,
        DATA_SYSTEM_STATE_IS_BUSY: False,
        DATA_SYSTEM_STATE_TURN_ON_COUNT: 0,
        DATA_SYSTEM_STATE_TIME_ZONE: 0,
        DATA_SYSTEM_STATE_TIME_ZONE_NAME: DEFAULT_TIME_ZONE_NAME
    }
}

ASSERTS = [
    "Power Supply: on, Robot: fault, Result: error",
    "Power Supply: on, Robot: notConnected, Result: idle",
    "Power Supply: on, Robot: programming, Result: cleaning",
    "Power Supply: on, Robot: init, Result: init",
    "Power Supply: on, Robot: scanning, Result: cleaning",
    "Power Supply: on, Robot: finished, Result: idle",
    "Power Supply: off, Robot: fault, Result: error",
    "Power Supply: off, Robot: notConnected, Result: off",
    "Power Supply: off, Robot: programming, Result: off",
    "Power Supply: off, Robot: init, Result: off",
    "Power Supply: off, Robot: scanning, Result: off",
    "Power Supply: off, Robot: finished, Result: off",
    "Power Supply: holdDelay, Robot: fault, Result: error",
    "Power Supply: holdDelay, Robot: notConnected, Result: idle",
    "Power Supply: holdDelay, Robot: programming, Result: idle",
    "Power Supply: holdDelay, Robot: init, Result: idle",
    "Power Supply: holdDelay, Robot: scanning, Result: idle",
    "Power Supply: holdDelay, Robot: finished, Result: idle",
    "Power Supply: holdWeekly, Robot: fault, Result: error",
    "Power Supply: holdWeekly, Robot: notConnected, Result: idle",
    "Power Supply: holdWeekly, Robot: programming, Result: idle",
    "Power Supply: holdWeekly, Robot: init, Result: idle",
    "Power Supply: holdWeekly, Robot: scanning, Result: idle",
    "Power Supply: holdWeekly, Robot: finished, Result: idle",
    "Power Supply: programming, Robot: fault, Result: error",
    "Power Supply: programming, Robot: notConnected, Result: cleaning",
    "Power Supply: programming, Robot: programming, Result: programming",
    "Power Supply: programming, Robot: init, Result: cleaning",
    "Power Supply: programming, Robot: scanning, Result: cleaning",
    "Power Supply: programming, Robot: finished, Result: idle",
    "Power Supply: error, Robot: fault, Result: error",
    "Power Supply: error, Robot: notConnected, Result: error",
    "Power Supply: error, Robot: programming, Result: error",
    "Power Supply: error, Robot: init, Result: error",
    "Power Supply: error, Robot: scanning, Result: error",
    "Power Supply: error, Robot: finished, Result: error"
]

system_details = SystemDetails()
device_data = copy(DEVICE_DATA)


print(
    f"| Power Supply State "
    f"| Robot State  "
    f"| Calculated State |"
)

print(
    f"| ------------------ "
    f"| -----------  "
    f"| ---------------- |"
)

for power_supply_state in list(PowerSupplyState):
    device_data[DATA_SECTION_SYSTEM_STATE][DATA_SYSTEM_STATE_PWS_STATE] = PowerSupplyState(power_supply_state)

    for robot_state in list(RobotState):
        device_data[DATA_SECTION_SYSTEM_STATE][DATA_SYSTEM_STATE_ROBOT_STATE] = RobotState(robot_state)

        system_details.update(device_data)

        result = (
            f"| {power_supply_state} "
            f"| {robot_state}  "
            f"| {system_details.vacuum_state} |"
        )

        print(result)
