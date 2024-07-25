from enum import StrEnum


class CalculatedState(StrEnum):
    OFF = "off"
    PROGRAMMING = "programming"
    ERROR = "error"
    CLEANING = "cleaning"
    INIT = "init"
    HOLD_DELAY = "holddelay"
    HOLD_WEEKLY = "holdweekly"
