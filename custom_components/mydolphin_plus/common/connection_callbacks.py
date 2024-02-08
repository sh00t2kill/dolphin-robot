from enum import StrEnum


class ConnectionCallbacks(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    CLOSED = "closed"
    INTERRUPTED = "interrupted"
    RESUMED = "resumed"
