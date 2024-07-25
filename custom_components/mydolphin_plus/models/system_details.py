from custom_components.mydolphin_plus.common.calculated_state import CalculatedState
from custom_components.mydolphin_plus.common.clean_modes import CleanModes
from custom_components.mydolphin_plus.common.consts import (
    ATTR_CALCULATED_STATUS,
    ATTR_IS_BUSY,
    ATTR_POWER_SUPPLY_STATE,
    ATTR_ROBOT_STATE,
    ATTR_ROBOT_TYPE,
    ATTR_TIME_ZONE,
    ATTR_TURN_ON_COUNT,
    ATTR_VACUUM_STATE,
    DATA_CYCLE_INFO_CLEANING_MODE,
    DATA_SECTION_CYCLE_INFO,
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
from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_RETURNING,
)
from homeassistant.const import ATTR_MODE


class SystemDetails:
    _is_updated: bool
    _data: dict

    def __init__(self):
        self._is_updated = False
        self._data = {}

    @property
    def is_updated(self) -> bool:
        return self._is_updated

    @property
    def data(self) -> dict:
        return self._data

    @property
    def calculated_state(self) -> CalculatedState:
        return self._data.get(ATTR_CALCULATED_STATUS, CalculatedState.OFF)

    @property
    def vacuum_state(self) -> str:
        return self._data.get(ATTR_VACUUM_STATE, STATE_DOCKED)

    @property
    def power_unit_state(self) -> PowerSupplyState:
        return self._data.get(ATTR_POWER_SUPPLY_STATE, PowerSupplyState.OFF)

    @property
    def robot_state(self) -> RobotState:
        return self._data.get(ATTR_ROBOT_STATE, RobotState.NOT_CONNECTED)

    @property
    def robot_type(self) -> str | None:
        return self._data.get(ATTR_ROBOT_TYPE)

    @property
    def is_busy(self) -> bool | None:
        return self._data.get(ATTR_IS_BUSY)

    @property
    def turn_on_count(self) -> int:
        return self._data.get(ATTR_TURN_ON_COUNT, 0)

    @property
    def time_zone(self) -> str | None:
        return self._data.get(ATTR_TIME_ZONE)

    def update(self, aws_data: dict) -> bool:
        new_data = self._get_updated_data(aws_data)

        changed_keys = [key for key in new_data if new_data[key] != self._data.get(key)]

        was_changed = len(changed_keys) > 0

        if was_changed:
            self._is_updated = True
            self._data = new_data

        return was_changed

    @staticmethod
    def _get_updated_data(aws_data: dict):
        system_state = aws_data.get(DATA_SECTION_SYSTEM_STATE, {})
        power_supply_state = system_state.get(
            DATA_SYSTEM_STATE_PWS_STATE, PowerSupplyState.OFF.value
        )
        robot_state = system_state.get(
            DATA_SYSTEM_STATE_ROBOT_STATE, RobotState.NOT_CONNECTED.value
        )
        robot_type = system_state.get(DATA_SYSTEM_STATE_ROBOT_TYPE)
        is_busy = system_state.get(DATA_SYSTEM_STATE_IS_BUSY, False)
        turn_on_count = system_state.get(DATA_SYSTEM_STATE_TURN_ON_COUNT, 0)
        time_zone = system_state.get(DATA_SYSTEM_STATE_TIME_ZONE, 0)
        time_zone_name = system_state.get(
            DATA_SYSTEM_STATE_TIME_ZONE_NAME, DEFAULT_TIME_ZONE_NAME
        )

        cycle_info = aws_data.get(DATA_SECTION_CYCLE_INFO, {})
        cleaning_mode = cycle_info.get(DATA_CYCLE_INFO_CLEANING_MODE, {})
        mode = cleaning_mode.get(ATTR_MODE, CleanModes.REGULAR)

        calculated_state = CalculatedState.OFF
        vacuum_state = STATE_DOCKED

        if power_supply_state == PowerSupplyState.ERROR:
            calculated_state = CalculatedState.ERROR
            vacuum_state = STATE_ERROR

        elif robot_state == RobotState.FAULT:
            calculated_state = CalculatedState.ERROR
            vacuum_state = STATE_ERROR

        elif power_supply_state == PowerSupplyState.PROGRAMMING:
            if robot_state == RobotState.PROGRAMMING:
                calculated_state = CalculatedState.PROGRAMMING

            elif robot_state != RobotState.FINISHED:
                calculated_state = CalculatedState.CLEANING

        elif power_supply_state == PowerSupplyState.ON:
            if robot_state == RobotState.INIT:
                calculated_state = CalculatedState.INIT

            elif robot_state not in [RobotState.NOT_CONNECTED, RobotState.FINISHED]:
                calculated_state = CalculatedState.CLEANING

            if mode == CleanModes.PICKUP:
                vacuum_state = STATE_RETURNING
            else:
                vacuum_state = STATE_CLEANING

        elif power_supply_state == PowerSupplyState.HOLD_DELAY:
            calculated_state = CalculatedState.HOLD_DELAY

        elif power_supply_state == PowerSupplyState.HOLD_WEEKLY:
            calculated_state = CalculatedState.HOLD_WEEKLY

        result = {
            ATTR_VACUUM_STATE: vacuum_state,
            ATTR_CALCULATED_STATUS: calculated_state,
            ATTR_POWER_SUPPLY_STATE: power_supply_state,
            ATTR_ROBOT_STATE: robot_state,
            ATTR_ROBOT_TYPE: robot_type,
            ATTR_IS_BUSY: is_busy,
            ATTR_TURN_ON_COUNT: turn_on_count,
            ATTR_TIME_ZONE: f"{time_zone_name} ({time_zone})",
        }

        return result
