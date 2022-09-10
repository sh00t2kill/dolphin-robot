"""
Following constants are mandatory for CORE:
    DEFAULT_NAME - Full name for the title of the integration
    DOMAIN - name of component, will be used as component's domain
    SUPPORTED_PLATFORMS - list of supported HA components to initialize
"""

from homeassistant.components.binary_sensor import DOMAIN as DOMAIN_BINARY_SENSOR
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, STATE_OFF, STATE_ON

DEFAULT_NAME = "MyDolphin Plus"
DOMAIN = "mydolphin_plus"
SUPPORTED_PLATFORMS = [
    DOMAIN_BINARY_SENSOR
]


DEFAULT_PORT = 8080

CONFIGURATION_MANAGER = f"cm_{DOMAIN}"


DATA_KEYS = [
    CONF_USERNAME,
    CONF_PASSWORD
]
