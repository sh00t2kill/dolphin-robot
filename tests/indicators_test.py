"""Test file for indicators."""
from custom_components.mydolphin_plus.common.consts import (
    PWS_STATE_CLEANING,
    PWS_STATE_ERROR,
    PWS_STATE_HOLD_DELAY,
    PWS_STATE_HOLD_WEEKLY,
    PWS_STATE_OFF,
    PWS_STATE_ON,
    PWS_STATE_PROGRAMMING,
    ROBOT_STATE_FAULT,
    ROBOT_STATE_FINISHED,
    ROBOT_STATE_INIT,
    ROBOT_STATE_NOT_CONNECTED,
    ROBOT_STATE_PROGRAMMING,
    ROBOT_STATE_SCANNING,
)

IS_ROBOT_BUSY = "isBusy"


class IndicatorType:
    """Indicator types."""

    ROBOT_STATE_NOT_CONNECTED = "ROBOT_STATE_NOT_CONNECTED"
    ROBOT_STATE_PROGRAMMING = "ROBOT_STATE_PROGRAMMING"
    GENERAL_ERROR_FALLBACK_ROBOT_OFF = "GENERAL_ERROR_FALLBACK_ROBOT_OFF"
    GENERAL_ERROR_FALLBACK_ROBOT_ON = "GENERAL_ERROR_FALLBACK_ROBOT_ON"
    ROBOT_IS_BUSY = "ROBOT_IS_BUSY"
    PWS_NOT_CONNECTED_TO_CLOUD = "PWS_NOT_CONNECTED_TO_CLOUD"


changeWifiToBleProcess = False
CONNECTED_TO_WIFI = "wifi"
available_states = []


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
        PWS_STATE_HOLD_DELAY,
        PWS_STATE_HOLD_WEEKLY,
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
        and connectivity_type in [CONNECTED_TO_WIFI]
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
    if pws_cloud_state in [ROBOT_STATE_NOT_CONNECTED] and connectivity_type in [
        CONNECTED_TO_WIFI
    ]:
        result = IndicatorType.PWS_NOT_CONNECTED_TO_CLOUD

    print(result)


def run(pws_state: str, robot_state: str):
    """Simulate calculation."""
    calculated_status = PWS_STATE_OFF

    pws_on = pws_state in [
        PWS_STATE_ON,
        PWS_STATE_HOLD_DELAY,
        PWS_STATE_HOLD_WEEKLY,
        PWS_STATE_PROGRAMMING,
    ]
    pws_error = pws_state in [ROBOT_STATE_NOT_CONNECTED]
    pws_cleaning = pws_state in [PWS_STATE_ON]
    pws_programming = pws_state == PWS_STATE_PROGRAMMING

    robot_error = robot_state in [ROBOT_STATE_FAULT, ROBOT_STATE_NOT_CONNECTED]
    robot_cleaning = robot_state not in [
        ROBOT_STATE_INIT,
        ROBOT_STATE_SCANNING,
        ROBOT_STATE_NOT_CONNECTED,
    ]
    robot_programming = robot_state == PWS_STATE_PROGRAMMING

    if pws_error or robot_error:
        calculated_status = PWS_STATE_ERROR

    elif pws_programming and robot_programming:
        calculated_status = PWS_STATE_PROGRAMMING

    elif pws_on:
        if (pws_cleaning and robot_cleaning) or (
            pws_programming and not robot_programming
        ):
            calculated_status = PWS_STATE_CLEANING

        else:
            calculated_status = PWS_STATE_ON

    capabilities = []

    if calculated_status in [PWS_STATE_OFF, PWS_STATE_ERROR]:
        capabilities.append("Turn On")

    if calculated_status in [PWS_STATE_ON, PWS_STATE_CLEANING, PWS_STATE_PROGRAMMING]:
        capabilities.append("Turn Off")

    if calculated_status in [PWS_STATE_ON]:
        capabilities.append("Start")

    if calculated_status in [PWS_STATE_CLEANING]:
        capabilities.append("Stop")

    actions = ", ".join(capabilities)

    print(
        f"| {calculated_status.capitalize().ljust(len(PWS_STATE_PROGRAMMING) + 1, ' ')} "
        f"| {pws_state.ljust(len(PWS_STATE_PROGRAMMING) + 1, ' ')} "
        f"| {robot_state.ljust(len(PWS_STATE_PROGRAMMING) + 1, ' ')} "
        f"| {actions.ljust(16, ' ')} |"
    )

    if calculated_status.capitalize() not in available_states:
        available_states.append(calculated_status.capitalize())


