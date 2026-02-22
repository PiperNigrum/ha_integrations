from homeassistant.components.notify import BaseNotificationService


async def async_get_service(hass, config, discovery_info=None):
    return WhatsAppNotifyService(hass)


class WhatsAppNotifyService(BaseNotificationService):
    def __init__(self, hass):
        self.hass = hass

    @property
    def targets(self):
        return {
            "whatsapp_send_message": "whatsapp_send_message",
            "whatsapp_send_media": "whatsapp_send_media",
        }

    async def async_send_message(self, message="", **kwargs):
        target = kwargs.get("target")
        title = kwargs.get("title", "")
        data = kwargs.get("data", {})

        chat_id = self.hass.states.get("sensor.whatsapp_tobias").state

        if target == "whatsapp_send_media":
            payload = {
                "chat_id": chat_id,
                "url": data.get("url"),
                "caption": f"*{title}*\n{message}" if title else message,
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
        else:
            combined = f"*{title}*\n{message}" if title else message

            await self.hass.services.async_call(
                "whatsapp",
                "send_message",
                {
                    "chat_id": chat_id,
                    "message": combined,
                },
                blocking=True,
            )
