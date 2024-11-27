"""test/api_test.py."""
import asyncio
from asyncio import sleep
from datetime import datetime
import json
import logging
import os
import sys
from typing import Any, Awaitable, Callable

from custom_components.mydolphin_plus.common.clean_modes import CleanModes
from custom_components.mydolphin_plus.common.connectivity_status import (
    ConnectivityStatus,
)
from custom_components.mydolphin_plus.common.consts import (
    API_RECONNECT_INTERVAL,
    SIGNAL_API_STATUS,
    SIGNAL_AWS_CLIENT_STATUS,
    UPDATE_API_INTERVAL,
    UPDATE_WS_INTERVAL,
    WS_RECONNECT_INTERVAL,
)
from custom_components.mydolphin_plus.common.joystick_direction import JoystickDirection
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

        self._actions = {
            "U": "Update WS Connection",
            "S": "Stop navigation",
            "F": "Forward navigation",
            "B": "Backward navigation",
            "L": "Left navigation",
            "R": "Right navigation",
            "E": "Exit navigation",
            "P": "Pickup",
            "C": "Clean"
        }

        self._actions_mapper: dict[str, Callable[[], Awaitable[None]]] = {
            "U": self._update,
            "S": self._stop_navigation,
            "F": self._forward_navigation,
            "B": self._backward_navigation,
            "L": self._left_navigation,
            "R": self._right_navigation,
            "E": self._exit_navigation,
            "P": self._pickup,
            "C": self._clean
        }

        instructions = ["Which action to perform:"]

        for action_key in self._actions:
            instructions.append(f"{action_key}) {self._actions[action_key]}")

        instructions.append("> ")
        self._instructions = "\n".join(instructions)

        self._ready_for_input = False

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

        await self._api.initialize()

        await sleep(3)

        while True:
            await self._read_input()

    async def _read_input(self):
        while not self._ready_for_input:
            await sleep(1)

        input_data = input(self._instructions).upper()

        if input_data in self._actions_mapper:
            action = self._actions_mapper[input_data]
            await action()

            await sleep(3)

    async def _update(self):
        _LOGGER.info("Update")

        await self._api.update()
        await self._aws_client.update()

    async def _stop_navigation(self):
        _LOGGER.info(JoystickDirection.STOP)

        self._aws_client.set_joystick_mode(JoystickDirection.STOP)

    async def _forward_navigation(self):
        _LOGGER.info(JoystickDirection.FORWARD)

        self._aws_client.set_joystick_mode(JoystickDirection.FORWARD)

    async def _backward_navigation(self):
        _LOGGER.info(JoystickDirection.BACKWARD)

        self._aws_client.set_joystick_mode(JoystickDirection.BACKWARD)

    async def _left_navigation(self):
        _LOGGER.info(JoystickDirection.LEFT)

        self._aws_client.set_joystick_mode(JoystickDirection.LEFT)

    async def _right_navigation(self):
        _LOGGER.info(JoystickDirection.RIGHT)

        self._aws_client.set_joystick_mode(JoystickDirection.RIGHT)

    async def _exit_navigation(self):
        _LOGGER.info("Exit navigation")

        self._aws_client.exit_joystick_mode()

    async def _pickup(self):
        _LOGGER.info("Pickup")

        self._aws_client.pickup()

    async def _clean(self):
        _LOGGER.info("Clean")

        self._aws_client.set_cleaning_mode(CleanModes.REGULAR)

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

            self._ready_for_input = True


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
