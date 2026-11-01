from enum import StrEnum
import logging

_LOGGER = logging.getLogger(__name__)


class CleanModes(StrEnum):
    REGULAR = "all"
    FAST_MODE = "short"
    FLOOR_ONLY = "floor"
    WATER_LINE = "water"
    ULTRA_CLEAN = "ultra"
    FULL_COVERAGE = "stairs"
    PICKUP = "pickup"


# ID of the features API entry that lists the clean modes
CLEANING_MODE_FEATURE = "2"

# Clean modes by the ID the features API gives them. The app shows these
# names, while the robot uses the values of CleanModes. None marks a mode the
# app hides, so Home Assistant leaves it out too.
CLEAN_MODE_FEATURES = {
    "291": CleanModes.REGULAR,
    "22": CleanModes.FAST_MODE,
    "23": CleanModes.FLOOR_ONLY,
    "211": CleanModes.FULL_COVERAGE,
    "292": None,  # Tic tac
}

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


def supported_clean_modes(features: object) -> list[CleanModes] | None:
    """
    Return the clean modes the features API lists.

    Return None when the API lists no clean modes, or one this integration
    doesn't know, so the caller can offer every mode instead.
    """
    if not isinstance(features, list):
        return None

    by_id = {
        feature.get("id"): feature for feature in features if isinstance(feature, dict)
    }
    subs = (by_id.get(CLEANING_MODE_FEATURE) or {}).get("subFeatures")
    if not isinstance(subs, list):
        return None

    ids = [sub.get("id") for sub in subs if isinstance(sub, dict)]
    unknown = [
        feature_id for feature_id in ids if feature_id not in CLEAN_MODE_FEATURES
    ]
    if unknown:
        _LOGGER.warning(
            "Robot lists unknown clean modes, offering all of them, IDs: %s", unknown
        )
        return None

    modes = [mode for feature_id in ids if (mode := CLEAN_MODE_FEATURES[feature_id])]
    return modes or None
