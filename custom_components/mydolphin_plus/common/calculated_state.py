from enum import StrEnum


class CalculatedState(StrEnum):
    OFF = "off"
    PROGRAMMING = "programming"
    ERROR = "error"
    CLEANING = "cleaning"
    INIT = "init"
    HOLD_DELAY = "hold_delay"
    HOLD_WEEKLY = "hold_weekly"

    @staticmethod
    def is_on_state(value) -> bool:
        is_on = value in [
            CalculatedState.INIT,
            CalculatedState.CLEANING,
            CalculatedState.PROGRAMMING,
            CalculatedState.HOLD_WEEKLY,
            CalculatedState.HOLD_DELAY,
        ]

        return is_on
