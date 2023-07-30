import voluptuous as vol
from voluptuous import Schema

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from ..common.consts import CONF_TITLE, DEFAULT_NAME

DATA_KEYS = [CONF_USERNAME, CONF_PASSWORD]


class ConfigData:
    _username: str | None
    _password: str | None

    def __init__(self):
        self._username = None
        self._password = None

    @property
    def username(self) -> str:
        username = self._username

        return username

    @property
    def password(self) -> str:
        password = self._password

        return password

    def update(self, data: dict):
        self._password = data.get(CONF_PASSWORD)
        self._username = data.get(CONF_USERNAME)

    def to_dict(self):
        obj = {
            CONF_USERNAME: self.username,
        }

        return obj

    def __repr__(self):
        to_string = f"{self.to_dict()}"

        return to_string

    @staticmethod
    def default_schema(user_input: dict | None) -> Schema:
        if user_input is None:
            user_input = {}

        new_user_input = {
            vol.Required(
                CONF_TITLE, default=user_input.get(CONF_TITLE, DEFAULT_NAME)
            ): str,
            vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME)): str,
            vol.Required(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD)): str,
        }

        schema = vol.Schema(new_user_input)

        return schema
