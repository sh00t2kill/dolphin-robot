"""Storage handlers."""
from __future__ import annotations

import logging
from typing import Awaitable, Callable

from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store

from ... import *
from ...core.api.base_api import BaseAPI
from ...core.helpers.const import *
from ...core.helpers.enums import ConnectivityStatus

_LOGGER = logging.getLogger(__name__)


class StorageAPI(BaseAPI):
    _storage: Store

    def __init__(self,
                 hass: HomeAssistant,
                 async_on_data_changed: Callable[[], Awaitable[None]] | None = None,
                 async_on_status_changed: Callable[[ConnectivityStatus], Awaitable[None]] | None = None
                 ):

        super().__init__(hass, async_on_data_changed, async_on_status_changed)

        self._storage = Store(self.hass, STORAGE_VERSION, self._file_name, encoder=JSONEncoder)

    @property
    def _file_name(self):
        file_name = f"{DOMAIN}.config.json"

        return file_name

    @property
    def is_locating(self):
        is_locating = self.data.get(STORAGE_DATA_LOCATING, False)

        return is_locating

    async def initialize(self):
        await self._async_load()

    async def _async_load(self):
        """Load the retained data from store and return de-serialized data."""
        _LOGGER.info(f"Loading configuration from {self._file_name}")

        self.data = await self._storage.async_load()

        _LOGGER.debug(f"Loaded configuration data: {self.data}")

        await self.set_status(ConnectivityStatus.Connected)
        await self.fire_data_changed_event()

    async def _async_save(self):
        """Generate dynamic data to store and save it to the filesystem."""
        _LOGGER.info(f"Save configuration to {self._file_name}, Data: {self.data}")

        await self._storage.async_save(self.data)

        await self.fire_data_changed_event()

    async def set_locating_mode(self, is_on: bool):
        _LOGGER.debug(f"Set locating mode to {is_on}")

        self.data[STORAGE_DATA_LOCATING] = is_on

        await self._async_save()
