from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = entry.data

    # WhatsApp.send_message
    async def handle_send_message(call: ServiceCall):
        await hass.services.async_call(
            "notify",
            "whatsapp_send_message",
            {
                "message": call.data.get("message"),
                "title": call.data.get("title", ""),
            },
            blocking=True,
        )

    hass.services.async_register(
        DOMAIN,
        "send_message",
        handle_send_message,
    )

    # WhatsApp.send_media
    async def handle_send_media(call: ServiceCall):
        await hass.services.async_call(
            "notify",
            "whatsapp_send_media",
            {
                "message": call.data.get("caption", ""),
                "data": {
                    "url": call.data.get("url"),
                    "sendMediaAsDocument": call.data.get("sendMediaAsDocument", False),
                    "sendAudioAsVoice": call.data.get("sendAudioAsVoice", False),
                    "sendVideoAsGif": call.data.get("sendVideoAsGif", False),
                    "sendMediaAsSticker": call.data.get("sendMediaAsSticker", False),
                    "sendMediaAsHd": call.data.get("sendMediaAsHd", False),
                    "isViewOnce": call.data.get("isViewOnce", False),
                    "linkPreview": call.data.get("linkPreview", False),
                }
            },
            blocking=True,
        )

    hass.services.async_register(
        DOMAIN,
        "send_media",
        handle_send_media,
    )

    # Notify-Plattform laden
    await hass.config_entries.async_forward_entry_setups(entry, ["notify"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["notify"])
    return unload_ok
