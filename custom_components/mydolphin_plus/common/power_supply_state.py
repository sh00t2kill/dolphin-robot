from enum import StrEnum


class PowerSupplyState(StrEnum):
    ON = "on"
    OFF = "off"
    HOLD_DELAY = "holdDelay"
    HOLD_WEEKLY = "holdWeekly"
    PROGRAMMING = "programming"
    ERROR = "error"
