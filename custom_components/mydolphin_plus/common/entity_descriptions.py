import calendar
from dataclasses import dataclass

from custom_components.mydolphin_plus.common.consts import (
    CLEANING_MODES_SHORT,
    DATA_KEY_AWS_BROKER,
    DATA_KEY_CYCLE_TIME,
    DATA_KEY_CYCLE_TIME_LEFT,
    DATA_KEY_FILTER_STATUS,
    DATA_KEY_LED,
    DATA_KEY_LED_MODE,
    DATA_KEY_SCHEDULE,
    DATA_KEY_VACUUM,
    DATA_KEY_WEEKLY_SCHEDULE,
    DATA_SECTION_DELAY,
    LED_MODES_NAMES,
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
from homeassistant.components.vacuum import VacuumEntityDescription, VacuumEntityFeature
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.helpers.entity import EntityDescription


@dataclass(slots=True)
class MyDolphinPlusVacuumEntityDescription(VacuumEntityDescription):
    """A class that describes vacuum entities."""

    features: VacuumEntityFeature = VacuumEntityFeature(0)
    fan_speed_list: list[str] = ()


@dataclass(slots=True)
class MyDolphinPlusDailyBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes vacuum entities."""

    day: str | None = None


ENTITY_DESCRIPTIONS: list[EntityDescription] = [
    MyDolphinPlusVacuumEntityDescription(
        key=DATA_KEY_VACUUM,
        name="",
        features=VACUUM_FEATURES,
        fan_speed_list=list(CLEANING_MODES_SHORT.keys()),
        translation_key=DATA_KEY_VACUUM,
    ),
    LightEntityDescription(
        key=DATA_KEY_LED, name="LED Mode", entity_category=EntityCategory.CONFIG
    ),
    SelectEntityDescription(
        key=DATA_KEY_LED_MODE,
        name="LED Mode",
        options=list(LED_MODES_NAMES.keys()),
        entity_category=EntityCategory.CONFIG,
        translation_key=DATA_KEY_LED_MODE,
    ),
    SensorEntityDescription(
        key=DATA_KEY_FILTER_STATUS,
        name="Filter Status",
    ),
    SensorEntityDescription(
        key=DATA_KEY_CYCLE_TIME,
        name="Cycle Time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    SensorEntityDescription(
        key=DATA_KEY_CYCLE_TIME_LEFT,
        name="Cycle Time Left",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    BinarySensorEntityDescription(
        key=DATA_KEY_AWS_BROKER,
        name="AWS Broker",
        icon="mdi:aws",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key=DATA_KEY_WEEKLY_SCHEDULE,
        name="Weekly Scheduler",
    ),
]

schedules = list(calendar.day_name)
schedules.append(DATA_SECTION_DELAY)

for day in schedules:
    binary_sensor = MyDolphinPlusDailyBinarySensorEntityDescription(
        key=f"{DATA_KEY_SCHEDULE} {day}",
        name=f"{DATA_KEY_SCHEDULE} {day.capitalize()}",
        day=day,
    )

    ENTITY_DESCRIPTIONS.append(binary_sensor)
