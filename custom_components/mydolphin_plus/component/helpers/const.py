"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.mydolphin_plus/
"""
import calendar
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.vacuum import VacuumEntityFeature
from homeassistant.const import ATTR_MODE, CONF_ENABLED, CONF_MODE, CONF_STATE
import homeassistant.helpers.config_validation as cv

from ...core.helpers.const import *

VERSION = "0.0.3"

ATTR_FRIENDLY_NAME = "friendly_name"
ATTR_START_TIME = "start_time"
ATTR_STATUS = "status"
ATTR_RESET_FBI = "reset_fbi"
ATTR_RSSI = "RSSI"
ATTR_NETWORK_NAME = "network_name"
ATTR_INTENSITY = "intensity"
ATTR_EXPECTED_END_TIME = "expected_end_time"
ATTR_BATTERY_LEVEL = "battery_level"

ATTR_AWS_IOT_BROKER_STATUS = "aws_iot_broker_status"

ATTR_CALCULATED_STATUS = "calculated_status"
ATTR_PWS_STATUS = "pws_status"
ATTR_ROBOT_STATUS = "robot_status"
ATTR_ROBOT_TYPE = "robot_type"
ATTR_IS_BUSY = "busy"
ATTR_TURN_ON_COUNT = "turn_on_count"
ATTR_TIME_ZONE = "time_zone"

ATTR_ENABLE = "enable"
ATTR_DISABLED = "disabled"

DYNAMIC_TYPE = "type"
DYNAMIC_DESCRIPTION = "description"
DYNAMIC_DESCRIPTION_JOYSTICK = "joystick"
DYNAMIC_DESCRIPTION_TEMPERATURE = "temperature"
DYNAMIC_TYPE_PWS_REQUEST = "pwsRequest"
DYNAMIC_CONTENT_SERIAL_NUMBER = "robotSerial"
DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL = "msmu"
DYNAMIC_CONTENT_REMOTE_CONTROL_MODE = "rcMode"
DYNAMIC_CONTENT_SPEED = "speed"
DYNAMIC_CONTENT_DIRECTION = "direction"

ATTR_REMOTE_CONTROL_MODE_EXIT = "exit"

DATA_ROOT_STATE = "state"
DATA_ROOT_TIMESTAMP = "timestamp"
DATA_ROOT_VERSION = "version"

WS_DATA_DIFF = "diff-seconds"
WS_DATA_TIMESTAMP = "timestamp"
WS_DATA_VERSION = "version"

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
DEFAULT_BATTERY_LEVEL = "NA"

UPDATE_API_INTERVAL = timedelta(seconds=60)
UPDATE_ENTITIES_INTERVAL = timedelta(seconds=1)
LOCATE_OFF_INTERVAL_SECONDS = timedelta(seconds=10)

WS_LAST_UPDATE = "last-update"

BASE_API = "https://mbapp18.maytronics.com/api"
LOGIN_URL = f"{BASE_API}/users/Login/"
TOKEN_URL = f"{BASE_API}/IOT/getToken_DecryptSN/"
ROBOT_DETAILS_URL = f"{BASE_API}/serialnumbers/getrobotdetailsbymusn/"

MAXIMUM_ATTEMPTS_GET_AWS_TOKEN = 5

API_REQUEST_HEADER_TOKEN = "token"
API_REQUEST_SERIAL_EMAIL = "Email"
API_REQUEST_SERIAL_PASSWORD = "Password"
API_REQUEST_SERIAL_NUMBER = "Sernum"

API_RESPONSE_DATA = "Data"
API_RESPONSE_STATUS = "Status"
API_RESPONSE_ALERT = "Alert"
API_RESPONSE_STATUS_FAILURE = "0"
API_RESPONSE_STATUS_SUCCESS = "1"

API_RESPONSE_DATA_TOKEN = "Token"
API_RESPONSE_DATA_ACCESS_KEY_ID = "AccessKeyId"
API_RESPONSE_DATA_SECRET_ACCESS_KEY = "SecretAccessKey"

API_DATA_MOTOR_UNIT_SERIAL = "motor_unit_serial"
API_DATA_SERIAL_NUMBER = "serial_number"
API_DATA_LOGIN_TOKEN = "login_token"

API_TOKEN_FIELDS = [
    API_RESPONSE_DATA_TOKEN,
    API_RESPONSE_DATA_ACCESS_KEY_ID,
    API_RESPONSE_DATA_SECRET_ACCESS_KEY
]

BLOCK_SIZE = 16

MQTT_QOS_0 = 0
MQTT_QOS_1 = 1

MQTT_MESSAGE_ENCODING = "utf-8"

AWS_REGION = "eu-west-1"
AWS_BASE_HOST = f"{AWS_REGION}.amazonaws.com"

AWS_IOT_URL = f"a12rqfdx55bdbv-ats.iot.{AWS_BASE_HOST}"
AWS_IOT_PORT = 443

LOGIN_HEADERS = {
    'appkey': '346BDE92-53D1-4829-8A2E-B496014B586C',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
}
CA_FILE_NAME = "AmazonRootCA.pem"

TOPIC_SHADOW = "$aws/things/{}/shadow"
TOPIC_DYNAMIC = "Maytronics/{}/main"

TOPIC_WILDCARD = "#"

TOPIC_ACTION_GET = "get"
TOPIC_ACTION_UPDATE = "update"

TOPIC_CALLBACK_ACCEPTED = "accepted"
TOPIC_CALLBACK_REJECTED = "rejected"

DATA_ROBOT_NAME = "Robot Name"

DATA_ROBOT_DETAILS = {
    "SERNUM": "Motor Unit Serial",
    "PARTNAME": "Product Name",
    "PARTDES": "Product Description",
    "AppName": "Application Name",
    "RegDate": "Registration Date",
    "MyRobotName": DATA_ROBOT_NAME,
    "isReg": "Is Registered",
    "RobotFamily": "Product Family"
}

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

CLEANING_MODES_SHORT = {
  CLEANING_MODE_REGULAR: "Regular",
  CLEANING_MODE_FAST_MODE: "Fast mode",
  CLEANING_MODE_FLOOR_ONLY: "Floor only",
  CLEANING_MODE_WATER_LINE: "Water line",
  CLEANING_MODE_ULTRA_CLEAN: "Ultra clean",
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

LED_MODES_NAMES = {
    LED_MODE_BLINKING: "Blinking",
    LED_MODE_ALWAYS_ON: "Always on",
    LED_MODE_DISCO: "Disco"
}

SERVICE_NAVIGATE = "navigate"
SERVICE_DAILY_SCHEDULE = "daily_schedule"
SERVICE_DELAYED_CLEAN = "delayed_clean"

CONF_DIRECTION = "direction"
CONF_DAY = "day"
CONF_TIME = "time"

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
    0: "mdi:clock-time-twelve",
    1: "mdi:clock-time-one",
    2: "mdi:clock-time-two",
    3: "mdi:clock-time-three",
    4: "mdi:clock-time-four",
    5: "mdi:clock-time-five",
    6: "mdi:clock-time-six",
    7: "mdi:clock-time-seven",
    8: "mdi:clock-time-eight",
    9: "mdi:clock-time-nine",
    10: "mdi:clock-time-ten",
    11: "mdi:clock-time-eleven",
    12: "mdi:clock-time-twelve",
    13: "mdi:clock-time-one",
    14: "mdi:clock-time-two",
    15: "mdi:clock-time-three",
    16: "mdi:clock-time-four",
    17: "mdi:clock-time-five",
    18: "mdi:clock-time-six",
    19: "mdi:clock-time-seven",
    20: "mdi:clock-time-eight",
    21: "mdi:clock-time-nine",
    22: "mdi:clock-time-ten",
    23: "mdi:clock-time-eleven"
}

PWS_STATE_ON = "on"
PWS_STATE_OFF = "off"
PWS_STATE_HOLD_DELAY = "holdDelay"
PWS_STATE_HOLD_WEEKLY = "holdWeekly"
PWS_STATE_PROGRAMMING = "programming"
PWS_STATE_ERROR = "error"
PWS_STATE_CLEANING = "cleaning"

ROBOT_STATE_FINISHED = "finished"
ROBOT_STATE_FAULT = "fault"
ROBOT_STATE_NOT_CONNECTED = "notConnected"
ROBOT_STATE_PROGRAMMING = "programming"
ROBOT_STATE_INIT = "init"
ROBOT_STATE_SCANNING = "scanning"

CALCULATED_STATES = {
    PWS_STATE_ON: PWS_STATE_ON,
    PWS_STATE_OFF: PWS_STATE_OFF,
    PWS_STATE_PROGRAMMING: PWS_STATE_PROGRAMMING,
    ROBOT_STATE_NOT_CONNECTED: "Disconnected",
    PWS_STATE_HOLD_DELAY: "Idle (Delay)",
    PWS_STATE_HOLD_WEEKLY: "Idle (Schedule)",
}

FILTER_BAG_STATUS = {
    -1: "Unknown",
    0: "Empty",
    1: "Partial full",
    26: "Getting full",
    75: "Almost full",
    100: "Full",
    101: "Fault",
    102: "Not available"
}

FILTER_BAG_ICONS = {
    -1: "mdi:robot-off",
    0: "mdi:gauge-empty",
    1: "mdi:gauge-low",
    26: "mdi:gauge",
    75: "mdi:gauge",
    100: "mdi:gauge-full",
    101: "mdi:robot-dead",
    102: "mdi:robot-confused-outline"
}

VACUUM_FEATURES = VacuumEntityFeature.STATE | \
                  VacuumEntityFeature.FAN_SPEED | \
                  VacuumEntityFeature.RETURN_HOME | \
                  VacuumEntityFeature.SEND_COMMAND | \
                  VacuumEntityFeature.START | \
                  VacuumEntityFeature.STOP | \
                  VacuumEntityFeature.PAUSE | \
                  VacuumEntityFeature.TURN_ON | \
                  VacuumEntityFeature.TURN_OFF | \
                  VacuumEntityFeature.LOCATE

STORAGE_DATA_LOCATING = "locating"
STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY = "aws-token-encrypted-key"

STORAGE_DATA_FILE_CONFIG = "config"
STORAGE_API_LIST = "list"
STORAGE_API_DATA_API = "api"
STORAGE_API_DATA_WS = "ws"

STORAGE_DATA_FILES = [
    STORAGE_DATA_FILE_CONFIG
]

STORAGE_API_DATA = [
    STORAGE_API_DATA_API,
    STORAGE_API_DATA_WS,
]
