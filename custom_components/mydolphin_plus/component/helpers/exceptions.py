from homeassistant.exceptions import HomeAssistantError

from ...component.helpers.enums import ConnectivityStatus


class MonitorNotFoundError(HomeAssistantError):
    monitor_id: str

    def __init__(self, monitor_id: str):
        self.monitor_id = monitor_id


class APIRequestException(Exception):
    endpoint: str
    response: dict

    def __init__(self, endpoint, response):
        super().__init__(f"API Request failed")

        self.endpoint = endpoint
        self.response = response


class APIValidationException(Exception):
    endpoint: str
    status: ConnectivityStatus

    def __init__(self, endpoint: str, status: ConnectivityStatus):
        super().__init__(f"API cannot process request to '{endpoint}', Status: {status}")

        self.endpoint = endpoint
        self.status = status
