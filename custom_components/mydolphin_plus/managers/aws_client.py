from __future__ import annotations

import asyncio
from datetime import datetime
import json
import logging
import os
import sys
from time import sleep
from typing import Any

import aiofiles
from awscrt import auth, mqtt
from awsiot import mqtt_connection_builder

from homeassistant.const import CONF_MODE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send

from ..common.clean_modes import CleanModes
from ..common.connection_callbacks import ConnectionCallbacks
from ..common.connectivity_status import IGNORED_TRANSITIONS, ConnectivityStatus
from ..common.consts import (
    API_RESPONSE_DATA_ACCESS_KEY_ID,
    API_RESPONSE_DATA_SECRET_ACCESS_KEY,
    API_RESPONSE_DATA_TOKEN,
    ATTR_REMOTE_CONTROL_MODE_EXIT,
    AWS_IOT_PORT,
    AWS_IOT_URL,
    AWS_REGION,
    CA_FILE_NAME,
    DATA_CYCLE_INFO_CLEANING_MODE_DURATION,
    DATA_FILTER_BAG_INDICATION_RESET_FBI_COMMAND,
    DATA_LED_ENABLE,
    DATA_LED_INTENSITY,
    DATA_LED_MODE,
    DATA_ROBOT_FAMILY,
    DATA_ROOT_STATE,
    DATA_ROOT_TIMESTAMP,
    DATA_ROOT_VERSION,
    DATA_SCHEDULE_CLEANING_MODE,
    DATA_SCHEDULE_IS_ENABLED,
    DATA_SCHEDULE_TIME,
    DATA_SCHEDULE_TIME_HOURS,
    DATA_SCHEDULE_TIME_MINUTES,
    DATA_SECTION_ACTIVITY,
    DATA_SECTION_CYCLE_INFO,
    DATA_SECTION_DYNAMIC,
    DATA_SECTION_FILTER_BAG_INDICATION,
    DATA_SECTION_LED,
    DATA_SECTION_SYSTEM_STATE,
    DATA_STATE_DESIRED,
    DATA_STATE_REPORTED,
    DATA_SYSTEM_STATE_PWS_STATE,
    DEFAULT_ENABLE,
    DEFAULT_LED_INTENSITY,
    DEFAULT_TIME_PART,
    DOMAIN,
    DYNAMIC_CONTENT,
    DYNAMIC_CONTENT_DIRECTION,
    DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL,
    DYNAMIC_CONTENT_REMOTE_CONTROL_MODE,
    DYNAMIC_CONTENT_SERIAL_NUMBER,
    DYNAMIC_CONTENT_SPEED,
    DYNAMIC_DESCRIPTION,
    DYNAMIC_DESCRIPTION_JOYSTICK,
    DYNAMIC_DESCRIPTION_TEMPERATURE,
    DYNAMIC_TYPE,
    DYNAMIC_TYPE_PWS_REQUEST,
    LED_MODE_BLINKING,
    MQTT_MESSAGE_ENCODING,
    SIGNAL_AWS_CLIENT_STATUS,
    TOPIC_CALLBACK_ACCEPTED,
    TOPIC_CALLBACK_REJECTED,
    WS_DATA_DIFF,
    WS_DATA_TIMESTAMP,
    WS_DATA_VERSION,
    WS_LAST_UPDATE,
)
from ..common.joystick_direction import JoystickDirection
from ..common.power_supply_state import PowerSupplyState
from ..common.robot_family import RobotFamily
from ..models.topic_data import TopicData
from .config_manager import ConfigManager

_LOGGER = logging.getLogger(__name__)


