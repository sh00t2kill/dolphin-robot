from enum import StrEnum


class RobotState(StrEnum):
    FAULT = "fault"
    NOT_CONNECTED = "notConnected"
    PROGRAMMING = "programming"
    INIT = "init"
    SCANNING = "scanning"
    FINISHED = "finished"
