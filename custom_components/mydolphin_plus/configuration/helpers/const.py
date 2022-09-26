"""
Following constants are mandatory for CORE:
    DEFAULT_NAME - Full name for the title of the integration
    DOMAIN - name of component, will be used as component's domain
    SUPPORTED_PLATFORMS - list of supported HA components to initialize
"""
from homeassistant.components.binary_sensor import DOMAIN as DOMAIN_BINARY_SENSOR
from homeassistant.components.remote import DOMAIN as DOMAIN_REMOTE
from homeassistant.components.select import DOMAIN as DOMAIN_SELECT
from homeassistant.components.sensor import DOMAIN as DOMAIN_SENSOR
from homeassistant.components.switch import DOMAIN as DOMAIN_SWITCH
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, STATE_OFF, STATE_ON

DEFAULT_NAME = "MyDolphin Plus"
DOMAIN = "mydolphin_plus"
SUPPORTED_PLATFORMS = [
    DOMAIN_BINARY_SENSOR,
    DOMAIN_REMOTE,
    DOMAIN_SELECT,
    DOMAIN_SENSOR,
    DOMAIN_SWITCH
]

DEFAULT_PORT = 8080

CONFIGURATION_MANAGER = f"cm_{DOMAIN}"

DATA_KEYS = [
    CONF_USERNAME,
    CONF_PASSWORD
]
