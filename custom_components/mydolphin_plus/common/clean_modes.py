from enum import StrEnum


class CleanModes(StrEnum):
    REGULAR = "all"
    FAST_MODE = "short"
    FLOOR_ONLY = "floor"
    WATER_LINE = "water"
    ULTRA_CLEAN = "ultra"
    PICKUP = "pickup"


# Keys of the cycle time presets for each clean mode, which older versions
# created as entities and kept in storage
LEGACY_CYCLE_TIME_KEYS = (
    "cycle_time_all",
    "cycle_time_short",
    "cycle_time_floor",
    "cycle_time_water",
    "cycle_time_ultra",
    "cycle_time_pickup",
)