class AWSClient:
    _awsiot_client: mqtt.Connection | None
    _robot_family: RobotFamily | None

    _topic_data: TopicData | None
    _status: ConnectivityStatus | None

    def __init__(self, hass: HomeAssistant | None, config_manager: ConfigManager):
        try:
            awsiot_id = (
                DOMAIN if config_manager.entry_id is None else config_manager.entry_id
            )

            self._hass = hass
            self._loop = asyncio.new_event_loop() if hass is None else hass.loop
            self._config_manager = config_manager
            self._awsiot_id = awsiot_id
            self._robot_family = None

            self._api_data = {}
            self._data = {}

            self._topic_data = None
            self._awsiot_client = None
            self._messages_published: dict[int, dict[str, str]] = {}

            self._status = None

            self._local_async_dispatcher_send = None

            self._connection_callbacks = {
                ConnectionCallbacks.SUCCESS: self._on_connection_success,
                ConnectionCallbacks.FAILURE: self._on_connection_failure,
                ConnectionCallbacks.CLOSED: self._on_connection_closed,
                ConnectionCallbacks.INTERRUPTED: self._on_connection_interrupted,
                ConnectionCallbacks.RESUMED: self._on_connection_resumed,
            }

            self._dynamic_message_handlers = {
                DYNAMIC_TYPE_PWS_REQUEST: self._on_pws_request_message
            }

            self._on_publish_completed_callback = lambda f: self._on_publish_completed(
                f
            )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load MyDolphin Plus WS, error: {ex}, line: {line_number}"
            )

    @property
    def status(self) -> str | None:
        status = self._status

        return status

    @property
    def _is_home_assistant(self):
        return self._hass is not None

    @property
    def _has_running_loop(self):
        return self._hass.loop is not None and not self._hass.loop.is_closed()

    @property
    def data(self) -> dict:
        return self._data

    async def terminate(self):
        try:

            def _on_terminate_future_completed(future):
                future.result()

                self._awsiot_client = None

            if self._awsiot_client is not None:
                disconnect_future = self._awsiot_client.disconnect()
                disconnect_future.add_done_callback(_on_terminate_future_completed)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(
                "Failed to gracefully shutdown AWS IOT Client, setting it to None, "
                f"Error: {ex}, Line: {line_number}"
            )

            self._awsiot_client = None

        self._set_status(ConnectivityStatus.DISCONNECTED, "terminate requested")

    async def initialize(self):
        try:
            self._set_status(
                ConnectivityStatus.CONNECTING, "Initializing MyDolphin AWS IOT WS"
            )

            aws_token = self._api_data.get(API_RESPONSE_DATA_TOKEN)
            aws_key = self._api_data.get(API_RESPONSE_DATA_ACCESS_KEY_ID)
            aws_secret = self._api_data.get(API_RESPONSE_DATA_SECRET_ACCESS_KEY)

            _LOGGER.debug(
                f"AWS IAM Credentials, Key: {aws_key}, Secret: {aws_secret}, Token: {aws_token}"
            )

            self._topic_data = TopicData(self._config_manager.motor_unit_serial)

            ca_content = await self._get_certificate()

            if self._is_home_assistant:
                client = await self._hass.async_add_executor_job(
                    self._get_client, aws_key, aws_secret, aws_token, ca_content
                )

            else:
                client = self._get_client(aws_key, aws_secret, aws_token, ca_content)

            def _on_connect_future_completed(future):
                future_results = future.result()
                _LOGGER.info(f"_on_connect_future_completed: {future_results}")

                self._awsiot_client = client

            connect_future = client.connect()
            connect_future.add_done_callback(_on_connect_future_completed)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            message = f"Failed to initialize MyDolphin Plus WS, error: {ex}, line: {line_number}"

            self._set_status(ConnectivityStatus.FAILED, message)

    def _get_client(self, aws_key, aws_secret, aws_token, ca_content):
        credentials_provider = auth.AwsCredentialsProvider.new_static(
            aws_key, aws_secret, aws_token
        )

        client = mqtt_connection_builder.websockets_with_default_aws_signing(
            endpoint=AWS_IOT_URL,
            port=AWS_IOT_PORT,
            region=AWS_REGION,
            ca_bytes=ca_content,
            credentials_provider=credentials_provider,
            client_id=self._awsiot_id,
            clean_session=False,
            keep_alive_secs=30,
            on_connection_success=self._connection_callbacks.get(
                ConnectionCallbacks.SUCCESS
            ),
            on_connection_failure=self._connection_callbacks.get(
                ConnectionCallbacks.FAILURE
            ),
            on_connection_closed=self._connection_callbacks.get(
                ConnectionCallbacks.CLOSED
            ),
            on_connection_interrupted=self._connection_callbacks.get(
                ConnectionCallbacks.INTERRUPTED
            ),
            on_connection_resumed=self._connection_callbacks.get(
                ConnectionCallbacks.RESUMED
            ),
        )

        return client

    def _subscribe(self):
        _LOGGER.debug(f"Subscribing topics: {self._topic_data.subscribe}")

        topics_to_subscribe = self._topic_data.subscribe.copy()

        def _on_subscribe_future_completed(future):
            subscribe_result = future.result()
            _LOGGER.info(
                f"Subscribed `{subscribe_result}` with {subscribe_result['qos']}"
            )

            if len(topics_to_subscribe) > 0:
                next_topic = topics_to_subscribe[0]
                topics_to_subscribe.remove(next_topic)

                next_subscribe_future, next_packet_id = self._awsiot_client.subscribe(
                    topic=next_topic,
                    qos=mqtt.QoS.AT_MOST_ONCE,
                    callback=self._message_callback,
                )
                next_subscribe_future.add_done_callback(_on_subscribe_future_completed)

        first_topic = topics_to_subscribe[0]

        topics_to_subscribe.remove(first_topic)

        subscribe_future, packet_id = self._awsiot_client.subscribe(
            topic=first_topic,
            qos=mqtt.QoS.AT_MOST_ONCE,
            callback=self._message_callback,
        )
        subscribe_future.add_done_callback(_on_subscribe_future_completed)

    async def update_api_data(self, api_data: dict):
        self._api_data = api_data

        if api_data is None:
            self._robot_family = RobotFamily.ALL

        else:
            robot_family_str = api_data.get(DATA_ROBOT_FAMILY)
            self._robot_family = RobotFamily.from_string(robot_family_str)

    async def update(self):
        try:
            if self._status == ConnectivityStatus.CONNECTED:
                _LOGGER.debug("Connected. Refresh details")

                now = datetime.now().timestamp()

                self.data[WS_LAST_UPDATE] = int(now)

                self._publish(self._topic_data.get)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to update WS data, error: {ex}, line: {line_number}")

    def _on_connection_success(self, connection, callback_data):
        if isinstance(callback_data, mqtt.OnConnectionSuccessData):
            _LOGGER.debug(f"AWS IoT successfully connected, URL: {AWS_IOT_URL}")
            self._awsiot_client = connection

            self._subscribe()

            self._set_status(ConnectivityStatus.CONNECTED)

    def _on_connection_failure(self, connection, callback_data):
        if connection is not None and isinstance(
            callback_data, mqtt.OnConnectionFailureData
        ):
            message = f"AWS IoT connection failed, Error: {callback_data.error}"

            self._set_status(ConnectivityStatus.FAILED, message)

    def _on_connection_closed(self, connection, callback_data):
        if connection is not None and isinstance(
            callback_data, mqtt.OnConnectionClosedData
        ):
            message = "AWS IoT connection was closed"

            self._set_status(ConnectivityStatus.DISCONNECTED, message)

    def _on_connection_interrupted(self, connection, error, **_kwargs):
        message = f"AWS IoT connection interrupted, Error: {error}"

        if connection is None:
            _LOGGER.error(message)

        else:
            self._set_status(ConnectivityStatus.FAILED, message)

    def _on_connection_resumed(
        self, connection, return_code, session_present, **_kwargs
    ):
        _LOGGER.debug(
            f"AWS IoT connection resumed, Code: {return_code}, Session Present: {session_present}"
        )
        self._awsiot_client = connection

        if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
            _LOGGER.debug("Resubscribing to existing topics")

            resubscribe_future, _ = connection.resubscribe_existing_topics()

            resubscribe_future.add_done_callback(self._on_resubscribe_complete)

        self._set_status(ConnectivityStatus.CONNECTED)

    @staticmethod
    def _on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        _LOGGER.info(f"Resubscribe results: {resubscribe_results}")

        for topic, qos in resubscribe_results["topics"]:
            if qos is None:
                _LOGGER.error(f"Server rejected resubscribe to topic: {topic}")

    def _message_callback(self, topic, payload, dup, qos, retain, **kwargs):
        message_payload = payload.decode(MQTT_MESSAGE_ENCODING)

        try:
            has_message = len(message_payload) <= 0
            payload_data = {} if has_message else json.loads(message_payload)

            motor_unit_serial = self._config_manager.motor_unit_serial
            _LOGGER.debug(
                f"Message received for device {motor_unit_serial}, Topic: {topic}"
            )

            if topic.endswith(TOPIC_CALLBACK_REJECTED):
                _LOGGER.warning(
                    f"Rejected message for {topic}, Message: {message_payload}"
                )

            elif topic == self._topic_data.dynamic:
                self._on_dynamic_content_received(payload_data)

            elif topic.endswith(TOPIC_CALLBACK_ACCEPTED):
                _LOGGER.debug(f"Payload: {message_payload}")

                version = payload_data.get(DATA_ROOT_VERSION)
                server_timestamp = payload_data.get(DATA_ROOT_TIMESTAMP)

                now = datetime.now().timestamp()
                diff = int(now) - server_timestamp

                self.data[WS_DATA_VERSION] = version
                self.data[WS_DATA_TIMESTAMP] = server_timestamp
                self.data[WS_DATA_DIFF] = diff

                state = payload_data.get(DATA_ROOT_STATE, {})
                reported = state.get(DATA_STATE_REPORTED, {})

                for category in reported.keys():
                    category_data = reported.get(category)

                    if category_data is not None:
                        latest_data = self.data.get(category)

                        if isinstance(latest_data, dict):
                            self.data[category].update(category_data)

                        else:
                            self.data[category] = category_data

                if topic == self._topic_data.get_accepted:
                    if self._robot_family == RobotFamily.M700:
                        self._read_temperature_and_in_water_details()

                elif topic == self._topic_data.update_accepted:
                    desired = state.get(DATA_STATE_DESIRED)

                    if desired is not None:
                        cleaning_mode = desired.get(DATA_SCHEDULE_CLEANING_MODE, {})
                        mode = cleaning_mode.get(CONF_MODE)

                        if mode is not None:
                            sleep(1)
                            self._set_cycle_time(mode)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno
            message_details = f"Topic: {topic}, Data: {payload}"
            error_details = f"Error: {str(ex)}, Line: {line_number}"

            _LOGGER.error(
                f"Callback parsing failed, {message_details}, {error_details}"
            )

    def _on_dynamic_content_received(self, message: dict):
        _LOGGER.debug(f"Dynamic payload: {message}")

        message_type = message.get(DYNAMIC_TYPE)
        content = message.get(DYNAMIC_CONTENT)
        handler = self._dynamic_message_handlers.get(message_type)

        if DATA_SECTION_DYNAMIC not in self.data:
            self.data[DATA_SECTION_DYNAMIC] = {}

        self.data[DATA_SECTION_DYNAMIC][message_type] = content

        if handler is not None:
            handler(message)

    def _on_pws_request_message(self, message: dict):
        direction = message.get(DYNAMIC_CONTENT_DIRECTION)
        remote_control_mode = message.get(DYNAMIC_CONTENT_REMOTE_CONTROL_MODE)

        if direction is not None:
            self.data[DATA_SECTION_ACTIVITY] = direction

        if remote_control_mode == ATTR_REMOTE_CONTROL_MODE_EXIT:
            self.data[DATA_SECTION_ACTIVITY] = None

    def _send_desired_command(self, payload: dict | None):
        data = {DATA_ROOT_STATE: {DATA_STATE_DESIRED: payload}}

        self._publish(self._topic_data.update, data)

    def _send_dynamic_command(self, description: str, payload: dict | None):
        payload[DYNAMIC_TYPE] = DYNAMIC_TYPE_PWS_REQUEST
        payload[DYNAMIC_DESCRIPTION] = description

        self._publish(self._topic_data.dynamic, payload)

    def _publish(self, topic: str, data: dict | None = None):
        if data is None:
            data = {}

        payload = json.dumps(data)

        if self._status == ConnectivityStatus.CONNECTED:
            try:
                if self._awsiot_client is not None:
                    publish_future, packet_id = self._awsiot_client.publish(
                        topic, payload, mqtt.QoS.AT_MOST_ONCE
                    )
                    self._pre_publish_message(packet_id, topic, payload)

                    publish_future.add_done_callback(
                        self._on_publish_completed_callback
                    )

            except Exception as ex:
                _LOGGER.error(
                    f"Error while trying to publish message: {data} to {topic}, Error: {str(ex)}"
                )

        else:
            _LOGGER.error(
                f"Failed to publish message: {data} to {topic}, Broker is not connected"
            )

    def _pre_publish_message(self, message_id: int, topic: str, payload: str):
        _LOGGER.debug(f"Published message to {topic}, Data: {payload}")

        self._messages_published[message_id] = {"topic": topic, "payload": payload}

    def _post_message_published(self, message_id: int):
        published_data = self._messages_published.get(message_id, {})

        topic = published_data.get("topic")
        payload = published_data.get("payload")

        _LOGGER.info(f"Published message #{message_id} to {topic}, Data: {payload}")

        del self._messages_published[message_id]

    def _on_publish_completed(self, publish_future):
        publish_results = publish_future.result()
        _LOGGER.debug(f"Publish results: {publish_results}")

        if publish_results is not None and "packet_id" in publish_results:
            packet_id = publish_results.get("packet_id")

            self._post_message_published(packet_id)

    def set_cleaning_mode(self, clean_mode: CleanModes):
        data = {DATA_SCHEDULE_CLEANING_MODE: {CONF_MODE: str(clean_mode)}}

        _LOGGER.info(f"Set cleaning mode, Desired: {data}")
        self._send_desired_command(data)

    def _set_cycle_time(self, clean_mode: CleanModes):
        cycle_time = self._config_manager.get_clean_cycle_time(clean_mode)

        data = {
            DATA_SECTION_CYCLE_INFO: {
                DATA_CYCLE_INFO_CLEANING_MODE_DURATION: cycle_time,
            }
        }

        _LOGGER.info(f"Set cycle time, Desired: {data}")
        self._send_desired_command(data)

    def set_led_mode(self, mode: int):
        data = self._get_led_settings(DATA_LED_MODE, mode)

        _LOGGER.info(f"Set led mode, Desired: {data}")
        self._send_desired_command(data)

    def set_led_intensity(self, intensity: int):
        data = self._get_led_settings(DATA_LED_INTENSITY, intensity)

        _LOGGER.info(f"Set led intensity, Desired: {data}")
        self._send_desired_command(data)

    def set_led_enabled(self, is_enabled: bool):
        data = self._get_led_settings(DATA_LED_ENABLE, is_enabled)

        _LOGGER.info(f"Set led enabled mode, Desired: {data}")
        self._send_desired_command(data)

    def set_joystick_mode(self, direction: JoystickDirection):
        request_data = {
            DYNAMIC_CONTENT: {
                DYNAMIC_CONTENT_SPEED: direction.get_speed(),
                DYNAMIC_CONTENT_DIRECTION: direction,
            }
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_JOYSTICK, request_data)

    def exit_joystick_mode(self):
        request_data = {
            DYNAMIC_CONTENT: {
                DYNAMIC_CONTENT_REMOTE_CONTROL_MODE: ATTR_REMOTE_CONTROL_MODE_EXIT
            }
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_JOYSTICK, request_data)

    def _read_temperature_and_in_water_details(self):
        motor_unit_serial = self._config_manager.motor_unit_serial
        serial_number = self._config_manager.serial_number

        request_data = {
            DYNAMIC_CONTENT_SERIAL_NUMBER: serial_number,
            DYNAMIC_CONTENT_MOTOR_UNIT_SERIAL: motor_unit_serial,
        }

        self._send_dynamic_command(DYNAMIC_DESCRIPTION_TEMPERATURE, request_data)

    def pickup(self):
        self.set_cleaning_mode(CleanModes.PICKUP)

    def pause(self):
        request_data = {
            DATA_SECTION_SYSTEM_STATE: {
                DATA_SYSTEM_STATE_PWS_STATE: PowerSupplyState.OFF.value
            }
        }

        _LOGGER.info(f"Set power state, Desired: {request_data}")
        self._send_desired_command(request_data)

    def reset_filter_indicator(self):
        request_data = {
            DATA_SECTION_FILTER_BAG_INDICATION: {
                DATA_FILTER_BAG_INDICATION_RESET_FBI_COMMAND: True
            }
        }

        _LOGGER.info(f"Reset filter bag indicator, Desired: {request_data}")
        self._send_desired_command(request_data)

    @staticmethod
    def _get_schedule_settings(enabled, mode, job_time):
        hours = DEFAULT_TIME_PART
        minutes = DEFAULT_TIME_PART

        if enabled and job_time is not None:
            job_time_parts = job_time.split(":")
            hours = int(job_time_parts[0])
            minutes = int(job_time_parts[1])

        data = {
            DATA_SCHEDULE_IS_ENABLED: enabled,
            DATA_SCHEDULE_CLEANING_MODE: {CONF_MODE: mode},
            DATA_SCHEDULE_TIME: {
                DATA_SCHEDULE_TIME_HOURS: hours,
                DATA_SCHEDULE_TIME_MINUTES: minutes,
            },
        }

        return data

    def _get_led_settings(self, key, value):
        default_data = {
            DATA_LED_ENABLE: DEFAULT_ENABLE,
            DATA_LED_INTENSITY: DEFAULT_LED_INTENSITY,
            DATA_LED_MODE: LED_MODE_BLINKING,
        }

        request_data = self.data.get(DATA_SECTION_LED, default_data)
        request_data[key] = value

        data = {DATA_SECTION_LED: request_data}

        return data

    def _set_status(self, status: ConnectivityStatus, message: str | None = None):
        log_level = ConnectivityStatus.get_log_level(status)

        if status != self._status:
            ignored_transitions = IGNORED_TRANSITIONS.get(self._status, [])
            should_perform_action = status not in ignored_transitions

            log_message = f"Status update {self._status} --> {status}"

            if not should_perform_action:
                log_message = f"{log_message}, no action will be performed"

            if message is not None:
                log_message = f"{log_message}, {message}"

            _LOGGER.log(log_level, log_message)

            if should_perform_action:
                self._status = status

                self._async_dispatcher_send(
                    SIGNAL_AWS_CLIENT_STATUS,
                    self._config_manager.entry_id,
                    status,
                )

        else:
            log_message = f"Status is {status}"

            if message is None:
                log_message = f"{log_message}, {message}"

            _LOGGER.log(log_level, log_message)

    def set_local_async_dispatcher_send(self, callback):
        self._local_async_dispatcher_send = callback

    def _async_dispatcher_send(self, signal: str, *args: Any) -> None:
        if self._hass is None:
            self._local_async_dispatcher_send(signal, *args)

        else:
            dispatcher_send(self._hass, signal, *args)

    @staticmethod
    async def _get_certificate():
        script_dir = os.path.dirname(__file__)
        ca_file_path = os.path.join(script_dir, CA_FILE_NAME)

        _LOGGER.debug(f"Loading CA file from {ca_file_path}")

        ca_file = await aiofiles.open(ca_file_path, mode="rb")
        ca_content = await ca_file.read()
        await ca_file.close()

        return ca_content
