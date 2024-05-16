from datetime import timedelta

from homeassistant.components.vacuum import VacuumEntityFeature
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform

MANUFACTURER = "Maytronics"
DEFAULT_NAME = "MyDolphin Plus"
DOMAIN = "mydolphin_plus"
DATA = f"{DOMAIN}_DATA"
LEGACY_KEY_FILE = f"{DOMAIN}.key"
CONFIGURATION_FILE = f"{DOMAIN}.config.json"

INVALID_TOKEN_SECTION = "https://github.com/sh00t2kill/dolphin-robot#invalid-token"

ENTRY_ID_CONFIG = "config"
CONF_TITLE = "title"

SIGNAL_DEVICE_NEW = f"{DOMAIN}_NEW_DEVICE_SIGNAL"
SIGNAL_AWS_CLIENT_STATUS = f"{DOMAIN}_AWS_CLIENT_STATUS_SIGNAL"
SIGNAL_API_STATUS = f"{DOMAIN}_API_SIGNAL"

CONFIGURATION_URL = "https://www.maytronics.com/"

PLATFORMS = [
    Platform.SELECT,
    Platform.LIGHT,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.VACUUM,
    Platform.NUMBER,
]

ATTR_EVENT = "Error"
ATTR_IS_ON = "is_on"
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
DYNAMIC_TYPE_PWS_RESPONSE = "pwsResponse"
DYNAMIC_TYPE_IOT_RESPONSE = "iotResponse"
DYNAMIC_CONTENT = "content"
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

DATA_SECTION_DYNAMIC = "dynamic"
DATA_SECTION_LED = "led"
DATA_SECTION_DEBUG = "debug"
DATA_SECTION_WIFI = "wifi"
DATA_SECTION_CYCLE_INFO = "cycleInfo"
DATA_SECTION_FILTER_BAG_INDICATION = "filterBagIndication"
DATA_SECTION_WEEKLY_SETTINGS = "weeklySettings"
DATA_SECTION_DELAY = "delay"
DATA_SECTION_FEATURE = "featureEn"
DATA_SECTION_SYSTEM_STATE = "systemState"
DATA_SECTION_ROBOT_ERROR = "robotError"
DATA_SECTION_PWS_ERROR = "pwsError"

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

DATA_ERROR_CODE = "errorCode"
DATA_ERROR_TURN_ON_COUNT = "turnOnCount"

DEFAULT_LED_INTENSITY = 80
DEFAULT_ENABLE = False
DEFAULT_TIME_ZONE_NAME = "UTC"
DEFAULT_TIME_PART = 255
DEFAULT_BATTERY_LEVEL = "NA"

UPDATE_API_INTERVAL = timedelta(seconds=60)
UPDATE_ENTITIES_INTERVAL = timedelta(seconds=5)
LOCATE_OFF_INTERVAL_SECONDS = timedelta(seconds=10)
API_RECONNECT_INTERVAL = timedelta(seconds=30)
WS_RECONNECT_INTERVAL = timedelta(minutes=1)

WS_LAST_UPDATE = "last-update"

BASE_API = "https://mbapp18.maytronics.com/api"
LOGIN_URL = f"{BASE_API}/users/Login/"
TOKEN_URL = f"{BASE_API}/IOT/getToken_DecryptSN/"
ROBOT_DETAILS_URL = f"{BASE_API}/serialnumbers/getrobotdetailsbymusn/"
ROBOT_DETAILS_BY_SN_URL = f"{BASE_API}/serialnumbers/getrobotdetailsbyrobotsn/"

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
API_RESPONSE_UNIT_SERIAL_NUMBER = "eSERNUM"

API_RESPONSE_DATA_TOKEN = "Token"
API_RESPONSE_DATA_ACCESS_KEY_ID = "AccessKeyId"
API_RESPONSE_DATA_SECRET_ACCESS_KEY = "SecretAccessKey"

API_DATA_MOTOR_UNIT_SERIAL = "motor_unit_serial"
API_DATA_SERIAL_NUMBER = "serial_number"
API_DATA_LOGIN_TOKEN = "login_token"

API_TOKEN_FIELDS = [
    API_RESPONSE_DATA_TOKEN,
    API_RESPONSE_DATA_ACCESS_KEY_ID,
    API_RESPONSE_DATA_SECRET_ACCESS_KEY,
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
    "appkey": "346BDE92-53D1-4829-8A2E-B496014B586C",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
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
DATA_ROBOT_FAMILY = "Robot Family"

DATA_ROBOT_DETAILS = {
    "SERNUM": "Motor Unit Serial",
    "PARTNAME": "Product Name",
    "PARTDES": "Product Description",
    "AppName": "Application Name",
    "RegDate": "Registration Date",
    "MyRobotName": DATA_ROBOT_NAME,
    "isReg": "Is Registered",
    "RobotFamily": DATA_ROBOT_FAMILY,
}

ATTR_ERROR_DESCRIPTIONS = "Description"
ATTR_LED_MODE = "led_mode"
ATTR_ATTRIBUTES = "attributes"
ATTR_ACTIONS = "actions"
ATTR_INSTRUCTIONS = "instructions"

LED_MODE_BLINKING = "1"
LED_MODE_ALWAYS_ON = "2"
LED_MODE_DISCO = "3"
LED_MODE_ICON_DEFAULT = "mdi:lighthouse-on"

ICON_LED_MODES = {
    LED_MODE_BLINKING: LED_MODE_ICON_DEFAULT,
    LED_MODE_ALWAYS_ON: "mdi:lightbulb-on",
    LED_MODE_DISCO: "mdi:lightbulb-multiple-outline",
}

CONF_DIRECTION = "direction"
CONF_DAY = "day"
CONF_TIME = "time"

JOYSTICK_SPEED = 1000

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
    JOYSTICK_LEFT,
]

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
    23: "mdi:clock-time-eleven",
}

