"""
Following constants are mandatory for CORE:
    DEFAULT_NAME - Full name for the title of the integration
    DOMAIN - name of component, will be used as component's domain
    SUPPORTED_PLATFORMS - list of supported HA components to initialize
"""
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, STATE_OFF, STATE_ON

MANUFACTURER = "Maytronics"
DEFAULT_NAME = "MyDolphin Plus"
DOMAIN = "mydolphin_plus"

MAIN_VIEW = f"main_view_{DOMAIN}"

DATA_KEYS = [
    CONF_USERNAME,
    CONF_PASSWORD
]
