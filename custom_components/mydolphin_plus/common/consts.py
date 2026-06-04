from datetime import timedelta

from homeassistant.components.vacuum import VacuumEntityFeature
from homeassistant.const import CONF_USERNAME, Platform

MANUFACTURER = "Maytronics"
DEFAULT_NAME = "MyDolphin Plus"
DOMAIN = "mydolphin_plus"
LEGACY_KEY_FILE = f"{DOMAIN}.key"
CONFIGURATION_FILE = f"{DOMAIN}.config.json"

INVALID_TOKEN_SECTION = "https://github.com/sh00t2kill/dolphin-robot#invalid-token"

CONF_TITLE = "title"
CONF_OTP = "otp"

INITIAL_TOKENS_KEY = "__initial_tokens__"

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
    Platform.REMOTE,
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
ATTR_MANUAL_MODE = "Manual Mode"
ATTR_ACTIVITY = "Activity"
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
DATA_SECTION_ACTIVITY = "activity"

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
UPDATE_WS_INTERVAL = timedelta(seconds=30)
API_RECONNECT_INTERVAL = timedelta(minutes=1)
WS_RECONNECT_INTERVAL = timedelta(minutes=1)

# Reconnection backoff settings
RECONNECT_BACKOFF_BASE = timedelta(minutes=1)  # Initial retry interval
RECONNECT_BACKOFF_MAX = timedelta(minutes=15)  # Maximum backoff time
RECONNECT_MAX_ATTEMPTS_BEFORE_MAX = (
    4  # Attempts before reaching max (1, 2, 4, 8, 15 min pattern)
)

# AWS credential caching
AWS_CREDENTIALS_TTL = timedelta(
    hours=1, minutes=50
)  # AWS IoT credentials valid for 2h, use 1h50m for safety
AWS_CREDENTIALS_EXPIRY = "aws_credentials_expiry"

# Rate limiting for token fetches
MIN_TOKEN_FETCH_INTERVAL = timedelta(minutes=5)  # Minimum time between token API calls
STORAGE_DATA_LAST_TOKEN_FETCH = "last-token-fetch"
STORAGE_DATA_LAST_AWS_CREDENTIALS_FETCH = "last-aws-credentials-fetch"

WS_LAST_UPDATE = "last-update"

COGNITO_CLIENT_ID = "4ed12eq01o6n0tl5f0sqmkq2na"
COGNITO_ENDPOINT = "https://cognito-idp.us-west-2.amazonaws.com/"
COGNITO_TARGET_PREFIX = "AWSCognitoIdentityProviderService."
COGNITO_HEADER_TARGET = "X-Amz-Target"
COGNITO_CONTENT_TYPE = "application/x-amz-json-1.1"
COGNITO_AUTH_FLOW_CUSTOM = "CUSTOM_AUTH"
COGNITO_AUTH_FLOW_REFRESH = "REFRESH_TOKEN_AUTH"
COGNITO_CHALLENGE_NAME = "CUSTOM_CHALLENGE"

APPS_BASE = "https://apps.maytronics.com"
AUTHENTICATE_USER_URL = f"{APPS_BASE}/mobapi/user/authenticate-user/"
AWS_STS_TOKEN_URL = f"{APPS_BASE}/mt-sso/aws/getToken/"

APP_KEY = "346BDE92-53D1-4829-8A2E-B496014B586C"
APP_VERSION = "ios_3.1.7_2"

BEARER_HEADERS_BASE = {
    "AppKey": APP_KEY,
    "app_version": APP_VERSION,
    "Accept": "*/*",
}

# Refresh the IdToken if it expires within this many seconds
ID_TOKEN_REFRESH_WINDOW_SECONDS = 300

API_REQUEST_SERIAL_EMAIL = "Email"
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

MQTT_MESSAGE_ENCODING = "utf-8"

AWS_REGION = "eu-west-1"
AWS_BASE_HOST = f"{AWS_REGION}.amazonaws.com"

AWS_IOT_URL = f"a12rqfdx55bdbv-ats.iot.{AWS_BASE_HOST}"
AWS_IOT_PORT = 443

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

CONF_DAY = "day"
CONF_TIME = "time"

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
    | VacuumEntityFeature.START
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.LOCATE
)

STORAGE_DATA_KEY = "key"
STORAGE_DATA_LOCATING = "locating"
STORAGE_DATA_ID_TOKEN = "id-token"
STORAGE_DATA_REFRESH_TOKEN = "refresh-token"
STORAGE_DATA_ID_TOKEN_EXPIRES_AT = "id-token-expires-at"
STORAGE_DATA_SERIAL_NUMBER = "serial-number"
STORAGE_DATA_MOTOR_UNIT_SERIAL = "motor-unit-serial"

DATA_KEY_STATUS = "Status"
DATA_KEY_VACUUM = "Vacuum"
DATA_KEY_REMOTE = "Remote"
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
DATA_KEY_BATTERY = "Battery"

TRANSLATION_KEY_ERROR_INSTRUCTIONS = "state_attributes.instructions.state"
ERROR_CLEAN_CODES = [0, 255]

EVENT_ERROR = f"{DOMAIN}_error"

TOKEN_PARAMS = [
    STORAGE_DATA_ID_TOKEN,
    STORAGE_DATA_REFRESH_TOKEN,
    STORAGE_DATA_ID_TOKEN_EXPIRES_AT,
    STORAGE_DATA_LAST_AWS_CREDENTIALS_FETCH,
    STORAGE_DATA_SERIAL_NUMBER,
    STORAGE_DATA_MOTOR_UNIT_SERIAL,
    STORAGE_DATA_LAST_TOKEN_FETCH,
    AWS_CREDENTIALS_EXPIRY,
]

TO_REDACT = [
    API_RESPONSE_DATA_TOKEN,
    API_RESPONSE_DATA_ACCESS_KEY_ID,
    API_RESPONSE_DATA_SECRET_ACCESS_KEY,
    DYNAMIC_CONTENT_SERIAL_NUMBER,
    CONF_USERNAME,
]

TO_REDACT.extend(TOKEN_PARAMS)
