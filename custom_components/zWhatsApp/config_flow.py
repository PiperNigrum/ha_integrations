import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT

class WhatsAppConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

        async def async_step_user(self, user_input=None):
                errors = {}

                        if user_input is not None:
                                    return self.async_create_entry(
                                                    title="WhatsApp Client",
                                                                    data=user_input
                                                                                )

                                                                                        schema = vol.Schema({
                                                                                                    vol.Required(CONF_BASE_URL): str,
                                                                                                                vol.Required(CONF_PORT): int
                                                                                                                        })

                                                                                                                                return self.async_show_form(
                                                                                                                                            step_id="user",
                                                                                                                                                        data_schema=schema,
                                                                                                                                                                    errors=errors
                                                                                                                                                                            )
                                                                                                                                                                            