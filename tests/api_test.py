"""test/api_test.py."""
import asyncio
from asyncio import sleep
import logging
import os
import sys

from custom_components.mydolphin_plus.component.api.mydolphin_plus_api import (
    IntegrationAPI,
)
from custom_components.mydolphin_plus.configuration.models.config_data import ConfigData
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


def handle_update():
    """Do update logging."""
    _LOGGER.info("Data updated")


async def run():
    """Test API."""
    data = {
        CONF_USERNAME: os.environ.get(CONF_USERNAME),
        CONF_PASSWORD: os.environ.get(CONF_PASSWORD),
    }

    config_data = ConfigData.from_dict(data)

    api = IntegrationAPI(None)

    await api.initialize(config_data)

    while True:
        await sleep(1)


loop = asyncio.new_event_loop()

try:
    loop.run_until_complete(run())
finally:
    loop.close()
