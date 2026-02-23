from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up WhatsApp from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Notify-Plattform laden
    await hass.config_entries.async_forward_entry_setups(entry, ["notify"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload WhatsApp config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["notify"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
