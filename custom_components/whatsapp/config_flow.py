import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT


class WhatsAppConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Erstinstallation oder Neukonfiguration."""
        errors = {}

        # Wenn bereits ein Eintrag existiert → Werte vorausfüllen
        existing_entry = None
        for entry in self._async_current_entries():
            existing_entry = entry
            break

        if user_input is not None:
            # Wenn es einen Eintrag gibt → aktualisieren
            if existing_entry:
                self.hass.config_entries.async_update_entry(existing_entry, data=user_input)
                return self.async_abort(reason="reconfigured")

            # Sonst neuen Eintrag erzeugen
            return self.async_create_entry(
                title="WhatsApp Client",
                data=user_input
            )

        # Defaults setzen
        defaults = {}
        if existing_entry:
            defaults = existing_entry.data

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default=defaults.get(CONF_BASE_URL, "")): str,
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, 3000)): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )
