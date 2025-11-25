"""Test the Toshiba AC climate entity."""

from unittest.mock import patch

from homeassistant.components.climate import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_SWING_MODE,
    DOMAIN as CLIMATE_DOMAIN,
    FAN_HIGH,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_SWING_MODE,
    SERVICE_SET_TEMPERATURE,
    SWING_ON,
    HVACMode,
)
from homeassistant.components.toshiba_ac.api import ToshibaAcDevice, ToshibaAcState
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
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


def _create_mock_state(
    is_on: bool = True,
    mode: str = "cool",
    temperature: int = 22,
    fan_speed: str = "auto",
    swing: str = "off",
) -> ToshibaAcState:
    """Create a mock state."""
    return ToshibaAcState(
        ac_id=TEST_DEVICE_AC_ID,
        is_on=is_on,
        mode=mode,
        temperature=temperature,
        fan_speed=fan_speed,
        swing=swing,
        power_level="100",
        self_cleaning=False,
        raw_payload=TEST_RAW_PAYLOAD,
    )


async def test_climate_entity_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test climate entity setup."""
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

        # Verify climate entity exists
        entity_id = f"climate.{TEST_DEVICE_NAME.lower().replace(' ', '_')}"
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == HVACMode.COOL


async def test_climate_hvac_modes(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test climate HVAC mode changes."""
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

        entity_id = f"climate.{TEST_DEVICE_NAME.lower().replace(' ', '_')}"

        # Test setting HVAC mode to heat
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
        mock_client.async_send_command.assert_called()


async def test_climate_temperature(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test climate temperature changes."""
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

        entity_id = f"climate.{TEST_DEVICE_NAME.lower().replace(' ', '_')}"

        # Test setting temperature
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 24},
            blocking=True,
        )
        mock_client.async_send_command.assert_called()


async def test_climate_fan_mode(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test climate fan mode changes."""
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

        entity_id = f"climate.{TEST_DEVICE_NAME.lower().replace(' ', '_')}"

        # Test setting fan mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: entity_id, ATTR_FAN_MODE: FAN_HIGH},
            blocking=True,
        )
        mock_client.async_send_command.assert_called()


async def test_climate_swing_mode(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test climate swing mode changes."""
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

        entity_id = f"climate.{TEST_DEVICE_NAME.lower().replace(' ', '_')}"

        # Test setting swing mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_SWING_MODE,
            {ATTR_ENTITY_ID: entity_id, ATTR_SWING_MODE: SWING_ON},
            blocking=True,
        )
        mock_client.async_send_command.assert_called()


async def test_climate_off_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test climate entity when AC is off."""
    mock_device = _create_mock_device()
    mock_state = _create_mock_state(is_on=False)

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

        entity_id = f"climate.{TEST_DEVICE_NAME.lower().replace(' ', '_')}"
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == HVACMode.OFF
