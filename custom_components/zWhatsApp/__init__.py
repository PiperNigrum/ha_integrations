from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Notify-Plattform laden
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "notify")
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "notify")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
