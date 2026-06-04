"""Config flow to configure."""

from __future__ import annotations

import logging
import time

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowHandler
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..common.consts import (
    CONF_OTP,
    CONF_TITLE,
    DEFAULT_NAME,
    INITIAL_TOKENS_KEY,
    STORAGE_DATA_ID_TOKEN,
    STORAGE_DATA_ID_TOKEN_EXPIRES_AT,
    STORAGE_DATA_MOTOR_UNIT_SERIAL,
    STORAGE_DATA_REFRESH_TOKEN,
    STORAGE_DATA_SERIAL_NUMBER,
)
from ..common.integration_info import IntegrationInfo
from ..models.config_data import ConfigData
from ..models.exceptions import LoginError
from .rest_api import cognito_initiate_auth, cognito_respond_otp, fetch_user_profile

_LOGGER = logging.getLogger(__name__)

_FLOW_STATE_ATTR = "_mydolphin_state"


class IntegrationFlowManager:
    _hass: HomeAssistant
    _entry: ConfigEntry | None

    _flow_handler: FlowHandler
    _flow_id: str
    _integration_info: IntegrationInfo

    def __init__(
        self,
        hass: HomeAssistant,
        flow_handler: FlowHandler,
        entry: ConfigEntry | None = None,
        source: str | None = None,
    ):
        self._hass = hass
        self._flow_handler = flow_handler
        self._entry = entry
        self._source = (
            source if source is not None else getattr(flow_handler, "source", None)
        )
        self._is_reauth = self._source == SOURCE_REAUTH
        self._flow_id = "user" if entry is None or self._is_reauth else "init"
        self._integration_info = IntegrationInfo()

    async def async_step(self, user_input: dict | None = None):
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input: dict | None = None):
        _LOGGER.info(f"Config flow user step, has_input={user_input is not None}")

        if user_input is None:
            defaults = (
                {
                    CONF_TITLE: self._entry.title,
                    CONF_USERNAME: self._entry.data.get(CONF_USERNAME),
                }
                if self._entry is not None
                else {}
            )
            return self._show_user_form(defaults)

        email = (user_input.get(CONF_USERNAME) or "").strip().lower()
        title = user_input.get(CONF_TITLE, DEFAULT_NAME)

        if not email:
            return self._show_user_form(user_input, errors={"base": "invalid_account"})

        session = async_get_clientsession(self._hass)
        await self._integration_info.initialize(self._hass)
        try:
            init = await cognito_initiate_auth(
                session,
                email,
                integration_info=self._integration_info,
            )
        except LoginError as ex:
            _LOGGER.warning(f"Cognito InitiateAuth failed: {ex}")
            return self._show_user_form(user_input, errors={"base": "otp_send_failed"})

        setattr(
            self._flow_handler,
            _FLOW_STATE_ATTR,
            {
                "title": title,
                "email": email,
                "cognito_session": init["Session"],
            },
        )

        return self._show_otp_form()

    async def async_step_otp(self, user_input: dict | None = None):
        state = getattr(self._flow_handler, _FLOW_STATE_ATTR, None)
        if state is None:
            return await self.async_step_user(None)

        if user_input is None:
            return self._show_otp_form()

        code = (user_input.get(CONF_OTP) or "").strip()
        if not code:
            return self._show_otp_form(errors={"base": "invalid_otp"})

        session = async_get_clientsession(self._hass)
        await self._integration_info.initialize(self._hass)
        try:
            auth = await cognito_respond_otp(
                session,
                state["email"],
                state["cognito_session"],
                code,
                integration_info=self._integration_info,
            )
            profile = await fetch_user_profile(
                session,
                auth["IdToken"],
                integration_info=self._integration_info,
            )
        except LoginError as ex:
            _LOGGER.warning(f"OTP exchange failed: {ex}")
            return self._show_otp_form(errors={"base": "invalid_otp"})

        expires_at = time.time() + int(auth.get("ExpiresIn", 3600))
        initial_tokens = {
            STORAGE_DATA_ID_TOKEN: auth["IdToken"],
            STORAGE_DATA_REFRESH_TOKEN: auth.get("RefreshToken"),
            STORAGE_DATA_ID_TOKEN_EXPIRES_AT: expires_at,
            STORAGE_DATA_SERIAL_NUMBER: profile.get("Sernum"),
            STORAGE_DATA_MOTOR_UNIT_SERIAL: profile.get("eSERNUM"),
        }

        try:
            delattr(self._flow_handler, _FLOW_STATE_ATTR)
        except AttributeError:
            pass

        if self._is_reauth:
            return self._flow_handler.async_update_reload_and_abort(
                self._flow_handler._get_reauth_entry(),
                data_updates={
                    CONF_USERNAME: state["email"],
                    INITIAL_TOKENS_KEY: initial_tokens,
                },
            )

        if self._entry is not None:
            self._hass.config_entries.async_update_entry(
                self._entry,
                title=state["title"],
                data={
                    CONF_USERNAME: state["email"],
                    INITIAL_TOKENS_KEY: initial_tokens,
                },
            )
            self._hass.config_entries.async_schedule_reload(self._entry.entry_id)
            return self._flow_handler.async_create_entry(title="", data={})

        return self._flow_handler.async_create_entry(
            title=state["title"],
            data={
                CONF_USERNAME: state["email"],
                INITIAL_TOKENS_KEY: initial_tokens,
            },
        )

    def _show_user_form(self, user_input: dict | None = None, errors=None):
        return self._flow_handler.async_show_form(
            step_id=self._flow_id,
            data_schema=ConfigData.default_schema(user_input),
            errors=errors,
        )

    def _show_otp_form(self, errors=None):
        return self._flow_handler.async_show_form(
            step_id="otp",
            data_schema=ConfigData.otp_schema(),
            errors=errors,
        )
