import calendar

import voluptuous as vol

from homeassistant.const import CONF_ENABLED, CONF_MODE
import homeassistant.helpers.config_validation as cv

from .clean_modes import CleanModes
from .consts import CONF_DAY, CONF_DIRECTION, CONF_TIME, JOYSTICK_DIRECTIONS

SERVICE_EXIT_NAVIGATION = "exit_navigation"
SERVICE_NAVIGATE = "navigate"
SERVICE_DAILY_SCHEDULE = "daily_schedule"
SERVICE_DELAYED_CLEAN = "delayed_clean"

SERVICE_SCHEMA_NAVIGATE = vol.Schema(
    {vol.Required(CONF_DIRECTION): vol.In(JOYSTICK_DIRECTIONS)}
)

SERVICE_SCHEMA_DAILY_SCHEDULE = vol.Schema(
    {
        vol.Optional(CONF_ENABLED, default=False): cv.boolean,
        vol.Required(CONF_DAY): vol.In(list(calendar.day_name)),
        vol.Optional(CONF_MODE, default=CleanModes.REGULAR): vol.In(list(CleanModes)),
        vol.Optional(CONF_TIME, default=None): cv.string,
    }
)

SERVICE_SCHEMA_DELAYED_CLEAN = vol.Schema(
    {
        vol.Optional(CONF_ENABLED, default=False): cv.boolean,
        vol.Optional(CONF_MODE, default=CleanModes.REGULAR): vol.In(list(CleanModes)),
        vol.Optional(CONF_TIME, default=None): cv.string,
    }
)

SERVICE_VALIDATION = {
    SERVICE_NAVIGATE: SERVICE_SCHEMA_NAVIGATE,
    SERVICE_DAILY_SCHEDULE: SERVICE_SCHEMA_DAILY_SCHEDULE,
    SERVICE_DELAYED_CLEAN: SERVICE_SCHEMA_DELAYED_CLEAN,
}
