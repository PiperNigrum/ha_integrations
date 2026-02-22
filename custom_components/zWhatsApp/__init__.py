from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up WhatsApp integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Neue HA API: forward_entry_setups erwartet eine LISTE
    await hass.config_entries.async_forward_entry_setups(entry, ["notify"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload WhatsApp integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["notify"])

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
