"""Test file for indicators."""
IS_ROBOT_BUSY = "isBusy"
PWS_CLOUD_STATUS = "pwsCloudStatus"
PWS_CLOUD_STATUS_NOT_CONNECTED = "not connected"
PWS_STATE = "pwsState"
PWS_STATE_OFF = "off"
PWS_STATE_ON = "on"
ROBOT_STATE = "robotState"
ROBOT_STATE_FAULT = "fault"
ROBOT_STATE_FINISHED = "finished"
ROBOT_STATE_INIT = "init"
ROBOT_STATE_MAPPING = "mapping"
ROBOT_STATE_NOT_CONNECTED = "notConnected"
ROBOT_STATE_PROGRAMMING = "programming"
ROBOT_STATE_SCANNING = "scanning"


class IndicatorType:
    """Indicator types."""

    ROBOT_STATE_NOT_CONNECTED = "ROBOT_STATE_NOT_CONNECTED"
    ROBOT_STATE_PROGRAMMING = "ROBOT_STATE_PROGRAMMING"
    GENERAL_ERROR_FALLBACK_ROBOT_OFF = "GENERAL_ERROR_FALLBACK_ROBOT_OFF"
    GENERAL_ERROR_FALLBACK_ROBOT_ON = "GENERAL_ERROR_FALLBACK_ROBOT_ON"
    ROBOT_IS_BUSY = "ROBOT_IS_BUSY"
    PWS_NOT_CONNECTED_TO_CLOUD = "PWS_NOT_CONNECTED_TO_CLOUD"


class Consts:
    """Consts."""

    HOLD_DELAY = "hold_delay"
    HOLD_WEEKLY = "hold_weekly"
    CONNECTED_TO_WIFI = "connected"


changeWifiToBleProcess = False


def indicator(
    pws_state: str,
    robot_state: str,
    pws_cloud_state: str,
    is_busy: bool,
    connectivity_type: str,
):
    """Assumption: indicator to present failed to connect."""
    result = IndicatorType.ROBOT_STATE_NOT_CONNECTED
    if pws_state == "on" and robot_state == ROBOT_STATE_NOT_CONNECTED:
        result = None

    print(result)


def indicator2(
    pws_state: str,
    robot_state: str,
    pws_cloud_state: str,
    is_busy: bool,
    connectivity_type: str,
):
    """Assumption: Is in programming (setup?) state."""
    result = None
    if pws_state == ROBOT_STATE_PROGRAMMING and robot_state == ROBOT_STATE_PROGRAMMING:
        result = IndicatorType.ROBOT_STATE_PROGRAMMING

    print(result)


def indicator3(
    pws_state: str,
    robot_state: str,
    pws_cloud_state: str,
    is_busy: bool,
    connectivity_type: str,
):
    """Assumption: Off."""
    result = None
    if pws_state in [
        "off",
        Consts.HOLD_DELAY,
        Consts.HOLD_WEEKLY,
    ] and robot_state not in [
        ROBOT_STATE_FINISHED,
        "fault",
        "ROBOT_STATE_NOT_CONNECTED",
    ]:
        result = IndicatorType.GENERAL_ERROR_FALLBACK_ROBOT_OFF

    print(result)


def indicator4(
    pws_state: str,
    robot_state: str,
    pws_cloud_state: str,
    is_busy: bool,
    connectivity_type: str,
):
    """Assumption: On."""
    result = None
    if pws_state in ["on"] and robot_state not in [
        ROBOT_STATE_INIT,
        ROBOT_STATE_SCANNING,
        ROBOT_STATE_NOT_CONNECTED,
    ]:
        result = IndicatorType.GENERAL_ERROR_FALLBACK_ROBOT_ON

    if pws_state in [ROBOT_STATE_PROGRAMMING] and robot_state not in [
        ROBOT_STATE_PROGRAMMING
    ]:
        result = IndicatorType.GENERAL_ERROR_FALLBACK_ROBOT_ON

    print(result)


def indicator5(
    pws_state: str,
    robot_state: str,
    pws_cloud_state: str,
    is_busy: bool,
    connectivity_type: str,
):
    """Assumption: Busy."""
    result = None
    if (
        is_busy
        and connectivity_type in [Consts.CONNECTED_TO_WIFI]
        and not changeWifiToBleProcess
    ):
        result = IndicatorType.ROBOT_IS_BUSY

    print(result)


def indicator6(
    pws_state: str,
    robot_state: str,
    pws_cloud_state: str,
    is_busy: bool,
    connectivity_type: str,
):
    """Assumption: Not connected to cloud."""
    result = None
    if pws_cloud_state in [PWS_CLOUD_STATUS_NOT_CONNECTED] and connectivity_type in [
        Consts.CONNECTED_TO_WIFI
    ]:
        result = IndicatorType.PWS_NOT_CONNECTED_TO_CLOUD

    print(result)
