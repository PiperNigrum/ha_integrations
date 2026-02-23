from typing import Any, Dict, Optional

import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

SERVICE_SEND_MESSAGE = "send_message"
SERVICE_SEND_MEDIA = "send_media"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the WhatsApp integration from a config entry.

    Registers two services:
      - whatsapp.send_message
      - whatsapp.send_media

    The services use the configured base_url and port from the config entry.
    """
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = entry.data

    session = async_get_clientsession(hass)

    async def _send_request(path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        base = entry.data.get(CONF_BASE_URL)
        port = entry.data.get(CONF_PORT, DEFAULT_PORT)
        if not base:
            _LOGGER.error("WhatsApp integration not configured: base_url missing")
            return None

        url = f"{base.rstrip('/')}/{path.lstrip('/')}"
        if port:
            # allow base to already include port; only append if base has no port
            # simple heuristic: if base contains ":" after "http", assume port present
            if "://" in base and base.rsplit(":", 1)[-1].isdigit() is False:
                url = f"{base.rstrip('/')}:{port}/{path.lstrip('/')}"
        try:
            resp = await session.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            try:
                return await resp.json()
            except Exception:
                return None
        except Exception as err:
            _LOGGER.exception("Error sending request to %s: %s", url, err)
            return None

    async def _handle_send_message(call: ServiceCall) -> None:
        data = {
            "chat_id": call.data.get("chat_id"),
            "message": call.data.get("message"),
        }
        # remove None values
        data = {k: v for k, v in data.items() if v is not None}
        await _send_request("sendMessage", data)

    async def _handle_send_media(call: ServiceCall) -> None:
        data = {
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
        data = {k: v for k, v in data.items() if v is not None}
        await _send_request("sendMedia", data)

    # Register services if not already present
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_MESSAGE):
        hass.services.async_register(DOMAIN, SERVICE_SEND_MESSAGE, _handle_send_message)

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_MEDIA):
        hass.services.async_register(DOMAIN, SERVICE_SEND_MEDIA, _handle_send_media)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry and remove registered services."""
    try:
        hass.services.async_remove(DOMAIN, SERVICE_SEND_MESSAGE)
    except Exception:
        _LOGGER.debug("Failed to remove service %s.%s", DOMAIN, SERVICE_SEND_MESSAGE)

    try:
        hass.services.async_remove(DOMAIN, SERVICE_SEND_MEDIA)
    except Exception:
        _LOGGER.debug("Failed to remove service %s.%s", DOMAIN, SERVICE_SEND_MEDIA)

    hass.data.get(DOMAIN, {}).pop("config", None)
    return True
