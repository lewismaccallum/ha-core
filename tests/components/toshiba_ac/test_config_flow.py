"""Test the Toshiba AC config flow."""

from unittest.mock import AsyncMock

import pytest

from homeassistant.components.toshiba_ac.api import (
    ToshibaAcAuthError,
    ToshibaAcConnectionError,
)
from homeassistant.components.toshiba_ac.const import (
    CONF_ACCESS_TOKEN,
    CONF_BRAND_ID,
    CONF_CONSUMER_ID,
    CONF_CONSUMER_MASTER_ID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import (
    TEST_ACCESS_TOKEN,
    TEST_BRAND_ID,
    TEST_CONSUMER_ID,
    TEST_CONSUMER_MASTER_ID,
    TEST_PASSWORD,
    TEST_USERNAME,
)

from tests.common import MockConfigEntry


async def test_user_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_toshiba_client: AsyncMock,
) -> None:
    """Test successful user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_BRAND_ID: TEST_BRAND_ID,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Toshiba AC ({TEST_USERNAME})"
    assert result["data"] == {
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_BRAND_ID: TEST_BRAND_ID,
        CONF_ACCESS_TOKEN: TEST_ACCESS_TOKEN,
        CONF_CONSUMER_ID: TEST_CONSUMER_ID,
        CONF_CONSUMER_MASTER_ID: TEST_CONSUMER_MASTER_ID,
    }


async def test_user_flow_already_configured(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_toshiba_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that duplicate accounts are rejected."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_BRAND_ID: TEST_BRAND_ID,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    ("exception", "error_key"),
    [
        (ToshibaAcAuthError("Invalid credentials"), "invalid_auth"),
        (ToshibaAcConnectionError("Connection failed"), "cannot_connect"),
        (Exception("Unknown error"), "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_toshiba_client: AsyncMock,
    exception: Exception,
    error_key: str,
) -> None:
    """Test error handling in user config flow."""
    mock_toshiba_client.async_login.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_BRAND_ID: TEST_BRAND_ID,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error_key}

    # Verify recovery after error
    mock_toshiba_client.async_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_BRAND_ID: TEST_BRAND_ID,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_reauth_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_toshiba_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful reauthentication flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    new_password = "new-password"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: new_password,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_PASSWORD] == new_password


@pytest.mark.parametrize(
    ("exception", "error_key"),
    [
        (ToshibaAcAuthError("Invalid credentials"), "invalid_auth"),
        (ToshibaAcConnectionError("Connection failed"), "cannot_connect"),
        (Exception("Unknown error"), "unknown"),
    ],
)
async def test_reauth_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_toshiba_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    error_key: str,
) -> None:
    """Test error handling in reauthentication flow."""
    mock_config_entry.add_to_hass(hass)
    mock_toshiba_client.async_login.side_effect = exception

    result = await mock_config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "new-password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": error_key}

    # Verify recovery after error
    mock_toshiba_client.async_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "new-password",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
