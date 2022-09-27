from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry

from ...configuration.helpers.const import *


class ConfigData:
    username: str | None
    password: str | None
    entry: ConfigEntry | None

    def __init__(self):
        self.username = None
        self.password = None
        self.entry = None

    @staticmethod
    def from_dict(data: dict[str, Any] = None) -> ConfigData:
        result = ConfigData()

        if data is not None:
            result.username = data.get(CONF_USERNAME)
            result.password = data.get(CONF_PASSWORD)

        return result

    def to_dict(self):
        obj = {
            CONF_USERNAME: self.username,
            CONF_PASSWORD: self.password
        }

        return obj

    def __repr__(self):
        to_string = f"{self.to_dict()}"

        return to_string
