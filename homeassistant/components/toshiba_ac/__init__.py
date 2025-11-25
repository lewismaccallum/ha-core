"""The Toshiba AC integration."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .api import (
    ToshibaAcApiError,
    ToshibaAcAuthError,
    ToshibaAcClient,
    ToshibaAcConnectionError,
)
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_BRAND_ID,
    CONF_CONSUMER_ID,
    CONF_CONSUMER_MASTER_ID,
)
from .coordinator import ToshibaAcConfigEntry, ToshibaAcCoordinator

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ToshibaAcConfigEntry) -> bool:
    """Set up Toshiba AC from a config entry."""
    session = aiohttp_client.async_get_clientsession(hass)
    client = ToshibaAcClient(session)

    # Set stored credentials
    client.set_credentials(
        access_token=entry.data[CONF_ACCESS_TOKEN],
        consumer_id=entry.data[CONF_CONSUMER_ID],
        consumer_master_id=entry.data[CONF_CONSUMER_MASTER_ID],
    )

    # If tokens are expired, re-login
    try:
        await client.async_get_devices()
    except (ToshibaAcAuthError, ToshibaAcConnectionError, ToshibaAcApiError):
        # Token may be expired, try to re-login
        await client.async_login(
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.data[CONF_BRAND_ID],
        )

    coordinator = ToshibaAcCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ToshibaAcConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
