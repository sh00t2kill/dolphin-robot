"""The power supply and robot devices take their details from the API and shadow."""

from __future__ import annotations

from types import SimpleNamespace

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mydolphin_plus.common.base_entity import MyDolphinPlusBaseEntity
from custom_components.mydolphin_plus.common.consts import (
    DATA_KEY_RSSI,
    DATA_KEY_VACUUM,
    DEFAULT_NAME,
    DOMAIN,
)
from custom_components.mydolphin_plus.common.entity_descriptions import (
    ENTITY_DESCRIPTIONS,
    MyDolphinPlusEntityDescription,
)
from custom_components.mydolphin_plus.managers.coordinator import (
    MyDolphinPlusCoordinator,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.util import slugify

pytest_plugins = "pytest_homeassistant_custom_component"

SERIAL = "serial"
ROBOT = {(DEFAULT_NAME, SERIAL)}
POWER_SUPPLY = {(DEFAULT_NAME, f"{SERIAL}_power_supply")}

LOGIN = {"Robot Name": "Willy"}
DETAILS = {
    **LOGIN,
    "Product Name": "99996291-PR2AU",
    "Product Description": "DOLPHIN PREMIUM 2000 AU",
}

SHADOW = {
    "systemState": {"robotType": "S4"},
    "versions": {
        "pwsVersion": {"pwsHwVersion": "00", "pwsSwVersion": "11.0004"},
        "robotVersion": {"muHwVersion": "02", "muSwVersion": "9DE1"},
    },
}


def _coordinator(
    hass: HomeAssistant,
    api_data: dict,
    aws_data: dict,
    entry: MockConfigEntry | None = None,
) -> MyDolphinPlusCoordinator:
    coordinator = MyDolphinPlusCoordinator.__new__(MyDolphinPlusCoordinator)
    coordinator.hass = hass
    coordinator._api = SimpleNamespace(data=api_data)
    coordinator._aws_client = SimpleNamespace(data=aws_data)
    coordinator._config_manager = SimpleNamespace(
        serial_number=SERIAL,
        entry=entry,
        get_entity_name=lambda description, device_info: (
            f"{device_info['name']} {description.name}"
        ),
    )

    return coordinator


def _description(key: str) -> MyDolphinPlusEntityDescription:
    return next(d for d in ENTITY_DESCRIPTIONS if d.key == slugify(key))


def test_devices_before_details(hass: HomeAssistant) -> None:
    """Before the details and shadow load the product and versions are unknown."""
    coordinator = _coordinator(hass, LOGIN, {})

    assert coordinator.get_device()["model"] is None
    assert coordinator.get_device()["model_id"] is None
    assert coordinator.get_device()["sw_version"] is None
    assert coordinator.get_power_supply_device()["sw_version"] is None


def test_devices_from_details(hass: HomeAssistant) -> None:
    """Each device gets its own versions; the robot links to the power supply."""
    coordinator = _coordinator(hass, DETAILS, SHADOW)

    robot = coordinator.get_device()
    assert robot["identifiers"] == ROBOT
    assert robot["model"] == "DOLPHIN PREMIUM 2000 AU"
    assert robot["model_id"] == "99996291-PR2AU"
    assert robot["sw_version"] == "9DE1"
    assert robot["hw_version"] == "S4"
    assert robot["serial_number"] == SERIAL
    assert robot["via_device"] == next(iter(POWER_SUPPLY))

    power_supply = coordinator.get_power_supply_device()
    assert power_supply["identifiers"] == POWER_SUPPLY
    assert power_supply["name"] == "Willy Power Supply"
    assert power_supply["sw_version"] == "11.0004"
    assert power_supply["model"] == "Power Supply"
    assert power_supply["hw_version"] is None


async def test_device_registry_updated(hass: HomeAssistant) -> None:
    """Devices made before the details loaded get linked and get them later."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    device_registry = dr.async_get(hass)

    coordinator = _coordinator(hass, LOGIN, {}, entry)
    coordinator._create_power_supply_device()
    robot = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, **coordinator.get_device()
    )

    _coordinator(hass, DETAILS, SHADOW, entry)._update_device_registry()

    power_supply = device_registry.async_get_device(identifiers=POWER_SUPPLY)
    robot = device_registry.async_get(robot.id)

    assert robot.via_device_id == power_supply.id
    assert robot.model == "DOLPHIN PREMIUM 2000 AU"
    assert robot.model_id == "99996291-PR2AU"
    assert robot.sw_version == "9DE1"
    assert robot.hw_version == "S4"
    assert power_supply.sw_version == "11.0004"


def test_power_supply_entity_keeps_its_ids(hass: HomeAssistant) -> None:
    """Moving an entity to the power supply keeps its name and unique ID."""
    coordinator = _coordinator(hass, DETAILS, SHADOW)

    rssi = MyDolphinPlusBaseEntity(_description(DATA_KEY_RSSI), coordinator)
    vacuum = MyDolphinPlusBaseEntity(_description(DATA_KEY_VACUUM), coordinator)

    assert rssi.device_info["identifiers"] == POWER_SUPPLY
    assert rssi.name == "Willy RSSI"
    assert rssi.unique_id == "sensor_serial_willy_rssi"
    assert vacuum.device_info["identifiers"] == ROBOT
