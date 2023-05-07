"""Storage handlers."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store

from ...configuration.helpers.const import DOMAIN
from ...configuration.models.config_data import ConfigData
from ...core.api.base_api import BaseAPI
from ...core.helpers.const import STORAGE_VERSION
from ...core.helpers.enums import ConnectivityStatus
from ..helpers.const import (
    STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY,
    STORAGE_DATA_FILE_CONFIG,
    STORAGE_DATA_FILES,
    STORAGE_DATA_LOCATING,
)

_LOGGER = logging.getLogger(__name__)


class StorageAPI(BaseAPI):
    _stores: dict[str, Store] | None
    _config_data: ConfigData | None
    _data: dict

    def __init__(
        self,
        hass: HomeAssistant | None,
        async_on_data_changed: Callable[[], Awaitable[None]] | None = None,
        async_on_status_changed: Callable[[ConnectivityStatus], Awaitable[None]]
        | None = None,
    ):
        super().__init__(hass, async_on_data_changed, async_on_status_changed)

        self._config_data = None
        self._stores = None
        self._data = {}

    @property
    def _storage_config(self) -> Store:
        storage = self._stores.get(STORAGE_DATA_FILE_CONFIG)

        return storage

    @property
    def is_locating(self) -> bool:
        is_locating = self.data.get(STORAGE_DATA_LOCATING, False)

        return is_locating

    @property
    def aws_token_encrypted_key(self) -> str | None:
        is_locating = self.data.get(STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY, False)

        return is_locating

    async def initialize(self, config_data: ConfigData):
        self._config_data = config_data

        self._initialize_storages()

        await self._async_load_configuration()

    def _initialize_storages(self):
        stores = {}

        entry_id = self._config_data.entry.entry_id

        for storage_data_file in STORAGE_DATA_FILES:
            file_name = f"{DOMAIN}.{entry_id}.{storage_data_file}.json"

            stores[storage_data_file] = Store(
                self.hass, STORAGE_VERSION, file_name, encoder=JSONEncoder
            )

        self._stores = stores

    async def _async_load_configuration(self):
        """Load the retained data from store and return de-serialized data."""
        self.data = await self._storage_config.async_load()

        if self.data is None:
            self.data = {
                STORAGE_DATA_LOCATING: False,
                STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY: None,
            }

            await self._async_save()

        _LOGGER.debug(f"Loaded configuration data: {self.data}")

        await self.set_status(ConnectivityStatus.Connected)
        await self.fire_data_changed_event()

    async def _async_save(self):
        """Generate dynamic data to store and save it to the filesystem."""
        _LOGGER.info(f"Save configuration, Data: {self.data}")

        await self._storage_config.async_save(self.data)

        await self.fire_data_changed_event()

    async def set_locating_mode(self, is_on: bool):
        _LOGGER.debug(f"Set locating mode to {is_on}")

        self.data[STORAGE_DATA_LOCATING] = is_on

        await self._async_save()

    async def set_aws_token_encrypted_key(self, key: str):
        _LOGGER.debug(f"Set AWS Token encrypted key to {key}")

        self.data[STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY] = key

        await self._async_save()
