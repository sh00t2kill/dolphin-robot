"""Integration information handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from homeassistant.loader import async_get_integration

_LOGGER = logging.getLogger(__name__)


class IntegrationInfo:
    """Handles integration name and version information."""

    _instance: IntegrationInfo | None = None
    _name: str | None = None
    _version: str | None = None
    _user_agent: str | None = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern - return the same instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self, hass: HomeAssistant | None) -> None:
        """Initialize integration info from manifest, cached at instance level."""
        if self._initialized:
            return  # Already initialized

        name = "unknown"
        version = "unknown"
        user_agent = "unknown"
        is_initialized = False

        if hass is not None:
            try:
                integration = await async_get_integration(hass, "mydolphin_plus")
                name = integration.name
                version = integration.version
                clean_name = name.replace(" ", "-")
                user_agent = f"HA-{clean_name}/{version}"
                is_initialized = True
            except Exception as ex:
                _LOGGER.warning(f"Failed to get integration info: {ex}")

        self._name = name
        self._version = version
        self._user_agent = user_agent
        self._initialized = is_initialized

    def get_version(self) -> str | None:
        """Get integration version."""
        return self._version

    def set_user_agent(self, headers: dict) -> None:
        """Set User-Agent header if name and version are available.

        Args:
            headers: Headers dict to modify. Will set User-Agent if name/version are valid.
        """
        if self._initialized:
            headers["User-Agent"] = self._user_agent
