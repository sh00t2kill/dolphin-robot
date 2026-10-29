"""Button to request a fresh pool water temperature reading."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import MyDolphinPlusBaseEntity, async_setup_entities
from .common.consts import SIGNAL_DEVICE_NEW


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    @callback
    def _async_device_new(entry_id: str) -> None:
        if entry.entry_id == entry_id:
            async_setup_entities(
                hass,
                entry,
                Platform.BUTTON,
                MyDolphinPlusTemperatureButton,
                async_add_entities,
            )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class MyDolphinPlusTemperatureButton(MyDolphinPlusBaseEntity, ButtonEntity):
    """Request a new temperature reading without starting the cleaner."""

    async def async_press(self) -> None:
        await self._local_coordinator.async_request_temperature()

    @callback
    def _handle_coordinator_update(self) -> None:
        """The button has no state to copy from the coordinator."""
