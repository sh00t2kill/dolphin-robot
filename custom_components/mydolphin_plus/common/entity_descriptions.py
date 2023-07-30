from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.components.light import LightEntityDescription
from homeassistant.components.number import NumberDeviceClass, NumberEntityDescription
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
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS,
    EntityCategory,
    Platform,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityDescription
from homeassistant.util import slugify

from .clean_modes import (
    CleanModes,
    get_clean_mode_cycle_time_key,
    get_clean_mode_cycle_time_name,
)
from .consts import (
    DATA_KEY_AWS_BROKER,
    DATA_KEY_CLEAN_MODE,
    DATA_KEY_CYCLE_COUNT,
    DATA_KEY_CYCLE_TIME,
    DATA_KEY_CYCLE_TIME_LEFT,
    DATA_KEY_FILTER_STATUS,
    DATA_KEY_LED,
    DATA_KEY_LED_INTENSITY,
    DATA_KEY_LED_MODE,
    DATA_KEY_NETWORK_NAME,
    DATA_KEY_POWER_SUPPLY_STATUS,
    DATA_KEY_PWS_ERROR,
    DATA_KEY_ROBOT_ERROR,
    DATA_KEY_ROBOT_STATUS,
    DATA_KEY_ROBOT_TYPE,
    DATA_KEY_RSSI,
    DATA_KEY_STATUS,
    DATA_KEY_VACUUM,
    DYNAMIC_DESCRIPTION_TEMPERATURE,
    ICON_LED_MODES,
    VACUUM_FEATURES,
)
from .robot_family import RobotFamily


@dataclass(slots=True)
class MyDolphinPlusEntityDescription(EntityDescription):
    platform: Platform | None = None


@dataclass(slots=True)
class MyDolphinPlusVacuumEntityDescription(
    StateVacuumEntityDescription, MyDolphinPlusEntityDescription
):
    """A class that describes vacuum entities."""

    platform: Platform | None = Platform.VACUUM
    features: VacuumEntityFeature = VacuumEntityFeature(0)
    fan_speed_list: list[str] = ()


@dataclass(slots=True)
class MyDolphinPlusBinarySensorEntityDescription(
    BinarySensorEntityDescription, MyDolphinPlusEntityDescription
):
    platform: Platform | None = Platform.BINARY_SENSOR
    on_value: str | bool | None = None
    attributes: list[str] | None = None


@dataclass(slots=True)
class MyDolphinPlusSensorEntityDescription(
    SensorEntityDescription, MyDolphinPlusEntityDescription
):
    platform: Platform | None = Platform.SENSOR


@dataclass(slots=True)
class MyDolphinPlusSelectEntityDescription(
    SelectEntityDescription, MyDolphinPlusEntityDescription
):
    platform: Platform | None = Platform.SELECT


@dataclass(slots=True)
class MyDolphinPlusNumberEntityDescription(
    NumberEntityDescription, MyDolphinPlusEntityDescription
):
    platform: Platform | None = Platform.NUMBER


@dataclass(slots=True)
class MyDolphinPlusLightEntityDescription(
    LightEntityDescription, MyDolphinPlusEntityDescription
):
    platform: Platform | None = Platform.LIGHT


