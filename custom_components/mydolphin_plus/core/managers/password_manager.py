from __future__ import annotations

import logging
from os import path, remove

from cryptography.fernet import Fernet

from homeassistant.core import HomeAssistant

from ...core.helpers.const import *
from ...core.managers.storage_manager import StorageManager
from ...core.models.storage_data import StorageData

_LOGGER = logging.getLogger(__name__)


class PasswordManager:
    data: StorageData | None
    hass: HomeAssistant
    crypto: Fernet

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.data = None

    async def initialize(self):
        if self.data is None:
            storage_manager = StorageManager(self.hass)

            self.data = await storage_manager.async_load_from_store()

            if self.data.key is None:
                legacy_key_path = self.hass.config.path(DOMAIN_KEY_FILE)

                if path.exists(legacy_key_path):
                    with open(legacy_key_path, "rb") as file:
                        self.data.key = file.read().decode("utf-8")

                    remove(legacy_key_path)
                else:
                    self.data.key = Fernet.generate_key().decode("utf-8")

                await storage_manager.async_save_to_store(self.data)

            self.crypto = Fernet(self.data.key.encode())

    def set(self, data: str) -> str:
        if data is not None:
            data = self.crypto.encrypt(data.encode()).decode()

        return data

    def get(self, data: str) -> str:
        if data is not None and len(data) > 0:
            data = self.crypto.decrypt(data.encode()).decode()

        return data
