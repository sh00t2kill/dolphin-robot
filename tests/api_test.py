"""test/api_test.py."""
import asyncio
from asyncio import sleep
import json
import logging
import os
import sys
from typing import Any

from custom_components.mydolphin_plus.common.connectivity_status import (
    ConnectivityStatus,
)
from custom_components.mydolphin_plus.common.consts import (
    API_DATA_LOGIN_TOKEN,
    API_DATA_MOTOR_UNIT_SERIAL,
    API_DATA_SERIAL_NUMBER,
    API_RECONNECT_INTERVAL,
    SIGNAL_API_STATUS,
    SIGNAL_AWS_CLIENT_STATUS,
    STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY,
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
formatter = logging.Formatter("%(asctime)s %(threadName)s[%(thread)d] %(levelname)s %(name)s %(message)s")
stream_handler.setFormatter(formatter)
root.addHandler(stream_handler)

_LOGGER = logging.getLogger(__name__)


class APITest:
    def __init__(self, internal_loop):
        self._login_credentials = {
            CONF_USERNAME: os.environ.get(CONF_USERNAME),
            CONF_PASSWORD: os.environ.get(CONF_PASSWORD),
        }

        self._internal_loop = internal_loop

        _LOGGER.info("Creating configuration manager instance")

        self._config_manager = ConfigManager(None)

        self._api = RestAPI(None, self._config_manager)
        self._aws_client = AWSClient(None, self._config_manager)

        self._api.set_local_async_dispatcher_send(self._async_dispatcher_send)
        self._aws_client.set_local_async_dispatcher_send(self._async_dispatcher_send)

        self._api_data_reloaded = False

    def _async_dispatcher_send(self, signal: str, *args: Any) -> None:
        _LOGGER.info(f"Signal: {signal}, Data: {json.dumps(args)}")

        if signal == SIGNAL_API_STATUS:
            status = args[1]
            self._internal_loop.create_task(self._on_api_status_changed(status)).__await__()

        if signal == SIGNAL_AWS_CLIENT_STATUS:
            status = args[1]
            self._internal_loop.create_task(self._on_aws_status_changed(status)).__await__()

    async def initialize(self):
        """Test API."""
        await self._config_manager.initialize(self._login_credentials)

        _LOGGER.info("Creating REST API instance")

        await self._restore_tokens()

        await self._api.initialize()

        if not self._api_data_reloaded:
            self._store_tokens()

        while True:
            if self._aws_client.status == ConnectivityStatus.CONNECTED:
                data = json.dumps(self._aws_client.data)

                _LOGGER.info(data)

            await sleep(15)

    def _store_tokens(self):
        _LOGGER.info("Storing tokens")
        api_data = self._api.data

        data = {
            STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY: api_data.get(STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY),
            API_DATA_SERIAL_NUMBER: api_data.get(API_DATA_SERIAL_NUMBER),
            API_DATA_MOTOR_UNIT_SERIAL: api_data.get(API_DATA_MOTOR_UNIT_SERIAL),
            API_DATA_LOGIN_TOKEN: api_data.get(API_DATA_LOGIN_TOKEN),
        }

        with open("tokens.json", "w") as f:
            f.write(json.dumps(data, indent=4))

    async def _restore_tokens(self):
        if not os.path.exists("tokens.json"):
            return

        _LOGGER.info("Restoring tokens")

        with open("tokens.json") as f:
            data = json.load(f)

            aws_token = data.get(STORAGE_DATA_AWS_TOKEN_ENCRYPTED_KEY)
            serial_number = data.get(API_DATA_SERIAL_NUMBER)
            motor_unit_serial = data.get(API_DATA_MOTOR_UNIT_SERIAL)
            api_token = data.get(API_DATA_LOGIN_TOKEN)

            await self._config_manager.update_tokens(api_token, aws_token, serial_number, motor_unit_serial)

        self._api_data_reloaded = True

    async def terminate(self):
        await self._api.terminate()

        await self._aws_client.terminate()

    async def _on_api_status_changed(self, status: ConnectivityStatus):
        if status == ConnectivityStatus.CONNECTED:
            await self._api.update()

            await self._aws_client.update_api_data(self._api.data)

            await self._aws_client.initialize()

        elif status == ConnectivityStatus.FAILED:
            await self._aws_client.terminate()

            await sleep(API_RECONNECT_INTERVAL.total_seconds())

            await self._api.initialize()

    async def _on_aws_status_changed(self, status: ConnectivityStatus):
        if status == ConnectivityStatus.FAILED:
            await sleep(WS_RECONNECT_INTERVAL.total_seconds())

            await self._api.initialize()

        if status == ConnectivityStatus.CONNECTED:
            await self._aws_client.update()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    instance = APITest(loop)

    try:
        loop.run_until_complete(instance.initialize())

    except KeyboardInterrupt:
        _LOGGER.info("Aborted")

    except Exception as rex:
        _LOGGER.error(f"Error: {rex}")

    finally:
        loop.run_until_complete(instance.terminate())
        loop.close()
