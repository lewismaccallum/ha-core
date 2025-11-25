"""Coordinator for Toshiba AC integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ToshibaAcApiError,
    ToshibaAcAuthError,
    ToshibaAcClient,
    ToshibaAcConnectionError,
    ToshibaAcDevice,
    ToshibaAcState,
)
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type ToshibaAcConfigEntry = ConfigEntry[ToshibaAcCoordinator]


class ToshibaAcCoordinator(DataUpdateCoordinator[dict[str, ToshibaAcState]]):
    """Coordinator for Toshiba AC integration."""

    config_entry: ToshibaAcConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ToshibaAcConfigEntry,
        client: ToshibaAcClient,
    ) -> None:
        """Initialize coordinator for Toshiba AC integration."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self.devices: dict[str, ToshibaAcDevice] = {}

    async def _async_setup(self) -> None:
        """Discover devices during coordinator setup."""
        try:
            device_list = await self.client.async_get_devices()
        except ToshibaAcAuthError as err:
            raise ConfigEntryAuthFailed(
                "Authentication failed for Toshiba AC API"
            ) from err
        except (ToshibaAcConnectionError, ToshibaAcApiError) as err:
            raise UpdateFailed(f"Error connecting to Toshiba AC API: {err}") from err

        self.devices = {device.ac_id: device for device in device_list}

    async def _async_update_data(self) -> dict[str, ToshibaAcState]:
        """Fetch data from API endpoint."""
        states: dict[str, ToshibaAcState] = {}

        # Refresh device list if empty
        if not self.devices:
            try:
                device_list = await self.client.async_get_devices()
                self.devices = {device.ac_id: device for device in device_list}
            except ToshibaAcAuthError as err:
                raise ConfigEntryAuthFailed(
                    "Authentication failed for Toshiba AC API"
                ) from err
            except (ToshibaAcConnectionError, ToshibaAcApiError) as err:
                raise UpdateFailed(
                    f"Error connecting to Toshiba AC API: {err}"
                ) from err

        # Get state for each device
        for ac_id in self.devices:
            try:
                state = await self.client.async_get_device_state(ac_id)
                states[ac_id] = state
            except ToshibaAcAuthError as err:
                raise ConfigEntryAuthFailed(
                    "Authentication failed for Toshiba AC API"
                ) from err
            except (ToshibaAcConnectionError, ToshibaAcApiError) as err:
                _LOGGER.warning("Error getting state for device %s: %s", ac_id, err)
                # Continue with other devices even if one fails

        return states
