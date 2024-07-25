from datetime import timedelta

from homeassistant.components.vacuum import VacuumEntityFeature
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform

MANUFACTURER = "Maytronics"
DEFAULT_NAME = "MyDolphin Plus"
DOMAIN = "mydolphin_plus"
LEGACY_KEY_FILE = f"{DOMAIN}.key"
CONFIGURATION_FILE = f"{DOMAIN}.config.json"

INVALID_TOKEN_SECTION = "https://github.com/sh00t2kill/dolphin-robot#invalid-token"

CONF_TITLE = "title"
CONF_RESET_PASSWORD = "reset_password"

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

ATTR_IS_ON = "is_on"
ATTR_START_TIME = "start_time"
ATTR_STATUS = "status"
ATTR_RESET_FBI = "reset_fbi"
ATTR_EXPECTED_END_TIME = "expected_end_time"

ATTR_CALCULATED_STATUS = "Calculated State"
ATTR_VACUUM_STATE = "Vacuum State"
ATTR_POWER_SUPPLY_STATE = "Power Supply State"
ATTR_ROBOT_STATE = "Robot State"
ATTR_ROBOT_TYPE = "Robot Type"
ATTR_IS_BUSY = "Busy"
ATTR_TURN_ON_COUNT = "Turn On Count"
ATTR_TIME_ZONE = "Time Zone"

DYNAMIC_TYPE = "type"
DYNAMIC_DESCRIPTION = "description"
DYNAMIC_DESCRIPTION_JOYSTICK = "joystick"
DYNAMIC_DESCRIPTION_TEMPERATURE = "temperature"
DYNAMIC_TYPE_PWS_REQUEST = "pwsRequest"
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

DATA_SCHEDULE_IS_ENABLED = "isEnabled"
DATA_SCHEDULE_CLEANING_MODE = "cleaningMode"
DATA_SCHEDULE_TIME = "time"
DATA_SCHEDULE_TIME_HOURS = "hours"
DATA_SCHEDULE_TIME_MINUTES = "minutes"

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

UPDATE_API_INTERVAL = timedelta(hours=1)
UPDATE_WS_INTERVAL = timedelta(minutes=5)
UPDATE_ENTITIES_INTERVAL = timedelta(seconds=5)
API_RECONNECT_INTERVAL = timedelta(minutes=1)
WS_RECONNECT_INTERVAL = timedelta(minutes=1)

WS_LAST_UPDATE = "last-update"

BASE_API = "https://mbapp18.maytronics.com/api"
LOGIN_URL = f"{BASE_API}/users/Login/"
EMAIL_VALIDATION_URL = f"{BASE_API}/users/isEmailExists/"
FORGOT_PASSWORD_URL = f"{BASE_API}/users/ForgotPassword/"
TOKEN_URL = f"{BASE_API}/IOT/getToken_DecryptSN/"
ROBOT_DETAILS_URL = f"{BASE_API}/serialnumbers/getrobotdetailsbymusn/"
ROBOT_DETAILS_BY_SN_URL = f"{BASE_API}/serialnumbers/getrobotdetailsbyrobotsn/"

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

API_RESPONSE_IS_EMAIL_EXISTS = "isEmailExists"

API_RESPONSE_DATA_TOKEN = "Token"
API_RESPONSE_DATA_ACCESS_KEY_ID = "AccessKeyId"
API_RESPONSE_DATA_SECRET_ACCESS_KEY = "SecretAccessKey"

API_TOKEN_FIELDS = [
    API_RESPONSE_DATA_TOKEN,
    API_RESPONSE_DATA_ACCESS_KEY_ID,
    API_RESPONSE_DATA_SECRET_ACCESS_KEY,
]

BLOCK_SIZE = 16

MQTT_MESSAGE_ENCODING = "utf-8"

AWS_REGION = "eu-west-1"
AWS_BASE_HOST = f"{AWS_REGION}.amazonaws.com"

AWS_IOT_URL = f"a12rqfdx55bdbv-ats.iot.{AWS_BASE_HOST}"
AWS_IOT_PORT = 443

LOGIN_HEADERS = {
    "appkey": "346BDE92-53D1-4829-8A2E-B496014B586C",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "integration-version": "1.0.19",
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

CLOCK_HOURS_NONE = "mdi:timer-sand-paused"
CLOCK_HOURS_ICON = "mdi:clock-time-"
CLOCK_HOURS_TEXT = [
    "twelve",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
]

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
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.LOCATE
)

STORAGE_DATA_KEY = "key"
STORAGE_DATA_LOCATING = "locating"
STORAGE_DATA_AWS_TOKEN = "aws-token"
STORAGE_DATA_API_TOKEN = "api-token"
STORAGE_DATA_SERIAL_NUMBER = "serial-number"
STORAGE_DATA_MOTOR_UNIT_SERIAL = "motor-unit-serial"

DATA_KEY_STATUS = "Status"
DATA_KEY_VACUUM = "Vacuum"
DATA_KEY_LED_MODE = "LED Mode"
DATA_KEY_LED_INTENSITY = "LED Intensity"
DATA_KEY_LED = "LED"
DATA_KEY_FILTER_STATUS = "Filter Status"
DATA_KEY_CYCLE_TIME = "Cycle Time"
DATA_KEY_CYCLE_TIME_LEFT = "Cycle Time Left"
DATA_KEY_AWS_BROKER = "AWS Broker"
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

TRANSLATION_KEY_ERROR_INSTRUCTIONS = "state_attributes.instructions.state"
ERROR_CLEAN_CODES = [0, 255]

EVENT_ERROR = f"{DOMAIN}_error"

TOKEN_PARAMS = [
    STORAGE_DATA_AWS_TOKEN,
    STORAGE_DATA_API_TOKEN,
    STORAGE_DATA_SERIAL_NUMBER,
    STORAGE_DATA_MOTOR_UNIT_SERIAL,
]

TO_REDACT = [
    API_RESPONSE_DATA_TOKEN,
    API_RESPONSE_DATA_ACCESS_KEY_ID,
    API_RESPONSE_DATA_SECRET_ACCESS_KEY,
    DYNAMIC_CONTENT_SERIAL_NUMBER,
    CONF_USERNAME,
    CONF_PASSWORD,
]

TO_REDACT.extend(TOKEN_PARAMS)
