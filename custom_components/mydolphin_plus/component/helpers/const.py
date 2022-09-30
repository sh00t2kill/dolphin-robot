"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.mydolphin_plus/
"""
import calendar
from datetime import timedelta

import voluptuous as vol

from homeassistant.const import (
    ATTR_MODE,
    CONF_DEVICE,
    CONF_DEVICE_ID,
    CONF_ENABLED,
    CONF_MODE,
    CONF_STATE,
)
import homeassistant.helpers.config_validation as cv

from ...core.helpers.const import *

VERSION = "0.0.3"

DEFAULT_ICON = "mdi:alarm-light"

ATTR_FRIENDLY_NAME = "friendly_name"
ATTR_START_TIME = "start_time"
ATTR_STATUS = "status"
ATTR_RESET_FBI = "reset_fbi"
ATTR_RSSI = "RSSI"
ATTR_NETWORK_NAME = "network_name"
ATTR_INTENSITY = "intensity"
ATTR_EXPECTED_END_TIME = "expected_end_time"

ATTR_CALCULATED_STATUS = "calculated_status"
ATTR_PWS_STATUS = "pws_status"
ATTR_ROBOT_STATUS = "robot_status"
ATTR_ROBOT_TYPE = "robot_type"
ATTR_IS_BUSY = "busy"
ATTR_TURN_ON_COUNT = "turn_on_count"
ATTR_TIME_ZONE = "time_zone"

ATTR_ENABLE = "enable"
ATTR_DISABLED = "disabled"

DYNAMIC_CONTENT = "content"
DYNAMIC_CONTENT_SERIAL_NUMBER = "serialNumber"
DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL = "motorUnitSerial"
DYNAMIC_CONTENT_REMOTE_CONTROL_MODE = "rcMode"
DYNAMIC_CONTENT_SPEED = "speed"
DYNAMIC_CONTENT_DIRECTION = "direction"

ATTR_REMOTE_CONTROL_MODE_EXIT = "exit"

DATA_ROOT_STATE = "state"
DATA_ROOT_TIMESTAMP = "timestamp"
DATA_ROOT_VERSION = "version"

DATA_SECTION_LED = "led"
DATA_SECTION_DEBUG = "debug"
DATA_SECTION_WIFI = "wifi"
DATA_SECTION_CYCLE_INFO = "cycleInfo"
DATA_SECTION_FILTER_BAG_INDICATION = "filterBagIndication"
DATA_SECTION_WEEKLY_SETTINGS = "weeklySettings"
DATA_SECTION_DELAY = "delay"
DATA_SECTION_FEATURE = "featureEn"
DATA_SECTION_SYSTEM_STATE = "systemState"

DATA_STATE_REPORTED = "reported"
DATA_STATE_DESIRED = "desired"

DATA_SYSTEM_STATE_PWS_STATE = "pwsState"
DATA_SYSTEM_STATE_ROBOT_STATE = "robotState"
DATA_SYSTEM_STATE_ROBOT_TYPE = "robotType"
DATA_SYSTEM_STATE_IS_BUSY = "isBusy"
DATA_SYSTEM_STATE_TURN_ON_COUNT = "rTurnOnCount"
DATA_SYSTEM_STATE_TIME_ZONE = "timeZone"
DATA_SYSTEM_STATE_TIME_ZONE_NAME = "timeZoneName"

DATA_FEATURE_WEEKLY_TIMER = "weeklyTimer"

DATA_SCHEDULE_IS_ENABLED = "isEnabled"
DATA_SCHEDULE_CLEANING_MODE = "cleaningMode"
DATA_SCHEDULE_TIME = "time"
DATA_SCHEDULE_TIME_HOURS = "hours"
DATA_SCHEDULE_TIME_MINUTES = "minutes"
DATA_SCHEDULE_TRIGGERED_BY = "triggeredBy"

DATA_FILTER_BAG_INDICATION_RESET_FBI = "resetFBI"
DATA_FILTER_BAG_INDICATION_RESET_FBI_COMMAND = "resetFbi"

DATA_CYCLE_INFO_CLEANING_MODE = "cleaningMode"
DATA_CYCLE_INFO_CLEANING_MODE_DURATION = "cycleTime"
DATA_CYCLE_INFO_CLEANING_MODE_START_TIME = "cycleStartTimeUTC"

DATA_LED_MODE = "ledMode"
DATA_LED_INTENSITY = "ledIntensity"
DATA_LED_ENABLE = "ledEnable"
DATA_DEBUG_WIFI_RSSI = "WIFI_RSSI"
DATA_WIFI_NETWORK_NAME = "netName"

DEFAULT_LED_INTENSITY = 80
DEFAULT_ENABLE = False
DEFAULT_TIME_ZONE_NAME = "UTC"
DEFAULT_TIME_PART = 255

SCAN_INTERVAL = timedelta(seconds=60)
HEARTBEAT_INTERVAL_SECONDS = timedelta(seconds=25)
TRIGGER_INTERVAL = timedelta(seconds=1)

BASE_API = "https://mbapp18.maytronics.com/api"
LOGIN_URL = f"{BASE_API}/users/Login/"
TOKEN_URL = f"{BASE_API}/IOT/getToken/"
ROBOT_DETAILS_URL = f"{BASE_API}/serialnumbers/getrobotdetailsbymusn/"

MQTT_QOS_AT_LEAST_ONCE = 1

AWS_REGION = "eu-west-1"
AWS_BASE_HOST = f"{AWS_REGION}.amazonaws.com"

AWS_IOT_URL = f"a12rqfdx55bdbv-ats.iot.{AWS_BASE_HOST}"
AWS_IOT_PORT = 443

LOGIN_HEADERS = {
    'appkey': '346BDE92-53D1-4829-8A2E-B496014B586C',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
}
CA_FILE_NAME = "AmazonRootCA.pem"

AWS_DATE_FORMAT = "%Y%m%d"

TOPIC_SHADOW = "$aws/things/{}/shadow"
TOPIC_DYNAMIC = "Maytronics/{}/main"

TOPIC_WILDCARD = "#"

TOPIC_ACTION_GET = "get"
TOPIC_ACTION_UPDATE = "update"

TOPIC_CALLBACK_ACCEPTED = "accepted"
TOPIC_CALLBACK_REJECTED = "rejected"
TOPIC_CALLBACK_DOCUMENTS = "documents"

DATA_ROBOT_DETAILS = {
    "SERNUM": "Motor Unit Serial",
    "PARTNAME": "Product Name",
    "PARTDES": "Product Description",
    "AppName": "Application Name",
    "RegDate": "Registration Date",
    "MyRobotName": "Robot Name",
    "isReg": "Is Registered",
    "RobotFamily": "Product Family"
}

ATTR_CLEANING_MODE = "cleaning_mode"
ATTR_LED_MODE = "led_mode"

CLEANING_MODE_REGULAR = "all"
CLEANING_MODE_FAST_MODE = "short"
CLEANING_MODE_FLOOR_ONLY = "floor"
CLEANING_MODE_WATER_LINE = "water"
CLEANING_MODE_ULTRA_CLEAN = "ultra"
CLEANING_MODE_PICKUP = "pickup"
CLEANING_MODE_ICON_DEFAULT = "mdi:border-all-variant"

CLEANING_MODES = {
  CLEANING_MODE_REGULAR: "Regular - Cleans floor, water and waterline",
  CLEANING_MODE_FAST_MODE: "Fast mode - Cleans the floor",
  CLEANING_MODE_FLOOR_ONLY: "Floor only - Cleans the floor only",
  CLEANING_MODE_WATER_LINE: "Water line - Cleans the walls and water line",
  CLEANING_MODE_ULTRA_CLEAN: "Ultra clean - Deeply cleans the floor, walls and waterline",
}

ICON_CLEANING_MODES = {
    CLEANING_MODE_REGULAR: CLEANING_MODE_ICON_DEFAULT,
    CLEANING_MODE_FAST_MODE: "mdi:clock-fast",
    CLEANING_MODE_FLOOR_ONLY: "mdi:border-bottom-variant",
    CLEANING_MODE_WATER_LINE: "mdi:format-align-top",
    CLEANING_MODE_ULTRA_CLEAN: "mdi:border-all"
}

LED_MODE_BLINKING = "1"
LED_MODE_ALWAYS_ON = "2"
LED_MODE_DISCO = "3"
LED_MODE_ICON_DEFAULT = "mdi:lighthouse-on"

ICON_LED_MODES = {
    LED_MODE_BLINKING: LED_MODE_ICON_DEFAULT,
    LED_MODE_ALWAYS_ON: "mdi:lightbulb-on",
    LED_MODE_DISCO: "mdi:lightbulb-multiple-outline"
}

SERVICE_NAVIGATE = "navigate"
SERVICE_DAILY_SCHEDULE = "daily_schedule"
SERVICE_DELAYED_CLEAN = "delayed_clean"

CONF_DIRECTION = "direction"
CONF_DAY = "day"
CONF_TIME = "time"
CONF_ATTRIBUTES = "attributes"

JOYSTICK_SPEED = 100

JOYSTICK_STOP = "stop"
JOYSTICK_FORWARD = "forward"
JOYSTICK_BACKWARD = "backward"
JOYSTICK_RIGHT = "right"
JOYSTICK_LEFT = "left"

JOYSTICK_DIRECTIONS = [
    JOYSTICK_STOP,
    JOYSTICK_FORWARD,
    JOYSTICK_BACKWARD,
    JOYSTICK_RIGHT,
    JOYSTICK_LEFT
]

SERVICE_SCHEMA_NAVIGATE = vol.Schema(
    {
        vol.Required(CONF_DIRECTION): vol.In([JOYSTICK_DIRECTIONS])
    }
)

SERVICE_SCHEMA_DAILY_SCHEDULE = vol.Schema(
    {
        vol.Optional(CONF_ENABLED, default=False): cv.boolean,
        vol.Required(CONF_DAY): vol.In(list(calendar.day_name)),
        vol.Optional(CONF_MODE, default=CLEANING_MODE_REGULAR): vol.In(CLEANING_MODES.keys()),
        vol.Optional(CONF_TIME, default=None): cv.string
    }
)

SERVICE_SCHEMA_DELAYED_CLEAN = vol.Schema(
    {
        vol.Optional(CONF_ENABLED, default=False): cv.boolean,
        vol.Optional(CONF_MODE, default=CLEANING_MODE_REGULAR): vol.In(CLEANING_MODES.keys()),
        vol.Optional(CONF_TIME, default=None): cv.string
    }
)

SERVICE_VALIDATION = {
    SERVICE_NAVIGATE: SERVICE_SCHEMA_NAVIGATE,
    SERVICE_DAILY_SCHEDULE: SERVICE_SCHEMA_DAILY_SCHEDULE,
    SERVICE_DELAYED_CLEAN: SERVICE_SCHEMA_DELAYED_CLEAN,
}

CLOCK_HOURS_ICONS = {
    "0": "mdi:clock-time-twelve",
    "1": "mdi:clock-time-one",
    "2": "mdi:clock-time-two",
    "3": "mdi:clock-time-three",
    "4": "mdi:clock-time-four",
    "5": "mdi:clock-time-five",
    "6": "mdi:clock-time-six",
    "7": "mdi:clock-time-seven",
    "8": "mdi:clock-time-eight",
    "9": "mdi:clock-time-nine",
    "10": "mdi:clock-time-ten",
    "11": "mdi:clock-time-eleven",
    "12": "mdi:clock-time-twelve",
    "13": "mdi:clock-time-one",
    "14": "mdi:clock-time-two",
    "15": "mdi:clock-time-three",
    "16": "mdi:clock-time-four",
    "17": "mdi:clock-time-five",
    "18": "mdi:clock-time-six",
    "19": "mdi:clock-time-seven",
    "20": "mdi:clock-time-eight",
    "21": "mdi:clock-time-nine",
    "22": "mdi:clock-time-ten",
    "23": "mdi:clock-time-eleven"
}

PWS_STATE_ON = "on"
PWS_STATE_OFF = "off"
PWS_STATE_HOLD_DELAY = "holdDelay"
PWS_STATE_HOLD_WEEKLY = "holdWeekly"
PWS_STATE_PROGRAMMING = "programming"

ROBOT_STATE_FINISHED = "finished"
ROBOT_STATE_FAULT = "fault"
ROBOT_STATE_NOT_CONNECTED = "notConnected"
ROBOT_STATE_PROGRAMMING = "programming"
ROBOT_STATE_INIT = "init"
ROBOT_STATE_SCANNING = "scanning"

UNMAPPED_CALCULATED_STATE = "Unmapped"

CALCULATED_STATES = {
    PWS_STATE_ON: PWS_STATE_ON,
    PWS_STATE_OFF: PWS_STATE_OFF,
    PWS_STATE_PROGRAMMING: PWS_STATE_PROGRAMMING,
    ROBOT_STATE_NOT_CONNECTED: "Disconnected",
    PWS_STATE_HOLD_DELAY: "Idle (Delay)",
    PWS_STATE_HOLD_WEEKLY: "Idle (Schedule)",
}
