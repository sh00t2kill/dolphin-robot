from datetime import datetime
import logging

from ...component.helpers.const import *

_LOGGER = logging.getLogger(__name__)


def get_cleaning_mode_details(mode):
    details = CLEANING_MODES.get(mode)

    return details


def get_cleaning_mode_name(mode):
    details = get_cleaning_mode_details(mode)
    details_parts = details.split(" - ")
    name = details_parts[0]

    return name


def get_cleaning_mode_description(mode):
    details = get_cleaning_mode_details(mode)
    details_parts = details.split(" - ")
    description = details_parts[1]

    return description


def get_date_time_from_timestamp(timestamp):
    result = datetime.fromtimestamp(timestamp)
    return result
