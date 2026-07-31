"""Regression tests for stable MyDolphin Plus entity identities."""

from types import SimpleNamespace

from homeassistant.const import Platform

from custom_components.mydolphin_plus.common.base_entity import (
    _legacy_unique_id,
)
from homeassistant.util import slugify


def test_unique_id_uses_the_raw_legacy_robot_name():
    """Correcting a display name must not change an existing identity."""
    description = SimpleNamespace(platform=Platform.LIGHT, key="led")

    assert _legacy_unique_id(
        description, "Y4708NMP4L", "CafÃ© LED"
    ) == slugify("light_Y4708NMP4L_CafÃ© LED")