ENTITY_DESCRIPTIONS: dict[str, list[MyDolphinPlusEntityDescription]] = {
    RobotFamily.ALL: [
        MyDolphinPlusVacuumEntityDescription(
            key=slugify(DATA_KEY_VACUUM),
            name="",
            features=VACUUM_FEATURES,
            fan_speed_list=list(CleanModes),
            translation_key=slugify(DATA_KEY_VACUUM),
        ),
        MyDolphinPlusLightEntityDescription(
            key=slugify(DATA_KEY_LED),
            name=DATA_KEY_LED,
            entity_category=EntityCategory.CONFIG,
            translation_key=slugify(DATA_KEY_LED),
        ),
        MyDolphinPlusSelectEntityDescription(
            key=slugify(DATA_KEY_LED_MODE),
            name=DATA_KEY_LED_MODE,
            options=list(ICON_LED_MODES.keys()),
            entity_category=EntityCategory.CONFIG,
            translation_key=slugify(DATA_KEY_LED_MODE),
        ),
        MyDolphinPlusNumberEntityDescription(
            key=slugify(DATA_KEY_LED_INTENSITY),
            name=DATA_KEY_LED_INTENSITY,
            native_min_value=0,
            native_max_value=100,
            entity_category=EntityCategory.CONFIG,
            device_class=NumberDeviceClass.POWER_FACTOR,
            translation_key=slugify(DATA_KEY_LED_INTENSITY),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_STATUS),
            name=DATA_KEY_STATUS,
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key=slugify(DATA_KEY_STATUS),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_RSSI),
            name=DATA_KEY_RSSI,
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=SensorDeviceClass.SIGNAL_STRENGTH,
            native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
            translation_key=slugify(DATA_KEY_RSSI),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_NETWORK_NAME),
            name=DATA_KEY_NETWORK_NAME,
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key=slugify(DATA_KEY_NETWORK_NAME),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_CLEAN_MODE),
            name=DATA_KEY_CLEAN_MODE,
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key=slugify(DATA_KEY_CLEAN_MODE),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_POWER_SUPPLY_STATUS),
            name=DATA_KEY_POWER_SUPPLY_STATUS,
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key=slugify(DATA_KEY_POWER_SUPPLY_STATUS),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_ROBOT_STATUS),
            name=DATA_KEY_ROBOT_STATUS,
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key=slugify(DATA_KEY_ROBOT_STATUS),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_ROBOT_TYPE),
            name=DATA_KEY_ROBOT_TYPE,
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key=slugify(DATA_KEY_ROBOT_TYPE),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_CYCLE_COUNT),
            name=DATA_KEY_CYCLE_COUNT,
            entity_category=EntityCategory.DIAGNOSTIC,
            state_class=SensorStateClass.TOTAL_INCREASING,
            translation_key=slugify(DATA_KEY_CYCLE_COUNT),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_FILTER_STATUS),
            name=DATA_KEY_FILTER_STATUS,
            translation_key=slugify(DATA_KEY_FILTER_STATUS),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_CYCLE_TIME),
            name=DATA_KEY_CYCLE_TIME,
            device_class=SensorDeviceClass.DURATION,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key=slugify(DATA_KEY_CYCLE_TIME),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_CYCLE_TIME_LEFT),
            name=DATA_KEY_CYCLE_TIME_LEFT,
            device_class=SensorDeviceClass.DURATION,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            translation_key=slugify(DATA_KEY_CYCLE_TIME_LEFT),
        ),
        MyDolphinPlusBinarySensorEntityDescription(
            key=slugify(DATA_KEY_AWS_BROKER),
            name=DATA_KEY_AWS_BROKER,
            icon="mdi:aws",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key=slugify(DATA_KEY_AWS_BROKER),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_ROBOT_ERROR),
            name=DATA_KEY_ROBOT_ERROR,
            icon="mdi:robot-vacuum-variant",
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key=slugify(DATA_KEY_ROBOT_ERROR),
        ),
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DATA_KEY_PWS_ERROR),
            name=DATA_KEY_PWS_ERROR,
            icon="mdi:water-boiler",
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key=slugify(DATA_KEY_PWS_ERROR),
        ),
    ],
    RobotFamily.M700: [
        MyDolphinPlusSensorEntityDescription(
            key=slugify(DYNAMIC_DESCRIPTION_TEMPERATURE),
            name=DYNAMIC_DESCRIPTION_TEMPERATURE.capitalize(),
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            translation_key=slugify(DYNAMIC_DESCRIPTION_TEMPERATURE),
        )
    ],
}

for clean_mode in list(CleanModes):
    name = get_clean_mode_cycle_time_name(CleanModes(clean_mode))
    key = get_clean_mode_cycle_time_key(CleanModes(clean_mode))

    ed = MyDolphinPlusNumberEntityDescription(
        key=key,
        name=name,
        native_min_value=0,
        native_max_value=600,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        translation_key=key,
    )

    ENTITY_DESCRIPTIONS[RobotFamily.ALL].append(ed)

    def get_entity_descriptions(
        platform: Platform, robot_family: RobotFamily | None
    ) -> list[MyDolphinPlusEntityDescription]:
        entity_descriptions = []

        for family in ENTITY_DESCRIPTIONS:
            if family == RobotFamily.ALL or robot_family == family:
                family_entity_description = ENTITY_DESCRIPTIONS[family]
                entity_descriptions.extend(family_entity_description)

        result = [
            entity_description
            for entity_description in entity_descriptions
            if entity_description.platform == platform
        ]

        return result
