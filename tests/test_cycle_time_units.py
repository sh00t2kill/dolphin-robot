"""Cycle Time Left shows hours on older entities."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mydolphin_plus import _set_suggested_time_units
from custom_components.mydolphin_plus.common.consts import DOMAIN
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

pytest_plugins = "pytest_homeassistant_custom_component"


def _sensor(
    entity_registry: er.EntityRegistry,
    entry: MockConfigEntry,
    translation_key: str,
    unit: str,
) -> er.RegistryEntry:
    return entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        translation_key,
        config_entry=entry,
        translation_key=translation_key,
        unit_of_measurement=unit,
    )


async def test_cycle_time_left_gets_suggested_unit(hass: HomeAssistant) -> None:
    """The sensor changes unit and keeps its other options."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    entity_registry = er.async_get(hass)

    time_left = _sensor(entity_registry, entry, "cycle_time_left", UnitOfTime.SECONDS)
    entity_registry.async_update_entity_options(
        time_left.entity_id, "sensor", {"suggested_display_precision": 3}
    )
    cycle_count = _sensor(entity_registry, entry, "cycle_count", "")

    _set_suggested_time_units(hass, entry)

    time_left = entity_registry.async_get(time_left.entity_id)
    cycle_count = entity_registry.async_get(cycle_count.entity_id)

    assert time_left.options["sensor"] == {
        "suggested_display_precision": 3,
        "unit_of_measurement": UnitOfTime.HOURS,
    }
    assert "sensor" not in cycle_count.options


async def test_cycle_time_left_keeps_user_unit(hass: HomeAssistant) -> None:
    """A unit the user already picked stays."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    entity_registry = er.async_get(hass)

    time_left = _sensor(entity_registry, entry, "cycle_time_left", UnitOfTime.SECONDS)
    entity_registry.async_update_entity_options(
        time_left.entity_id, "sensor", {"unit_of_measurement": UnitOfTime.MINUTES}
    )

    _set_suggested_time_units(hass, entry)

    time_left = entity_registry.async_get(time_left.entity_id)

    assert time_left.options["sensor"]["unit_of_measurement"] == UnitOfTime.MINUTES
