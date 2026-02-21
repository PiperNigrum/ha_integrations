from homeassistant.components.notify import BaseNotificationService

async def async_get_service(hass, config, discovery_info=None):
    # Name des Notify-Dienstes festlegen
        return WhatsAppNotificationService(hass, "whatsapp_send_message")


        class WhatsAppNotificationService(BaseNotificationService):
            def __init__(self, hass, name):
                    self.hass = hass
                            self._name = name

                                @property
                                    def name(self):
                                            # Name des Notify-Dienstes → notify.whatsapp_send_message
                                                    return self._name

                                                        async def async_send_message(self, message="", **kwargs):
                                                                title = kwargs.get("title", "")

                                                                        # Kombinierter WhatsApp-Text
                                                                                combined_message = f"*{title}*\n{message}" if title else message

                                                                                        # chat_id aus Sensor lesen
                                                                                                chat_state = self.hass.states.get("sensor.whatsapp_tobias")
                                                                                                        chat_id = chat_state.state if chat_state else ""

                                                                                                                # WhatsApp.send_Media aufrufen
                                                                                                                        await self.hass.services.async_call(
                                                                                                                                    "WhatsApp",
                                                                                                                                                "send_message",
                                                                                                                                                            {
                                                                                                                                                                            "chat_id": chat_id,
                                                                                                                                                                                            "message": combined_message
                                                                                                                                                                                                        },
                                                                                                                                                                                                                    blocking=True
                                                                                                                                                                                                                            )
                                                                                                                                                                                                                            