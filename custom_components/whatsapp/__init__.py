from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_NOTIFY_SERVICE_MESSAGE = "whatsapp_send_message"
_NOTIFY_SERVICE_MEDIA = "whatsapp_send_media"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WhatsApp integration from a config entry and forward notify platform."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = entry.data

    # Load the notify platform (notify.py) so it can register the notify wrappers.
    await hass.config_entries.async_forward_entry_setups(entry, ["notify"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry, unload platforms and remove registered services."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["notify"])

    # Remove notify wrapper services if they were registered
    try:
        hass.services.async_remove("notify", _NOTIFY_SERVICE_MESSAGE)
    except Exception:
        pass

    try:
        hass.services.async_remove("notify", _NOTIFY_SERVICE_MEDIA)
    except Exception:
        pass

    # Clean up stored data
    hass.data.get(DOMAIN, {}).pop("config", None)
    hass.data.get(DOMAIN, {}).pop("notify_registered", None)

    return unload_ok
