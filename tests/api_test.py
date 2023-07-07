"""test/api_test.py."""
import asyncio
from asyncio import sleep
import json
import logging
import os
import sys

from custom_components.mydolphin_plus.common.connectivity_status import (
    ConnectivityStatus,
)
from custom_components.mydolphin_plus.common.consts import (
    API_RECONNECT_INTERVAL,
    WS_RECONNECT_INTERVAL,
)
from custom_components.mydolphin_plus.managers.aws_client import AWSClient
from custom_components.mydolphin_plus.managers.config_manager import ConfigManager
from custom_components.mydolphin_plus.managers.rest_api import RestAPI
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

DEBUG = str(os.environ.get("DEBUG", False)).lower() == str(True).lower()

log_level = logging.DEBUG if DEBUG else logging.INFO

root = logging.getLogger()
root.setLevel(log_level)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(log_level)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
stream_handler.setFormatter(formatter)
root.addHandler(stream_handler)

_LOGGER = logging.getLogger(__name__)


class APITest:
    def __init__(self):
        self._login_credentials = {
            CONF_USERNAME: os.environ.get(CONF_USERNAME),
            CONF_PASSWORD: os.environ.get(CONF_PASSWORD),
        }

        _LOGGER.info("Creating configuration manager instance")

        self._config_manager = ConfigManager(None)
        self._config_manager.update_credentials(self._login_credentials)

        self._api = RestAPI(None, self._config_manager, self._on_api_status_changed)
        self._aws_client = AWSClient(None, self._on_aws_status_changed)

    async def initialize(self):
        """Test API."""
        await self._config_manager.initialize()

        _LOGGER.info("Creating REST API instance")

        await self._api.initialize(self._config_manager.aws_token_encrypted_key)

        while True:
            await sleep(1)

            if self._aws_client.status == ConnectivityStatus.Connected:
                data = json.dumps(self._aws_client.data, indent=4)

                _LOGGER.info(data)

    async def _on_api_status_changed(self, status: ConnectivityStatus):
        if status == ConnectivityStatus.Connected:
            await self._api.update()

            await self._aws_client.update_api_data(self._api.data)

            await self._aws_client.initialize()

        elif status == ConnectivityStatus.Failed:
            await self._aws_client.terminate()

            await sleep(API_RECONNECT_INTERVAL.total_seconds())

            await self._api.initialize(self._config_manager.aws_token_encrypted_key)

    async def _on_aws_status_changed(self, status: ConnectivityStatus):
        if status == ConnectivityStatus.Failed:
            await self._api.initialize(None)

            await sleep(WS_RECONNECT_INTERVAL.total_seconds())

            await self._api.initialize(self._config_manager.aws_token_encrypted_key)

        if status == ConnectivityStatus.Connected:
            await self._aws_client.update()


loop = asyncio.new_event_loop()

try:
    instance = APITest()
    loop.run_until_complete(instance.initialize())
finally:
    loop.close()
