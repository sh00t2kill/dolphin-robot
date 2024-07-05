"""Config flow to configure."""
from __future__ import annotations

from copy import copy
import logging
from typing import Any

from cryptography.fernet import InvalidToken

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowHandler

from ..common.connectivity_status import ConnectivityStatus
from ..common.consts import CONF_RESET_PASSWORD, CONF_TITLE, DEFAULT_NAME
from ..models.config_data import DATA_KEYS, ConfigData
from ..models.exceptions import LoginError
from .config_manager import ConfigManager
from .password_manager import PasswordManager
from .rest_api import RestAPI

_LOGGER = logging.getLogger(__name__)


class IntegrationFlowManager:
    _hass: HomeAssistant
    _entry: ConfigEntry | None

    _flow_handler: FlowHandler
    _flow_id: str

    _config_manager: ConfigManager

    def __init__(
        self,
        hass: HomeAssistant,
        flow_handler: FlowHandler,
        entry: ConfigEntry | None = None,
    ):
        self._hass = hass
        self._flow_handler = flow_handler
        self._entry = entry
        self._flow_id = "user" if entry is None else "init"
        self._config_manager = ConfigManager(self._hass, None)

    async def async_step(self, user_input: dict | None = None):
        """Manage the domain options."""
        _LOGGER.info(f"Config flow started, Step: {self._flow_id}")

        form_errors = None

        if user_input is None:
            if self._entry is None:
                user_input = {}

            else:
                user_input = {key: self._entry.data[key] for key in self._entry.data}
                user_input[CONF_TITLE] = self._entry.title

                await PasswordManager.decrypt(
                    self._hass, user_input, self._entry.entry_id
                )

        else:
            error_key: str | None = None

            try:
                await self._config_manager.initialize(user_input)

                api = RestAPI(self._hass, self._config_manager)

                reset_password_flow = user_input.get(CONF_RESET_PASSWORD, False)

                if reset_password_flow:
                    await api.reset_password()
                    user_input = {}

                else:
                    await api.validate()

                    if api.status == ConnectivityStatus.TEMPORARY_CONNECTED:
                        _LOGGER.debug("User inputs are valid")

                        if self._entry is None:
                            data = copy(user_input)

                        else:
                            data = await self.remap_entry_data(user_input)

                        await PasswordManager.encrypt(self._hass, data)

                        title = data.get(CONF_TITLE, DEFAULT_NAME)

                        new_user_data = {
                            key: data[key] for key in data if key in DATA_KEYS
                        }

                        return self._flow_handler.async_create_entry(
                            title=title, data=new_user_data
                        )

                    else:
                        error_key = ConnectivityStatus.get_ha_error(api.status)

            except LoginError:
                error_key = "invalid_credentials"

            except InvalidToken:
                error_key = "corrupted_encryption_key"

            if error_key is not None:
                form_errors = {"base": error_key}

                _LOGGER.warning(f"Failed to create integration, Error Key: {error_key}")

        schema = ConfigData.default_schema(user_input)

        return self._flow_handler.async_show_form(
            step_id=self._flow_id, data_schema=schema, errors=form_errors
        )

    async def remap_entry_data(self, options: dict[str, Any]) -> dict[str, Any]:
        entry = self._entry
        entry_data = entry.data

        title = options.get(CONF_TITLE, DEFAULT_NAME)

        config_data = {
            key: options.get(key, entry_data.get(key))
            for key in options
            if key in DATA_KEYS
        }

        options_excluded_keys = [CONF_TITLE, CONF_RESET_PASSWORD]
        options_excluded_keys.extend(DATA_KEYS)

        config_options = {
            key: options[key] for key in options if key not in options_excluded_keys
        }

        await PasswordManager.encrypt(self._hass, config_data)

        self._hass.config_entries.async_update_entry(
            entry, data=config_data, title=title
        )

        return config_options
