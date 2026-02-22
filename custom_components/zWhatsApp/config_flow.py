import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_PORT,
    CONF_SERVICE,
    SERVICE_SEND_MESSAGE,
    SERVICE_SEND_MEDIA,
)


class WhatsAppConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Erstinstallation."""
        if user_input is not None:
            base_data = {
                CONF_BASE_URL: user_input[CONF_BASE_URL],
                CONF_PORT: user_input[CONF_PORT],
            }

            # Entry 1: send_message
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": "import"},
                    data={**base_data, CONF_SERVICE: SERVICE_SEND_MESSAGE},
                )
            )

            # Entry 2: send_media
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": "import"},
                    data={**base_data, CONF_SERVICE: SERVICE_SEND_MEDIA},
                )
            )

            return self.async_create_entry(title="WhatsApp Client", data=base_data)

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL): str,
                vol.Required(CONF_PORT): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_import(self, user_input):
        """Erzeugt die beiden Notify‑Entries."""
        return self.async_create_entry(
            title=f"WhatsApp {user_input[CONF_SERVICE]}",
            data=user_input,
        )

    async def async_step_reconfigure(self, user_input=None):
        """Neukonfiguration."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            self.hass.config_entries.async_update_entry(entry, data=user_input)
            return self.async_abort(reason="reconfigured")

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=entry.data.get(CONF_BASE_URL)): str,
                vol.Required(CONF_PORT, default=entry.data.get(CONF_PORT)): int,
            }
        )

        return self.async_show_form(step_id="reconfigure", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WhatsAppOptionsFlow(config_entry)


class WhatsAppOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        return await self.hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reconfigure", "entry_id": self.entry.entry_id},
            data=self.entry.data,
        )
