"""
Support for MyDolphin Plus.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.mydolphin_plus/
"""
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.light import PLATFORM_SCHEMA
from homeassistant.const import CONF_DEVICE, CONF_ENABLED, CONF_MODE
import homeassistant.helpers.config_validation as cv

from ...core.helpers.const import *

CONF_SUPPORT_STREAM = "support_stream"

VERSION = "0.0.3"

DEFAULT_ICON = "mdi:alarm-light"
ATTR_FRIENDLY_NAME = "friendly_name"

SCAN_INTERVAL = timedelta(seconds=60)
HEARTBEAT_INTERVAL_SECONDS = timedelta(seconds=25)
TRIGGER_INTERVAL = timedelta(seconds=1)

DEFAULT_FORCE_UPDATE = False

MAX_MSG_SIZE = 0
DISCONNECT_INTERVAL = 5
RECONNECT_INTERVAL = 30

DISCOVERY = f"{DOMAIN}_discovery"

PROTOCOLS = {True: "https", False: "http"}
WS_PROTOCOLS = {True: "wss", False: "ws"}

BASE_API = "https://mbapp18.maytronics.com/api"
LOGIN_URL = f"{BASE_API}/users/Login/"
TOKEN_URL = f"{BASE_API}/IOT/getToken/"
ROBOT_DETAILS_URL = f"{BASE_API}/serialnumbers/getrobotdetailsbymusn/"

AWS_REGION = "eu-west-1"
AWS_BASE_HOST = f"{AWS_REGION}.amazonaws.com"
DYNAMODB_HOST = f'dynamodb.{AWS_BASE_HOST}'
DYNAMODB_URL = f"https://{DYNAMODB_HOST}/"

IOT_URL = f"a12rqfdx55bdbv-ats.iot.{AWS_BASE_HOST}"

LOGIN_HEADERS = {
    'appkey': '346BDE92-53D1-4829-8A2E-B496014B586C',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
}
CA_FILE_NAME = "AmazonRootCA.pem"
LOCAL_STATE_TOPIC = 'robot/state'

AWS_HEADER_CONTENT_TYPE = "content-type"
AWS_HEADER_HOST = "host"
AWS_HEADER_DATE = "x-amz-date"
AWS_HEADER_TARGET = "x-amz-target"

AWS_CONTENT_TYPE = "application/x-amz-json-1.0"
AMZ_TARGET = "DynamoDB_20120810.Query"
AWS_METHOD = "POST\n/\n"
AWS_ALGORITHM = "AWS4-HMAC-SHA256"
AWS_REQUEST_KEY = "aws4_request"

AWS_DATE_FORMAT = "%Y%m%d"
AWS_DATE_TIME_FORMAT = f"{AWS_DATE_FORMAT}T%H%M%SZ"

AWS_DYNAMODB_QUERY_PARAMETER = "[SERIAL]"
AWS_DYNAMODB_QUERY_PAYLOAD = '{' \
                             '\"TableName\":\"maytronics_iot_history\",' \
                             '\"Limit\":1,' \
                             '\"KeyConditionExpression\":\"musn = :val \",' \
                             '\"ScanIndexForward\":false,' \
                             '\"ExpressionAttributeValues\":' \
                             '{\":val\":' \
                             '{\"S\":\"' + AWS_DYNAMODB_QUERY_PARAMETER + '"\'}}}'

AWS_DYNAMODB_SERVICE = "dynamodb"

TOPIC_GET = "$aws/things/{}/shadow/get/#"
TOPIC_UPDATE = "$aws/things/{}/shadow/update/#"
TOPIC_DYNAMIC = "Maytronics/{}/main"
TOPICS = [TOPIC_DYNAMIC, TOPIC_UPDATE, TOPIC_GET]

DATA_ROBOT_DETAILS = {
    "SERNUM": "Serial Number",
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
CLEANING_MODE_ICON_DEFAULT = "mdi:border-all-variant"

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

CLEANING_MODES = {
  "all": "Regular - Cleans floor, water and waterline (2h)",
  "short": "Fast mode - Cleans the floor (1h)",
  "floor": "Floor only - Cleans the floor only (2h)",
  "water": "Water line - Cleans the walls and water line (2h)",
  "ultra": "Ultra clean - Deeply cleans the floor, walls and waterline (2h)"
}

SERVICE_NAVIGATE = "navigate"
SERVICE_PICKUP = "pickup"
SERVICE_SET_DAILY_SCHEDULE = "set_daily_schedule"
SERVICE_DELAYED_CLEAN = "delayed_clean"

CONF_DIRECTION = "direction"
CONF_DAY = "day"
CONF_TIME = "time"

SERVICE_SCHEMA_NAVIGATE = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Required(CONF_DIRECTION): vol.In(["forward", "backward", "left", "right"])
    }
)

SERVICE_SCHEMA_PICKUP = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): cv.string
    }
)

SERVICE_SCHEMA_DAILY_SCHEDULE = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Required(CONF_ENABLED): cv.boolean,
        vol.Required(CONF_DAY): vol.In(["forward", "backward", "left", "right"]),
        vol.Required(CONF_MODE): vol.In(CLEANING_MODES.keys()),
        vol.Required(CONF_TIME): cv.string
    }
)

SERVICE_SCHEMA_DELAYED_CLEAN = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Required(CONF_ENABLED): cv.boolean,
        vol.Required(CONF_MODE): vol.In(CLEANING_MODES.keys()),
        vol.Required(CONF_TIME): cv.string
    }
)

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
