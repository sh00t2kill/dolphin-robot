import voluptuous as vol
from voluptuous import Schema

from homeassistant.const import CONF_USERNAME
from homeassistant.helpers import selector

from ..common.consts import (
    APP_SELECT_OPTIONS,
    CONF_APP_ID,
    CONF_OTP,
    CONF_TITLE,
    DEFAULT_APP_ID,
    DEFAULT_NAME,
    resolve_app_id,
)

DATA_KEYS = [CONF_USERNAME, CONF_APP_ID]


class ConfigData:
    _username: str | None
    _app_id: str | None

    def __init__(self):
        self._username = None
        self._app_id = DEFAULT_APP_ID

    @property
    def username(self) -> str:
        return self._username

    @property
    def app_id(self) -> str:
        return resolve_app_id(self._app_id)

    def update(self, data: dict):
        self._username = data.get(CONF_USERNAME)
        self._app_id = resolve_app_id(data.get(CONF_APP_ID))

    def to_dict(self):
        return {CONF_USERNAME: self.username, CONF_APP_ID: self.app_id}

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
                vol.Required(
                    CONF_APP_ID,
                    default=resolve_app_id(user_input.get(CONF_APP_ID)),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=APP_SELECT_OPTIONS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME)): str,
            }
        )

    @staticmethod
    def otp_schema() -> Schema:
        return vol.Schema({vol.Required(CONF_OTP): str})
