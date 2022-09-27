from homeassistant.backports.enum import StrEnum


class EntityStatus(StrEnum):
    EMPTY = "empty"
    READY = "ready"
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"
