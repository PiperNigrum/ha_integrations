import logging
import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType):
    # Wird benötigt, sonst: "No setup function defined"
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    base_url = entry.data[CONF_BASE_URL]
    port = entry.data[CONF_PORT]
    
    session = aiohttp.ClientSession()

    async def send_message(call: ServiceCall):
        chat_id = call.data["chat_id"]
        message = call.data["message"].replace("\n", "\\n")

        url = f"http://{base_url}:{port}/api/chats/{{chat_id}}/messages"
        payload = {"msg": message}

        async with async_timeout.timeout(10):
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    _LOGGER.error("Failed to send message: %s", await resp.text())

    async def send_media(call: ServiceCall):
        chat_id = call.data["chat_id"]
        url_media = call.data["url"].replace("\n", "")
        caption = call.data.get("caption", "").replace("\n", "\\n")

        options = {
            "sendMediaAsDocument": call.data.get("sendMediaAsDocument", False),
            "sendAudioAsVoice": call.data.get("sendAudioAsVoice", False),
            "sendVideoAsGif": call.data.get("sendVideoAsGif", False),
            "sendMediaAsSticker": call.data.get("sendMediaAsSticker", False),
            "sendMediaAsHd": call.data.get("sendMediaAsHd", False),
            "isViewOnce": call.data.get("isViewOnce", False),
            "linkPreview": call.data.get("linkPreview", False)
        }

        url = f"http://{base_url}:{port}/api/chats/{{chat_id}}/messages"

        payload = {
            "url": url_media,
            "options": {
                "caption": caption,
                **options
            }
        }

        async with async_timeout.timeout(10):
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    _LOGGER.error("Failed to send media: %s", await resp.text())

    hass.services.async_register(DOMAIN, "send_message", send_message)
    hass.services.async_register(DOMAIN, "send_media", send_media)

    return True