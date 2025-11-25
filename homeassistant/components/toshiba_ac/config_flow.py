"""Config flow for Toshiba AC integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import aiohttp_client

from .api import ToshibaAcAuthError, ToshibaAcClient, ToshibaAcConnectionError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_BRAND_ID,
    CONF_CONSUMER_ID,
    CONF_CONSUMER_MASTER_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_BRAND_ID): str,
    }
)


class ToshibaAcConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Toshiba AC."""

    VERSION = 1
    MINOR_VERSION = 1

    async def _async_validate_credentials(
        self, user_input: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, str] | None]:
        """Validate credentials and return errors and API tokens."""
        errors: dict[str, str] = {}
        tokens: dict[str, str] | None = None

        session = aiohttp_client.async_get_clientsession(self.hass)
        client = ToshibaAcClient(session)

        try:
            result = await client.async_login(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_BRAND_ID],
            )
            tokens = {
                CONF_ACCESS_TOKEN: result["access_token"],
                CONF_CONSUMER_ID: result["consumer_id"],
                CONF_CONSUMER_MASTER_ID: result["consumer_master_id"],
            }
        except ToshibaAcAuthError:
            errors["base"] = "invalid_auth"
        except ToshibaAcConnectionError:
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return errors, tokens

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()

            errors, tokens = await self._async_validate_credentials(user_input)

            if not errors and tokens:
                return self.async_create_entry(
                    title=f"Toshiba AC ({user_input[CONF_USERNAME]})",
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_BRAND_ID: user_input[CONF_BRAND_ID],
                        **tokens,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthentication confirmation."""
        errors: dict[str, str] = {}

        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            combined_input = {
                CONF_USERNAME: reauth_entry.data[CONF_USERNAME],
                CONF_BRAND_ID: reauth_entry.data[CONF_BRAND_ID],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }
            errors, tokens = await self._async_validate_credentials(combined_input)

            if not errors and tokens:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        **tokens,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={
                CONF_USERNAME: reauth_entry.data[CONF_USERNAME],
            },
            errors=errors,
        )
