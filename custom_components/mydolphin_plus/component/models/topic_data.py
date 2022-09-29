from ...component.helpers.const import *


class TopicData:
    serial: str
    dynamic: str

    def __init__(self, motor_unit_serial: str):
        self.motor_unit_serial = motor_unit_serial

        self._shadow_topic = TOPIC_SHADOW.format(motor_unit_serial)
        self.dynamic = TOPIC_DYNAMIC.format(motor_unit_serial)

    @property
    def get(self) -> str:
        return f"{self._shadow_topic}/{TOPIC_ACTION_GET}"

    @property
    def _get_wildcard(self) -> str:
        return f"{self.get}/{TOPIC_WILDCARD}"

    @property
    def get_accepted(self) -> str:
        return f"{self.get}/{TOPIC_CALLBACK_ACCEPTED}"

    @property
    def update(self) -> str:
        return f"{self._shadow_topic}/{TOPIC_ACTION_UPDATE}"

    @property
    def _update_wildcard(self) -> str:
        return f"{self.update}/{TOPIC_WILDCARD}"

    @property
    def update_accepted(self) -> str:
        return f"{self.update}/{TOPIC_CALLBACK_ACCEPTED}"

    @property
    def subscribe(self) -> list[str]:
        return [self.dynamic, self._get_wildcard, self._update_wildcard]
