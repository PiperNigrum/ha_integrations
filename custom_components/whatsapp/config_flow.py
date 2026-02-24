from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT, DEFAULT_PORT


class WhatsAppConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="WhatsApp",
                data=user_input
            )

        schema = vol.Schema({
            vol.Required(
                CONF_BASE_URL,
                description="Host / Base URL"
            ): str,
            vol.Required(
                CONF_PORT,
                default=DEFAULT_PORT,
                description="Port"
            ): int,
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WhatsAppOptionsFlow(config_entry)


class WhatsAppOptionsFlow(config_entries.OptionsFlow):
    """Handle options after setup."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.data
        options = self.config_entry.options

        schema = vol.Schema({
            vol.Required(
                CONF_BASE_URL,
                default=options.get(CONF_BASE_URL, data.get(CONF_BASE_URL)),
                description="Host / Base URL"
            ): str,
            vol.Required(
                CONF_PORT,
                default=options.get(CONF_PORT, data.get(CONF_PORT, DEFAULT_PORT)),
                description="Port"
            ): int,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
