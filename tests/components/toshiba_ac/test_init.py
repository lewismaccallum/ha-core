"""Test the Toshiba AC init."""

from unittest.mock import patch

from homeassistant.components.toshiba_ac.api import (
    ToshibaAcAuthError,
    ToshibaAcDevice,
    ToshibaAcState,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .conftest import (
    TEST_ACCESS_TOKEN,
    TEST_CONSUMER_ID,
    TEST_CONSUMER_MASTER_ID,
    TEST_DEVICE_AC_ID,
    TEST_DEVICE_MODEL,
    TEST_DEVICE_NAME,
    TEST_DEVICE_UNIQUE_ID,
    TEST_RAW_PAYLOAD,
)

from tests.common import MockConfigEntry


def _create_mock_device() -> ToshibaAcDevice:
    """Create a mock device."""
    return ToshibaAcDevice(
        ac_id=TEST_DEVICE_AC_ID,
        name=TEST_DEVICE_NAME,
        device_unique_id=TEST_DEVICE_UNIQUE_ID,
        model=TEST_DEVICE_MODEL,
    )


def _create_mock_state() -> ToshibaAcState:
    """Create a mock state."""
    return ToshibaAcState(
        ac_id=TEST_DEVICE_AC_ID,
        is_on=True,
        mode="cool",
        temperature=22,
        fan_speed="auto",
        swing="off",
        power_level="100",
        self_cleaning=False,
        raw_payload=TEST_RAW_PAYLOAD,
    )


async def test_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful setup of config entry."""
    mock_device = _create_mock_device()
    mock_state = _create_mock_state()

    with patch(
        "homeassistant.components.toshiba_ac.ToshibaAcClient", autospec=True
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.async_get_devices.return_value = [mock_device]
        mock_client.async_get_device_state.return_value = mock_state
        mock_client.access_token = TEST_ACCESS_TOKEN
        mock_client.consumer_id = TEST_CONSUMER_ID
        mock_client.consumer_master_id = TEST_CONSUMER_MASTER_ID

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.LOADED


async def test_setup_entry_auth_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test setup fails with auth error."""
    with patch(
        "homeassistant.components.toshiba_ac.ToshibaAcClient", autospec=True
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.async_get_devices.side_effect = ToshibaAcAuthError("Token expired")
        mock_client.async_login.side_effect = ToshibaAcAuthError("Invalid credentials")

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful unload of config entry."""
    mock_device = _create_mock_device()
    mock_state = _create_mock_state()

    with patch(
        "homeassistant.components.toshiba_ac.ToshibaAcClient", autospec=True
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.async_get_devices.return_value = [mock_device]
        mock_client.async_get_device_state.return_value = mock_state
        mock_client.access_token = TEST_ACCESS_TOKEN
        mock_client.consumer_id = TEST_CONSUMER_ID
        mock_client.consumer_master_id = TEST_CONSUMER_MASTER_ID

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.LOADED

        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
