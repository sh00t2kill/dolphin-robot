from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ...component.api.mydolphin_plus_api import MyDolphinPlusAPI
from ...component.helpers.enums import ConnectivityStatus
from ...configuration.helpers.exceptions import LoginError
from ...configuration.models.config_data import ConfigData
from ...core.helpers.const import *
from ...core.managers.password_manager import PasswordManager

_LOGGER = logging.getLogger(__name__)


def async_get_configuration_manager(hass: HomeAssistant) -> ConfigurationManager:
    data = None

    if hass is not None and hass.data is not None:
        data = hass.data.get(DATA)

    if data is None or CONFIGURATION_MANAGER not in data:
        configuration_manager = ConfigurationManager(hass)

        if data is not None:
            hass.data[DATA][CONFIGURATION_MANAGER] = configuration_manager

    else:
        configuration_manager: ConfigurationManager = hass.data[DATA][CONFIGURATION_MANAGER]

    return configuration_manager


class ConfigurationManager:
    password_manager: PasswordManager
    config: dict[str, ConfigData]

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.config = {}
        self.password_manager = PasswordManager(hass)

    async def initialize(self):
        await self.password_manager.initialize()

    def get(self, entry_id: str):
        config = self.config.get(entry_id)

        return config

    async def load(self, entry: ConfigEntry):
        await self.initialize()

        config = {k: entry.data[k] for k in entry.data}

        if CONF_PASSWORD in config:
            encrypted_password = config[CONF_PASSWORD]

            config[CONF_PASSWORD] = self.password_manager.get(encrypted_password)

        config_data = ConfigData.from_dict(config)

        if config_data is not None:
            config_data.entry = entry

            self.config[entry.entry_id] = config_data

    async def validate(self, data: dict[str, Any]):
        _LOGGER.debug("Validate login")

        config_data = ConfigData.from_dict(data)

        api = MyDolphinPlusAPI(self.hass, config_data)
        await api.initialize()

        errors = ConnectivityStatus.get_config_errors(api.status)

        if errors is None:
            password = data[CONF_PASSWORD]

            data[CONF_PASSWORD] = self.password_manager.set(password)

        else:
            raise LoginError(errors)

    @staticmethod
    def get_data_fields(user_input: dict[str, Any] | None) -> dict[vol.Marker, Any]:
        if user_input is None:
            user_input = ConfigData.from_dict().to_dict()

        fields = {
            vol.Optional(CONF_USERNAME, default=user_input.get(CONF_USERNAME)): str,
            vol.Optional(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD)): str
        }

        return fields

    def get_options_fields(self, user_input: dict[str, Any] | None) -> dict[vol.Marker, Any]:
        if user_input is None:
            data = ConfigData.from_dict().to_dict()

        else:
            data = {k: user_input[k] for k in user_input}
            encrypted_password = data.get(CONF_PASSWORD)

            data[CONF_PASSWORD] = self.password_manager.get(encrypted_password)

        fields = {
            vol.Optional(CONF_USERNAME, default=data.get(CONF_USERNAME)): str,
            vol.Optional(CONF_PASSWORD, default=data.get(CONF_PASSWORD)): str
        }

        return fields

    def remap_entry_data(self, entry: ConfigEntry, options: dict[str, Any]) -> dict[str, Any]:
        config_options = {}
        config_data = {}

        for key in options:
            if key in DATA_KEYS:
                config_data[key] = options.get(key, entry.data.get(key))

            else:
                config_options[key] = options.get(key)

        config_entries = self.hass.config_entries
        config_entries.async_update_entry(entry, data=config_data)

        return config_options
