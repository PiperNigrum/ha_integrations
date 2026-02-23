from typing import Dict, Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT

_NOTIFY_SERVICE_MESSAGE = "whatsapp_send_message"
_NOTIFY_SERVICE_MEDIA = "whatsapp_send_media"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the WhatsApp integration from a config entry.

    This registers two notify.* wrapper services that forward to the existing
    whatsapp.* services. Only registers services once and keeps track of what
    was registered so we can remove them on unload.
    """
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = entry.data

    # Keep track of services we registered so we can remove them on unload
    registered = hass.data[DOMAIN].setdefault("registered_services", [])

    # Handler: notify.whatsapp_send_message -> whatsapp.send_message
    async def _handle_notify_send_message(call: ServiceCall) -> None:
        payload: Dict[str, Any] = {
            "chat_id": call.data.get("chat_id"),
            "message": call.data.get("message"),
            "title": call.data.get("title"),
        }
        # remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        await hass.services.async_call(
            "whatsapp",
            "send_message",
            payload,
            blocking=True,
        )

    # Handler: notify.whatsapp_send_media -> whatsapp.send_media
    async def _handle_notify_send_media(call: ServiceCall) -> None:
        payload: Dict[str, Any] = {
            "chat_id": call.data.get("chat_id"),
            "url": call.data.get("url"),
            "caption": call.data.get("caption", call.data.get("message", "")),
            "sendMediaAsDocument": call.data.get("sendMediaAsDocument", False),
            "sendAudioAsVoice": call.data.get("sendAudioAsVoice", False),
            "sendVideoAsGif": call.data.get("sendVideoAsGif", False),
            "sendMediaAsSticker": call.data.get("sendMediaAsSticker", False),
            "sendMediaAsHd": call.data.get("sendMediaAsHd", False),
            "isViewOnce": call.data.get("isViewOnce", False),
            "linkPreview": call.data.get("linkPreview", False),
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        await hass.services.async_call(
            "whatsapp",
            "send_media",
            payload,
            blocking=True,
        )

    # Register notify services only if they don't already exist
    if not hass.services.has_service("notify", _NOTIFY_SERVICE_MESSAGE):
        hass.services.async_register("notify", _NOTIFY_SERVICE_MESSAGE, _handle_notify_send_message)
        registered.append(("notify", _NOTIFY_SERVICE_MESSAGE))

    if not hass.services.has_service("notify", _NOTIFY_SERVICE_MEDIA):
        hass.services.async_register("notify", _NOTIFY_SERVICE_MEDIA, _handle_notify_send_media)
        registered.append(("notify", _NOTIFY_SERVICE_MEDIA))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry and remove services we registered."""
    registered = hass.data.get(DOMAIN, {}).get("registered_services", [])

    for domain, service in list(registered):
        try:
            hass.services.async_remove(domain, service)
        except Exception:
            # ignore removal errors
            pass
        try:
            registered.remove((domain, service))
        except ValueError:
            pass

    # clean up stored data
    hass.data.get(DOMAIN, {}).pop("config", None)
    hass.data.get(DOMAIN, {}).pop("registered_services", None)

    return True
