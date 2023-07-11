"""Config flow to configure."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .common.connectivity_status import ConnectivityStatus
from .common.consts import DEFAULT_NAME, DOMAIN
from .managers.config_manager import ConfigManager
from .managers.rest_api import RestAPI

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class DomainFlowHandler(config_entries.ConfigFlow):
    """Handle a domain config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        super().__init__()

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        _LOGGER.debug(f"Starting async_step_user of {DEFAULT_NAME}")

        errors = None

        if user_input is not None:
            config_manager = ConfigManager(self.hass, None)
            config_manager.update_credentials(user_input)

            await config_manager.initialize()

            api = RestAPI(self.hass, config_manager)

            await api.validate()

            if api.status == ConnectivityStatus.TemporaryConnected:
                _LOGGER.debug("User inputs are valid")

                user_input[CONF_PASSWORD] = config_manager.password_hashed

                return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

            else:
                _LOGGER.warning("Failed to create integration")

        new_user_input = {
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        }

        schema = vol.Schema(new_user_input)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
