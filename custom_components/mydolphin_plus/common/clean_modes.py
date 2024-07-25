from enum import StrEnum

from homeassistant.util import slugify


class CleanModes(StrEnum):
    REGULAR = "all"
    FAST_MODE = "short"
    FLOOR_ONLY = "floor"
    WATER_LINE = "water"
    ULTRA_CLEAN = "ultra"
    PICKUP = "pickup"


CLEAN_MODES_CYCLE_TIME = {
    CleanModes.REGULAR: 120,
    CleanModes.FAST_MODE: 60,
    CleanModes.FLOOR_ONLY: 120,
    CleanModes.WATER_LINE: 120,
    CleanModes.ULTRA_CLEAN: 120,
    CleanModes.PICKUP: 5,
}


def get_clean_mode_cycle_time_name(clean_mode: CleanModes):
    name = f"Cycle Time {clean_mode}"

    return name


def get_clean_mode_cycle_time_key(clean_mode: CleanModes):
    name = get_clean_mode_cycle_time_name(clean_mode)
    key = slugify(name)

    return key