PWS_STATE_ON = "on"
PWS_STATE_OFF = "off"
PWS_STATE_HOLD_DELAY = "holddelay"
PWS_STATE_HOLD_WEEKLY = "holdweekly"
PWS_STATE_PROGRAMMING = "programming"
PWS_STATE_ERROR = "error"
PWS_STATE_CLEANING = "cleaning"

ROBOT_STATE_FINISHED = "finished"
ROBOT_STATE_FAULT = "fault"
ROBOT_STATE_NOT_CONNECTED = "notConnected"
ROBOT_STATE_PROGRAMMING = "programming"
ROBOT_STATE_INIT = "init"
ROBOT_STATE_SCANNING = "scanning"

CONSIDERED_POWER_STATE = {
    PWS_STATE_OFF: False,
    PWS_STATE_ERROR: False,
    PWS_STATE_ON: True,
    PWS_STATE_CLEANING: True,
    PWS_STATE_PROGRAMMING: True,
    ROBOT_STATE_INIT: True,
}

FILTER_BAG_STATUS = {
    "unknown": (-1, -1),
    "empty": (0, 0),
    "partially_full": (1, 25),
    "getting_full": (26, 74),
    "almost_full": (75, 99),
    "full": (100, 100),
    "fault": (101, 101),
    "not_available": (102, 102),
}

FILTER_BAG_ICONS = {
    "unknown": "mdi:robot-off",
    "empty": "mdi:gauge-empty",
    "partially_full": "mdi:gauge-low",
    "getting_full": "mdi:gauge",
    "almost_full": "mdi:gauge",
    "full": "mdi:gauge-full",
    "fault": "mdi:robot-dead",
    "not_available": "mdi:robot-confused-outline",
}

VACUUM_FEATURES = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.FAN_SPEED
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.TURN_ON
    | VacuumEntityFeature.TURN_OFF
    | VacuumEntityFeature.LOCATE
)

STORAGE_DATA_KEY = "key"
STORAGE_DATA_LOCATING = "locating"
STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY = "aws-token-encrypted-key"

STORAGE_DATA_FILE_CONFIG = "config"

STORAGE_DATA_FILES = [STORAGE_DATA_FILE_CONFIG]

DATA_KEYS = [CONF_USERNAME, CONF_PASSWORD]

DATA_KEY_STATUS = "Status"
DATA_KEY_VACUUM = "Vacuum"
DATA_KEY_LED_MODE = "LED Mode"
DATA_KEY_LED_INTENSITY = "LED Intensity"
DATA_KEY_LED = "LED"
DATA_KEY_FILTER_STATUS = "Filter Status"
DATA_KEY_CYCLE_TIME = "Cycle Time"
DATA_KEY_CYCLE_TIME_LEFT = "Cycle Time Left"
DATA_KEY_AWS_BROKER = "AWS Broker"
DATA_KEY_WEEKLY_SCHEDULER = "Weekly Scheduler"
DATA_KEY_SCHEDULE = "Schedule"
DATA_KEY_RSSI = "RSSI"
DATA_KEY_NETWORK_NAME = "Network Name"
DATA_KEY_CLEAN_MODE = "Clean Mode"
DATA_KEY_POWER_SUPPLY_STATUS = "Power Supply Status"
DATA_KEY_ROBOT_STATUS = "Robot Status"
DATA_KEY_ROBOT_TYPE = "Robot Type"
DATA_KEY_BUSY = "Busy"
DATA_KEY_CYCLE_COUNT = "Cycle Count"
DATA_KEY_ROBOT_ERROR = "Robot Error"
DATA_KEY_PWS_ERROR = "Power Supply Error"

ACTION_ENTITY_RETURN_TO_BASE = "return_to_base"
ACTION_ENTITY_SET_FAN_SPEED = "set_fan_speed"
ACTION_ENTITY_START = "start"
ACTION_ENTITY_STOP = "stop"
ACTION_ENTITY_PAUSE = "stop"
ACTION_ENTITY_TURN_ON = "turn_on"
ACTION_ENTITY_TURN_OFF = "turn_off"
ACTION_ENTITY_TOGGLE = "toggle"
ACTION_ENTITY_SEND_COMMAND = "send_command"
ACTION_ENTITY_LOCATE = "locate"
ACTION_ENTITY_SELECT_OPTION = "select_option"
ACTION_ENTITY_SET_NATIVE_VALUE = "set_native_value"

TRANSLATION_KEY_ERROR_INSTRUCTIONS = "state_attributes.instructions.state"
ERROR_CLEAN_CODES = [0, 255]

EVENT_ERROR = f"{DOMAIN}_error"

TO_REDACT = [
    STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY,
    API_DATA_SERIAL_NUMBER,
    API_DATA_LOGIN_TOKEN,
    API_DATA_MOTOR_UNIT_SERIAL,
    API_RESPONSE_DATA_TOKEN,
    API_RESPONSE_DATA_ACCESS_KEY_ID,
    API_RESPONSE_DATA_SECRET_ACCESS_KEY,
    DYNAMIC_CONTENT_SERIAL_NUMBER,
    CONF_USERNAME,
    CONF_PASSWORD,
]
