from enum import StrEnum


class JoystickDirection(StrEnum):
    STOP = "stop"
    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"

    def get_speed(self) -> int:
        speed = 0 if self == JoystickDirection.STOP else 100

        return speed
