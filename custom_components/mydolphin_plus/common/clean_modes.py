from enum import StrEnum

from homeassistant.util import slugify


class CleanModes(StrEnum):
    REGULAR = "all"
    FAST_MODE = "short"
    FLOOR_ONLY = "floor"
    WATER_LINE = "water"
    ULTRA_CLEAN = "ultra"
    PICKUP = "pickup"


_ICON_CLEANING_MODES = {
    CleanModes.REGULAR: "mdi:border-all-variant",
    CleanModes.FAST_MODE: "mdi:clock-fast",
    CleanModes.FLOOR_ONLY: "mdi:border-bottom-variant",
    CleanModes.WATER_LINE: "mdi:format-align-top",
    CleanModes.ULTRA_CLEAN: "mdi:border-all",
}

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


def get_clean_mode_icon(clean_mode: CleanModes):
    icon = _ICON_CLEANING_MODES.get(clean_mode)

    return icon
