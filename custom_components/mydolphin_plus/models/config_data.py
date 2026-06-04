import voluptuous as vol
from voluptuous import Schema

from homeassistant.const import CONF_USERNAME

from ..common.consts import CONF_OTP, CONF_TITLE, DEFAULT_NAME

DATA_KEYS = [CONF_USERNAME]


class ConfigData:
    _username: str | None

    def __init__(self):
        self._username = None

    @property
    def username(self) -> str:
        return self._username

    def update(self, data: dict):
        self._username = data.get(CONF_USERNAME)

    def to_dict(self):
        return {CONF_USERNAME: self.username}

    def __repr__(self):
        return f"{self.to_dict()}"

    @staticmethod
    def default_schema(user_input: dict | None) -> Schema:
        if user_input is None:
            user_input = {}

        return vol.Schema(
            {
                vol.Required(
                    CONF_TITLE, default=user_input.get(CONF_TITLE, DEFAULT_NAME)
                ): str,
                vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME)): str,
            }
        )

    @staticmethod
    def otp_schema() -> Schema:
        return vol.Schema({vol.Required(CONF_OTP): str})
