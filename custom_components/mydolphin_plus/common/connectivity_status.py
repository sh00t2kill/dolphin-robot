from enum import StrEnum
import logging


class ConnectivityStatus(StrEnum):
    NOT_CONNECTED = "Not connected"
    CONNECTING = "Establishing connection to API"
    CONNECTED = "Connected to the API"
    TEMPORARY_CONNECTED = "Connected with temporary API key"
    FAILED = "Failed to access API"
    INVALID_CREDENTIALS = "Invalid credentials"
    MISSING_API_KEY = "Permanent API Key was not found"
    DISCONNECTED = "Disconnected by the system"
    API_NOT_FOUND = "API Not found"
    INVALID_ACCOUNT = "Invalid account"
    EXPIRED_TOKEN = "Expired Token"

    @staticmethod
    def get_log_level(status: StrEnum) -> int:
        if status in [
            ConnectivityStatus.CONNECTED,
            ConnectivityStatus.CONNECTING,
            ConnectivityStatus.DISCONNECTED,
            ConnectivityStatus.TEMPORARY_CONNECTED,
        ]:
            return logging.INFO
        elif status in [
            ConnectivityStatus.NOT_CONNECTED,
            ConnectivityStatus.EXPIRED_TOKEN,
        ]:
            return logging.WARNING
        else:
            return logging.ERROR

    @staticmethod
    def get_ha_error(status: str) -> str | None:
        errors = {
            str(ConnectivityStatus.INVALID_CREDENTIALS): "invalid_credentials",
            str(ConnectivityStatus.INVALID_ACCOUNT): "invalid_account",
            str(ConnectivityStatus.MISSING_API_KEY): "missing_permanent_api_key",
            str(ConnectivityStatus.FAILED): "invalid_server_details",
            str(ConnectivityStatus.API_NOT_FOUND): "invalid_server_details",
        }

        error_id = errors.get(status)

        return error_id


IGNORED_TRANSITIONS = {ConnectivityStatus.DISCONNECTED: [ConnectivityStatus.FAILED]}
