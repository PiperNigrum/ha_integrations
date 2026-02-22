from homeassistant.components.notify import BaseNotificationService

from .const import (
    CONF_SERVICE,
    SERVICE_SEND_MESSAGE,
    SERVICE_SEND_MEDIA,
)


async def async_get_service(hass, config, discovery_info=None):
    service_type = config.get(CONF_SERVICE)

    if service_type == SERVICE_SEND_MESSAGE:
        return WhatsAppSendMessageService(hass, "send_message")

    if service_type == SERVICE_SEND_MEDIA:
        return WhatsAppSendMediaService(hass, "send_media")

    return None


class WhatsAppSendMessageService(BaseNotificationService):
    def __init__(self, hass, name):
        self.hass = hass
        self._name = name

    @property
    def name(self):
        return self._name

    async def async_send_message(self, message="", **kwargs):
        title = kwargs.get("title", "")
        combined = f"*{title}*\n{message}" if title else message

        chat_id = self.hass.states.get("sensor.whatsapp_tobias").state

        await self.hass.services.async_call(
            "whatsapp",
            "send_message",
            {"chat_id": chat_id, "message": combined},
            blocking=True,
        )


class WhatsAppSendMediaService(BaseNotificationService):
    def __init__(self, hass, name):
        self.hass = hass
        self._name = name

    @property
    def name(self):
        return self._name

    async def async_send_message(self, message="", **kwargs):
        data = kwargs.get("data", {})
        title = kwargs.get("title", "")
        caption = f"*{title}*\n{message}" if title else message

        chat_id = self.hass.states.get("sensor.whatsapp_tobias").state

        payload = {
            "chat_id": chat_id,
            "url": data.get("url"),
            "caption": caption,
            "sendMediaAsDocument": data.get("sendMediaAsDocument", False),
            "sendAudioAsVoice": data.get("sendAudioAsVoice", False),
            "sendVideoAsGif": data.get("sendVideoAsGif", False),
            "sendMediaAsSticker": data.get("sendMediaAsSticker", False),
            "sendMediaAsHd": data.get("sendMediaAsHd", False),
            "isViewOnce": data.get("isViewOnce", False),
            "linkPreview": data.get("linkPreview", False),
        }

        await self.hass.services.async_call(
            "whatsapp",
            "send_media",
            payload,
            blocking=True,
        )
