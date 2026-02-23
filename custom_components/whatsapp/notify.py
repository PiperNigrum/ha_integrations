from homeassistant.components.notify import BaseNotificationService


async def async_get_service(hass, config, discovery_info=None):
    # Zwei getrennte Notify-Services zurückgeben
    return [
        WhatsAppSendMessageNotifyService(hass, "whatsapp_send_message"),
        WhatsAppSendMediaNotifyService(hass, "whatsapp_send_media"),
    ]


class WhatsAppSendMessageNotifyService(BaseNotificationService):
    def __init__(self, hass, name):
        self.hass = hass
        self._name = name

    @property
    def name(self):
        # ergibt notify.whatsapp_send_message
        return self._name

    async def async_send_message(self, message="", **kwargs):
        title = kwargs.get("title", "")
        combined = f"*{title}*\n{message}" if title else message

        chat_id_state = self.hass.states.get("sensor.whatsapp_tobias")
        chat_id = chat_id_state.state if chat_id_state else ""

        await self.hass.services.async_call(
            "whatsapp",
            "send_message",
            {
                "chat_id": chat_id,
                "message": combined,
            },
            blocking=True,
        )


class WhatsAppSendMediaNotifyService(BaseNotificationService):
    def __init__(self, hass, name):
        self.hass = hass
        self._name = name

    @property
    def name(self):
        # ergibt notify.whatsapp_send_media
        return self._name

    async def async_send_message(self, message="", **kwargs):
        title = kwargs.get("title", "")
        data = kwargs.get("data", {}) or {}

        caption = f"*{title}*\n{message}" if title else message

        chat_id_state = self.hass.states.get("sensor.whatsapp_tobias")
        chat_id = chat_id_state.state if chat_id_state else ""

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
