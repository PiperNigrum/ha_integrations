import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT


class WhatsAppConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Erstinstallation oder Neukonfiguration."""
        errors = {}

        # Prüfen, ob es schon einen Eintrag gibt
        existing_entry = next(iter(self._async_current_entries()), None)

        if user_input is not None:
            if existing_entry:
                # Bestehenden Eintrag aktualisieren
                self.hass.config_entries.async_update_entry(
                    existing_entry, data=user_input
                )
                return self.async_abort(reason="reconfigured")

            # Neuen Eintrag anlegen
            return self.async_create_entry(
                title="WhatsApp Client",
                data=user_input,
            )

        defaults = existing_entry.data if existing_entry else {}

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=defaults.get(CONF_BASE_URL, "")): str,
                vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, 3000)): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
