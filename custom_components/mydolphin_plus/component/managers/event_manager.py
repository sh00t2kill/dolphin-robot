from __future__ import annotations

from datetime import datetime
import logging
import sys
from typing import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from ...component.helpers.const import *

_LOGGER = logging.getLogger(__name__)


class MyDolphinPlusEventManager:
    hass: HomeAssistant | None = None
    states: dict[str, dict]
    callback: Callable[[], None]

    def __init__(self, hass: HomeAssistant, callback: Callable[[], None]):
        self.hass = hass
        self.callback = callback
        self.states = {}
        self._remove_async_track_time = None

    async def initialize(self):
        self._remove_async_track_time = async_track_time_interval(
            self.hass, self._check_triggers, TRIGGER_INTERVAL
        )

    def terminate(self):
        if self._remove_async_track_time is not None:
            self._remove_async_track_time()
            self._remove_async_track_time = None

    def message_received(self, topic, payload):
        try:
            '''
            trigger_details = payload.get(TRIGGER_DETAILS, {})
            trigger_reason = trigger_details.get(TRIGGER_DETAILS_REASON)

            sensor_type = PLUG_SENSOR_TYPE.get(trigger_reason, None)

            if sensor_type is None:
                event_name = f"{SHINOBI_EVENT}{trigger_reason}"

                self.hass.bus.async_fire(event_name, payload)

            else:
                trigger_name = payload.get(TRIGGER_NAME)
                trigger_plug = trigger_details.get(TRIGGER_DETAILS_PLUG)

                if trigger_name is None:
                    trigger_name = trigger_details.get(TRIGGER_NAME)

                value = {
                    TRIGGER_NAME: trigger_name,
                    TRIGGER_PLUG: trigger_plug,
                    TRIGGER_DETAILS_REASON: trigger_reason,
                    TRIGGER_STATE: STATE_ON,
                    TRIGGER_TIMESTAMP: datetime.now().timestamp(),
                    TRIGGER_TOPIC: topic
                }

                previous_data = self.get(topic, sensor_type)
                previous_state = previous_data.get(TRIGGER_STATE, STATE_OFF)

                self.set(topic, sensor_type, value)

                if previous_state == STATE_OFF:
                    self.callback()
            '''
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to handle sensor message, Error: {ex}, Line: {line_number}")

    def _check_triggers(self, now):
        self.hass.async_create_task(self._async_check_triggers(now))

    async def _async_check_triggers(self, event_time):
        try:
            '''
            current_time = datetime.now().timestamp()

            all_keys = self.states.keys()
            changed = False

            for key in all_keys:
                data = self.states.get(key)

                if data is not None:
                    topic = data.get(TRIGGER_TOPIC, None)
                    trigger_reason = data.get(TRIGGER_DETAILS_REASON, None)
                    trigger_timestamp = data.get(TRIGGER_TIMESTAMP, None)
                    trigger_state = data.get(TRIGGER_STATE, STATE_OFF)

                    if topic is not None and trigger_state == STATE_ON:
                        sensor_type = PLUG_SENSOR_TYPE[trigger_reason]

                        diff = current_time - trigger_timestamp
                        event_duration = SENSOR_AUTO_OFF_INTERVAL.get(sensor_type, 20)

                        if diff >= event_duration:
                            changed = True
                            data[TRIGGER_STATE] = STATE_OFF

                            self.set(topic, sensor_type, data)

            if changed:
                self.callback()
            '''
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to check triggers (async) at {event_time}, Error: {ex}, Line: {line_number}"
            )

    def get(self, topic, event_type):
        key = self._get_key(topic, event_type)

        state = None # self.states.get(key, TRIGGER_DEFAULT)

        return state

    def set(self, topic, event_type, value):
        _LOGGER.debug(f"Set {event_type} state: {value} for {topic}")

        key = self._get_key(topic, event_type)

        self.states[key] = value

    @staticmethod
    def _get_key(topic, event_type):
        key = f"{topic}_{event_type}".lower()

        return key
