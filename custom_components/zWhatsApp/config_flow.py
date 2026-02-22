import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT

class WhatsAppConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Erstinstallation."""
        if user_input is not None:
            return self.async_create_entry(
                title="WhatsApp Client",
                data=user_input
            )

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL): str,
            vol.Required(CONF_PORT): int
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_reconfigure(self, user_input=None):
        """Neukonfiguration ohne Löschen."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            self.hass.config_entries.async_update_entry(entry, data=user_input)
            return self.async_abort(reason="reconfigured")

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default=entry.data.get(CONF_BASE_URL)): str,
            vol.Required(CONF_PORT, default=entry.data.get(CONF_PORT)): int
        })

        return self.async_show_form(step_id="reconfigure", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WhatsAppOptionsFlow(config_entry)


class WhatsAppOptionsFlow(config_entries.OptionsFlow):
    """Damit HA den Button 'Konfigurieren' anzeigt."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reconfigure", "entry_id": self.config_entry.entry_id},
            data=self.config_entry.data
        )
