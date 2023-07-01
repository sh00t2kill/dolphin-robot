import calendar
from dataclasses import dataclass

from custom_components.mydolphin_plus.common.consts import (
    CLEANING_MODES_SHORT,
    DATA_KEY_AWS_BROKER,
    DATA_KEY_CLEAN_MODE,
    DATA_KEY_CYCLE_COUNT,
    DATA_KEY_CYCLE_TIME,
    DATA_KEY_CYCLE_TIME_LEFT,
    DATA_KEY_FILTER_STATUS,
    DATA_KEY_LED,
    DATA_KEY_LED_MODE,
    DATA_KEY_MAIN_UNIT_STATUS,
    DATA_KEY_NETWORK_NAME,
    DATA_KEY_ROBOT_STATUS,
    DATA_KEY_ROBOT_TYPE,
    DATA_KEY_RSSI,
    DATA_KEY_SCHEDULE,
    DATA_KEY_STATUS,
    DATA_KEY_VACUUM,
    DATA_KEY_WEEKLY_SCHEDULER,
    DATA_SECTION_DELAY,
    ICON_LED_MODES,
    VACUUM_FEATURES,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.components.light import LightEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.components.vacuum import (
    StateVacuumEntityDescription,
    VacuumEntityFeature,
)
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS, EntityCategory, UnitOfTime
from homeassistant.helpers.entity import EntityDescription
from homeassistant.util import slugify


@dataclass(slots=True)
class MyDolphinPlusVacuumEntityDescription(StateVacuumEntityDescription):
    """A class that describes vacuum entities."""

    features: VacuumEntityFeature = VacuumEntityFeature(0)
    fan_speed_list: list[str] = ()


@dataclass(slots=True)
class MyDolphinPlusDailyBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes vacuum entities."""

    day: str | None = None


ENTITY_DESCRIPTIONS: list[EntityDescription] = [
    MyDolphinPlusVacuumEntityDescription(
        key=slugify(DATA_KEY_VACUUM),
        name="",
        features=VACUUM_FEATURES,
        fan_speed_list=list(CLEANING_MODES_SHORT.keys()),
        translation_key=slugify(DATA_KEY_VACUUM),
    ),
    LightEntityDescription(
        key=slugify(DATA_KEY_LED),
        name=DATA_KEY_LED,
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key=slugify(DATA_KEY_LED_MODE),
        name=DATA_KEY_LED_MODE,
        options=list(ICON_LED_MODES.keys()),
        entity_category=EntityCategory.CONFIG,
        translation_key=slugify(DATA_KEY_LED_MODE),
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_STATUS),
        name=DATA_KEY_STATUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_RSSI),
        name=DATA_KEY_RSSI,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_NETWORK_NAME),
        name=DATA_KEY_NETWORK_NAME,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_CLEAN_MODE),
        name=DATA_KEY_CLEAN_MODE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_MAIN_UNIT_STATUS),
        name=DATA_KEY_MAIN_UNIT_STATUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_ROBOT_TYPE),
        name=DATA_KEY_ROBOT_STATUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_ROBOT_TYPE),
        name=DATA_KEY_ROBOT_TYPE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_CYCLE_COUNT),
        name=DATA_KEY_CYCLE_COUNT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_FILTER_STATUS),
        name=DATA_KEY_FILTER_STATUS,
        translation_key=slugify(DATA_KEY_FILTER_STATUS),
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_CYCLE_TIME),
        name=DATA_KEY_CYCLE_TIME,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    SensorEntityDescription(
        key=slugify(DATA_KEY_CYCLE_TIME_LEFT),
        name=DATA_KEY_CYCLE_TIME_LEFT,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    BinarySensorEntityDescription(
        key=slugify(DATA_KEY_AWS_BROKER),
        name=DATA_KEY_AWS_BROKER,
        icon="mdi:aws",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key=slugify(DATA_KEY_WEEKLY_SCHEDULER),
        name=DATA_KEY_WEEKLY_SCHEDULER,
    ),
]

schedules = list(calendar.day_name)
schedules.append(DATA_SECTION_DELAY)

for day in schedules:
    binary_sensor = MyDolphinPlusDailyBinarySensorEntityDescription(
        key=slugify(f"{DATA_KEY_SCHEDULE} {day}"),
        name=f"{DATA_KEY_SCHEDULE} {day.capitalize()}",
        day=day,
    )

    ENTITY_DESCRIPTIONS.append(binary_sensor)