print(
    f"| {'State'.ljust(len(PWS_STATE_PROGRAMMING) + 1, ' ')} "
    f"| {'PWS'.ljust(len(PWS_STATE_PROGRAMMING) + 1, ' ')} "
    f"| {'Robot'.ljust(len(PWS_STATE_PROGRAMMING) + 1, ' ')} "
    f"| {'Actions'.ljust(16, ' ')} |"
)

print(
    f"| {''.ljust(len(PWS_STATE_PROGRAMMING) + 1, '-')} "
    f"| {''.ljust(len(PWS_STATE_PROGRAMMING) + 1, '-')} "
    f"| {''.ljust(len(PWS_STATE_PROGRAMMING) + 1, '-')} "
    f"| {''.ljust(16, '-')} |"
)

run(PWS_STATE_OFF, ROBOT_STATE_NOT_CONNECTED)
run(PWS_STATE_OFF, ROBOT_STATE_FAULT)
run(PWS_STATE_OFF, PWS_STATE_PROGRAMMING)
run(PWS_STATE_OFF, ROBOT_STATE_FINISHED)
run(PWS_STATE_OFF, ROBOT_STATE_INIT)
run(PWS_STATE_OFF, ROBOT_STATE_SCANNING)

run(PWS_STATE_ON, ROBOT_STATE_NOT_CONNECTED)
run(PWS_STATE_ON, ROBOT_STATE_FAULT)
run(PWS_STATE_ON, PWS_STATE_PROGRAMMING)
run(PWS_STATE_ON, ROBOT_STATE_FINISHED)
run(PWS_STATE_ON, ROBOT_STATE_INIT)
run(PWS_STATE_ON, ROBOT_STATE_SCANNING)

run(PWS_STATE_HOLD_DELAY, ROBOT_STATE_NOT_CONNECTED)
run(PWS_STATE_HOLD_DELAY, ROBOT_STATE_FAULT)
run(PWS_STATE_HOLD_DELAY, PWS_STATE_PROGRAMMING)
run(PWS_STATE_HOLD_DELAY, ROBOT_STATE_FINISHED)
run(PWS_STATE_HOLD_DELAY, ROBOT_STATE_INIT)
run(PWS_STATE_HOLD_DELAY, ROBOT_STATE_SCANNING)

run(PWS_STATE_HOLD_WEEKLY, ROBOT_STATE_NOT_CONNECTED)
run(PWS_STATE_HOLD_WEEKLY, ROBOT_STATE_FAULT)
run(PWS_STATE_HOLD_WEEKLY, PWS_STATE_PROGRAMMING)
run(PWS_STATE_HOLD_WEEKLY, ROBOT_STATE_FINISHED)
run(PWS_STATE_HOLD_WEEKLY, ROBOT_STATE_INIT)
run(PWS_STATE_HOLD_WEEKLY, ROBOT_STATE_SCANNING)

run(PWS_STATE_PROGRAMMING, ROBOT_STATE_NOT_CONNECTED)
run(PWS_STATE_PROGRAMMING, ROBOT_STATE_FAULT)
run(PWS_STATE_PROGRAMMING, PWS_STATE_PROGRAMMING)
run(PWS_STATE_PROGRAMMING, ROBOT_STATE_FINISHED)
run(PWS_STATE_PROGRAMMING, ROBOT_STATE_INIT)
run(PWS_STATE_PROGRAMMING, ROBOT_STATE_SCANNING)

print(f"Available states: {', '.join(available_states)}")
