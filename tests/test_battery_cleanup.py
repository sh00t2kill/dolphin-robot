"""Removal of the battery sensor that older versions created."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mydolphin_plus import _remove_battery_entity
from custom_components.mydolphin_plus.common.consts import DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

pytest_plugins = "pytest_homeassistant_custom_component"


async def test_removes_battery_sensor_only(hass: HomeAssistant) -> None:
    """Only the battery sensor goes; other sensors stay."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    entity_registry = er.async_get(hass)

    battery = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "sensor_serial_robot_battery",
        config_entry=entry,
        original_device_class=SensorDeviceClass.BATTERY,
    )
    rssi = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "sensor_serial_robot_rssi",
        config_entry=entry,
        original_device_class=SensorDeviceClass.SIGNAL_STRENGTH,
    )

    _remove_battery_entity(hass, entry)

    assert entity_registry.async_get(battery.entity_id) is None
    assert entity_registry.async_get(rssi.entity_id) is not None
