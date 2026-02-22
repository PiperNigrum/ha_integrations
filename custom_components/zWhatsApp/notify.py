from homeassistant.components.notify import BaseNotificationService

async def async_get_service(hass, config, discovery_info=None):
    # discovery_info entscheidet, welcher Dienst erzeugt wird
    service_type = discovery_info.get("service")

    if service_type == "send_message":
        return WhatsAppSendMessageService(hass, "whatsapp_send_message")

    if service_type == "send_media":
        return WhatsAppSendMediaService(hass, "whatsapp_send_media")

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
        combined_message = f"*{title}*\n{message}" if title else message

        chat_id = self.hass.states.get("sensor.whatsapp_tobias").state

        await self.hass.services.async_call(
            "WhatsApp",
            "send_message",
            {
                "chat_id": chat_id,
                "message": combined_message
            },
            blocking=True
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
            "WhatsApp",
            "send_media",
            payload,
            blocking=True
        )
