from ...configuration.helpers.const import *

PLATFORMS = {domain: f"{DOMAIN}_{domain}_UPDATE_SIGNAL" for domain in SUPPORTED_PLATFORMS}

ENTITY_ID = "id"
ENTITY_NAME = "name"
ENTITY_STATE = "state"
ENTITY_ATTRIBUTES = "attributes"
ENTITY_ICON = "icon"
ENTITY_UNIQUE_ID = "unique-id"
ENTITY_BINARY_SENSOR_DEVICE_CLASS = "binary-sensor-device-class"
ENTITY_DEVICE_NAME = "device-name"
ENTITY_MONITOR_DETAILS = "monitor-details"
ENTITY_DISABLED = "disabled"
ENTITY_DOMAIN = "domain"
ENTITY_STATUS = "status"
ENTITY_CONFIG_ENTRY_ID = "entry_id"

STORAGE_VERSION = 1

PASSWORD_MANAGER = f"pm_{DOMAIN}"
DATA = f"data_{DOMAIN}"

DOMAIN_KEY_FILE = f"{DOMAIN}.key"
