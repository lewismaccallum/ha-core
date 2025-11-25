"""Common fixtures for the Toshiba AC tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.toshiba_ac.const import (
    CONF_ACCESS_TOKEN,
    CONF_BRAND_ID,
    CONF_CONSUMER_ID,
    CONF_CONSUMER_MASTER_ID,
    DOMAIN,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

TEST_USERNAME = "test@example.com"
TEST_PASSWORD = "testpassword123"
TEST_BRAND_ID = "test-brand-id"
TEST_ACCESS_TOKEN = "test-access-token"
TEST_CONSUMER_ID = "test-consumer-id"
TEST_CONSUMER_MASTER_ID = "test-consumer-master-id"

TEST_DEVICE_AC_ID = "12345"
TEST_DEVICE_NAME = "Living Room AC"
TEST_DEVICE_UNIQUE_ID = "unique-12345"
TEST_DEVICE_MODEL = "RAS-XXX"

# Sample raw payload: ON, COOL, 22°C, AUTO fan, SWING off, POWER 100%
TEST_RAW_PAYLOAD = "30" + "42" + "16" + "41" + "31" + "64" + "00" * 8 + "10"


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_USERNAME.lower(),
        data={
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_BRAND_ID: TEST_BRAND_ID,
            CONF_ACCESS_TOKEN: TEST_ACCESS_TOKEN,
            CONF_CONSUMER_ID: TEST_CONSUMER_ID,
            CONF_CONSUMER_MASTER_ID: TEST_CONSUMER_MASTER_ID,
        },
    )


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.toshiba_ac.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_toshiba_client() -> Generator[AsyncMock]:
    """Create a mock Toshiba AC API client."""
    with (
        patch(
            "homeassistant.components.toshiba_ac.ToshibaAcClient", autospec=True
        ) as mock_client_class,
        patch(
            "homeassistant.components.toshiba_ac.config_flow.ToshibaAcClient",
            autospec=True,
        ) as mock_config_flow_client_class,
    ):
        mock_client = mock_client_class.return_value
        mock_config_flow_client = mock_config_flow_client_class.return_value

        # Setup login response
        mock_client.async_login.return_value = {
            "access_token": TEST_ACCESS_TOKEN,
            "consumer_id": TEST_CONSUMER_ID,
            "consumer_master_id": TEST_CONSUMER_MASTER_ID,
        }
        mock_config_flow_client.async_login.return_value = {
            "access_token": TEST_ACCESS_TOKEN,
            "consumer_id": TEST_CONSUMER_ID,
            "consumer_master_id": TEST_CONSUMER_MASTER_ID,
        }

        yield mock_config_flow_client
