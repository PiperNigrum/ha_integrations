from typing import Any, Dict

from homeassistant.components.notify import BaseNotificationService
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_NOTIFY_SERVICE_MESSAGE = "whatsapp_send_message"
_NOTIFY_SERVICE_MEDIA = "whatsapp_send_media"


async def async_get_service(hass: HomeAssistant, config: Dict[str, Any], discovery_info=None):
    """Register two notify.* wrapper services that forward to whatsapp.* services.

    Returns a minimal notify service instance to satisfy the platform API.
    """
    # Ensure we only register the notify wrapper services once
    if not hass.data.setdefault(DOMAIN, {}).get("notify_registered"):
        async def _handle_notify_send_message(call: ServiceCall) -> None:
            payload = {
                "chat_id": call.data.get("chat_id"),
                "message": call.data.get("message"),
                "title": call.data.get("title"),
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            await hass.services.async_call("whatsapp", "send_message", payload, blocking=True)

        async def _handle_notify_send_media(call: ServiceCall) -> None:
            payload = {
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
            await hass.services.async_call("whatsapp", "send_media", payload, blocking=True)

        if not hass.services.has_service("notify", _NOTIFY_SERVICE_MESSAGE):
            hass.services.async_register("notify", _NOTIFY_SERVICE_MESSAGE, _handle_notify_send_message)

        if not hass.services.has_service("notify", _NOTIFY_SERVICE_MEDIA):
            hass.services.async_register("notify", _NOTIFY_SERVICE_MEDIA, _handle_notify_send_media)

        hass.data[DOMAIN]["notify_registered"] = True

    # Return a minimal notify service instance (proxy). HA expects an object here.
    return _WhatsAppNotifyProxy(hass)


class _WhatsAppNotifyProxy(BaseNotificationService):
    """Minimal proxy notify service to satisfy the notify platform contract."""

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    @property
    def name(self) -> str:
        return "whatsapp_proxy"

    async def async_send_message(self, message: str = "", **kwargs) -> None:
        """Fallback: forward to whatsapp.send_message by default."""
        payload = {
            "chat_id": kwargs.get("chat_id"),
            "message": message,
            "title": kwargs.get("title"),
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        await self.hass.services.async_call("whatsapp", "send_message", payload, blocking=True)
