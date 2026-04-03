from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_BASE_URL, CONF_PORT, CONF_API_KEY, DEFAULT_PORT


def _normalize_url(url: str) -> str:
    """Ergänzt https:// falls kein Schema angegeben ist."""
    url = url.strip().rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"
    return url


class WhatsAppConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            user_input[CONF_BASE_URL] = _normalize_url(user_input[CONF_BASE_URL])
            return self.async_create_entry(
                title="WhatsApp",
                data=user_input
            )
        schema = vol.Schema({
            vol.Required(CONF_BASE_URL): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_API_KEY): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_reconfigure(self, user_input=None):
        """Ermöglicht das Neukonfigurieren eines bestehenden Eintrags."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            user_input[CONF_BASE_URL] = _normalize_url(user_input[CONF_BASE_URL])
            return self.async_update_reload_and_abort(
                entry,
                data_updates=user_input,
            )
        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default=entry.data.get(CONF_BASE_URL, "")): str,
            vol.Required(CONF_PORT, default=entry.data.get(CONF_PORT, DEFAULT_PORT)): int,
            vol.Required(CONF_API_KEY, default=entry.data.get(CONF_API_KEY, "")): str,
        })
        return self.async_show_form(step_id="reconfigure", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "WhatsAppOptionsFlow":
        return WhatsAppOptionsFlow()


class WhatsAppOptionsFlow(config_entries.OptionsFlow):
    # Kein __init__ – config_entry ist bereits in der Basisklasse verfügbar (ab HA 2025.12 Pflicht)

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            user_input[CONF_BASE_URL] = _normalize_url(user_input[CONF_BASE_URL])
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.data
        options = self.config_entry.options or {}
        schema = vol.Schema({
            vol.Required(
                CONF_BASE_URL,
                default=options.get(CONF_BASE_URL, data.get(CONF_BASE_URL))
            ): str,
            vol.Required(
                CONF_PORT,
                default=options.get(CONF_PORT, data.get(CONF_PORT, DEFAULT_PORT))
            ): int,
            vol.Optional(
                CONF_API_KEY,
                default=options.get(CONF_API_KEY, data.get(CONF_API_KEY, ""))
            ): str,
        })
        return self.async_show_form(step_id="init", data_schema=schema)