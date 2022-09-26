import logging

from homeassistant.backports.enum import StrEnum


class ConnectivityStatus(StrEnum):
    NotConnected = "Not connected"
    Connecting = "Establishing connection to API"
    Connected = "Connected to the API"
    TemporaryConnected = "Connected with temporary API key"
    Failed = "Failed to access API"
    InvalidCredentials = "Invalid credentials"
    Disconnected = "Disconnected by the system"
    NotFound = "API Not found"

    @staticmethod
    def get_log_level(status: StrEnum) -> int:
        if status == ConnectivityStatus.Connected:
            return logging.DEBUG
        elif status in [ConnectivityStatus.Disconnected]:
            return logging.INFO
        elif status in [ConnectivityStatus.NotConnected, ConnectivityStatus.Connecting]:
            return logging.WARNING
        else:
            return logging.ERROR

    @staticmethod
    def is_api_request_allowed(endpoint: str, status: StrEnum):
        result = status == ConnectivityStatus.Connected

        return result

    @staticmethod
    def get_config_errors(status: StrEnum):
        result = None
        status_mapping = {
            str(ConnectivityStatus.NotConnected): "invalid_server_details",
            str(ConnectivityStatus.Connecting): "invalid_server_details",
            str(ConnectivityStatus.Failed): "invalid_server_details",
            str(ConnectivityStatus.NotFound): "invalid_server_details",
            str(ConnectivityStatus.InvalidCredentials): "invalid_admin_credentials"
        }

        status_description = status_mapping.get(str(status))

        if status_description is not None:
            result = {"base": status_description}

        return result
