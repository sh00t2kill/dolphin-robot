import json
import logging
import os
import sys

from cryptography.fernet import InvalidToken

from homeassistant.config_entries import STORAGE_VERSION, ConfigEntry
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store

from ..common.clean_modes import (
    CLEAN_MODES_CYCLE_TIME,
    CleanModes,
    get_clean_mode_cycle_time_key,
)
from ..common.consts import (
    CONFIGURATION_FILE,
    DEFAULT_NAME,
    DOMAIN,
    INVALID_TOKEN_SECTION,
    STORAGE_DATA_API_TOKEN,
    STORAGE_DATA_AWS_TOKEN,
    STORAGE_DATA_LOCATING,
    STORAGE_DATA_MOTOR_UNIT_SERIAL,
    STORAGE_DATA_SERIAL_NUMBER,
    TOKEN_PARAMS,
)
from ..common.entity_descriptions import MyDolphinPlusEntityDescription
from ..models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class ConfigManager:
    _data: dict | None
    _config_data: ConfigData

    _store: Store | None
    _translations: dict | None
    _entry_title: str
    _entry_id: str

    _is_set_up_mode: bool
    _is_initialized: bool

    def __init__(self, hass: HomeAssistant | None, entry: ConfigEntry | None = None):
        self._hass = hass
        self._entry = entry
        self._entry_id = None if entry is None else entry.entry_id
        self._entry_title = DEFAULT_NAME if entry is None else entry.title

        self._config_data = ConfigData()

        self._data = None

        self._store = None
        self._translations = None

        self._is_set_up_mode = entry is None
        self._is_initialized = False
        self._is_home_assistant = hass is not None

        if self._is_home_assistant:
            self._store = Store(
                hass, STORAGE_VERSION, CONFIGURATION_FILE, encoder=JSONEncoder
            )

    @property
    def is_initialized(self) -> bool:
        is_initialized = self._is_initialized

        return is_initialized

    @property
    def entry(self) -> ConfigEntry:
        entry = self._entry

        return entry

    @property
    def entry_id(self) -> str:
        entry_id = self._entry_id

        return entry_id

    @property
    def name(self) -> str:
        entry_title = self._entry_title

        return entry_title

    @property
    def is_locating(self) -> bool:
        is_locating = self._data.get(STORAGE_DATA_LOCATING, False)

        return is_locating

    @property
    def api_token(self) -> str | None:
        api_token = self._data.get(STORAGE_DATA_API_TOKEN)

        return api_token

    @property
    def aws_token(self) -> str | None:
        aws_token = self._data.get(STORAGE_DATA_AWS_TOKEN)

        return aws_token

    @property
    def serial_number(self) -> str | None:
        serial_number = self._data.get(STORAGE_DATA_SERIAL_NUMBER)

        return serial_number

    @property
    def motor_unit_serial(self) -> str | None:
        motor_unit_serial = self._data.get(STORAGE_DATA_MOTOR_UNIT_SERIAL)

        return motor_unit_serial

    @property
    def _token_details(self):
        token_details = {
            token_param: self._data.get(token_param) for token_param in TOKEN_PARAMS
        }

        return token_details

    @property
    def should_login(self) -> bool:
        should_login = None in self._token_details.values()

        return should_login

    @property
    def config_data(self) -> ConfigData:
        config_data = self._config_data

        return config_data

    async def initialize(self, entry_config: dict):
        try:
            await self._load()

            self._config_data.update(entry_config)

            if self._hass is None:
                self._translations = {}

            else:
                self._translations = await translation.async_get_translations(
                    self._hass, self._hass.config.language, "entity", {DOMAIN}
                )

            _LOGGER.debug(
                f"Translations loaded, Data: {json.dumps(self._translations)}"
            )

            self._is_initialized = True

        except InvalidToken:
            self._is_initialized = False

            _LOGGER.error(
                f"Invalid encryption key, Please follow instructions in {INVALID_TOKEN_SECTION}"
            )

        except Exception as ex:
            self._is_initialized = False

            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize configuration manager, Error: {ex}, Line: {line_number}"
            )

    def get_translation(
        self,
        platform: Platform,
        entity_key: str,
        attribute: str,
        default_value: str | None = None,
    ) -> str | None:
        translation_key = (
            f"component.{DOMAIN}.entity.{platform}.{entity_key}.{attribute}"
        )

        translated_value = self._translations.get(translation_key, default_value)

        _LOGGER.debug(
            "Translations requested, "
            f"Key: {translation_key}, "
            f"Default value: {default_value}, "
            f"Value: {translated_value}"
        )

        return translated_value

    def get_entity_name(
        self,
        entity_description: MyDolphinPlusEntityDescription,
        device_info: DeviceInfo,
    ) -> str:
        entity_key = entity_description.key

        device_name = device_info.get("name")
        platform = entity_description.platform

        translated_name = self.get_translation(
            platform, entity_key, CONF_NAME, entity_description.name
        )

        entity_name = (
            device_name
            if translated_name is None or translated_name == ""
            else f"{device_name} {translated_name}"
        )

        return entity_name

    def get_clean_cycle_time(self, clean_mode: CleanModes) -> int:
        key = get_clean_mode_cycle_time_key(clean_mode)
        value = self._data.get(key)

        return value

    async def reset_login_details(self):
        for token_param in TOKEN_PARAMS:
            self._data[token_param] = None

        await self._save()

    async def update_login_details(self, api_token: str, serial_number: str):
        self._data[STORAGE_DATA_API_TOKEN] = api_token
        self._data[STORAGE_DATA_SERIAL_NUMBER] = serial_number

        await self._save()

    async def update_aws_token(self, aws_token: str | None):
        self._data[STORAGE_DATA_AWS_TOKEN] = aws_token

        await self._save()

    async def update_motor_unit_serial(self, motor_unit_serial: str):
        self._data[STORAGE_DATA_MOTOR_UNIT_SERIAL] = motor_unit_serial

        await self._save()

    async def update_clean_cycle_time(self, clean_mode: CleanModes, time: int):
        key = get_clean_mode_cycle_time_key(clean_mode)
        self._data[key] = int(time)

        await self._save()

    async def update_is_locating(self, state: bool):
        self._data[STORAGE_DATA_LOCATING] = state

        await self._save()

    def get_debug_data(self) -> dict:
        data = self._config_data.to_dict()

        for key in self._data:
            data[key] = self._data[key]

        return data

    async def _load(self):
        self._data = None

        await self._load_config_from_file()

        _LOGGER.info(f"loaded: {self._data}")
        should_save = False

        if self._data is None:
            should_save = True
            self._data = {}

        default_configuration = self._get_defaults()
        _LOGGER.info(f"default_configuration: {default_configuration}")

        for key in default_configuration:
            value = default_configuration[key]

            if key not in self._data:
                _LOGGER.info(f"adding {key}")
                should_save = True
                self._data[key] = value

        if should_save:
            _LOGGER.info("updated")
            await self._save()

    @staticmethod
    def _get_defaults() -> dict:
        data = {STORAGE_DATA_LOCATING: False}

        for clean_mode in list(CleanModes):
            key = get_clean_mode_cycle_time_key(CleanModes(clean_mode))
            default_time = CLEAN_MODES_CYCLE_TIME.get(clean_mode)

            data[key] = int(default_time)

        return data

    async def _load_config_from_file(self):
        if self._is_home_assistant:
            store_data = await self._store.async_load()

            if store_data is not None:
                self._data = store_data.get(self._entry_id)

        else:
            if not os.path.exists("config.json"):
                return

            with open("config.json") as f:
                self._data = json.load(f)

    async def remove(self, entry_id: str):
        if self._is_home_assistant:
            store_data = await self._store.async_load()

            if store_data is not None and entry_id in store_data:
                data = {key: store_data[key] for key in store_data}
                data.pop(entry_id)

                await self._store.async_save(data)

    async def _save(self):
        if self._is_home_assistant:
            should_save = False
            store_data = await self._store.async_load()

            if store_data is None:
                store_data = {}

            entry_data = store_data.get(self._entry_id, {})

            _LOGGER.debug(
                f"Storing config data: {json.dumps(self._data)}, "
                f"Exiting: {json.dumps(entry_data)}"
            )

            for key in self._data:
                stored_value = entry_data.get(key)

                if key in [CONF_PASSWORD, CONF_USERNAME]:
                    entry_data.pop(CONF_USERNAME)

                    if stored_value is not None:
                        should_save = True

                else:
                    current_value = self._data.get(key)

                    if stored_value != current_value:
                        should_save = True

                        entry_data[key] = self._data[key]

            if should_save and self._entry_id is not None:
                store_data[self._entry_id] = entry_data

                await self._store.async_save(store_data)
        else:
            with open("config.json", "w") as f:
                f.write(json.dumps(self._data, indent=4))
