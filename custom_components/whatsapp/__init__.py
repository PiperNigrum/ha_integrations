from typing import Any, Dict, Optional
import logging
from urllib.parse import urlparse, urlunparse

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

SERVICE_SEND_MESSAGE = "send_message"
SERVICE_SEND_MEDIA = "send_media"


def _build_target_url(base: str, port: Optional[int], chat_id: str) -> str:
    """Build URL for POSTing to /api/chats/{chat_id}/messages, respecting optional port."""
    base = (base or "").rstrip("/")
    parsed = urlparse(base)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc or parsed.path  # handle if user passed without scheme
    # If netloc contains no port and a port is provided, append it
    host_part = netloc.split("@")[-1]
    if port and ":" not in host_part:
        netloc = f"{netloc}:{port}"
    rebuilt = urlunparse((scheme, netloc, f"/api/chats/{chat_id}/messages", "", "", ""))
    return rebuilt


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WhatsApp services from a single config entry.

    Registers:
      - whatsapp.send_message
      - whatsapp.send_media

    Both services use the configured base_url and port from the config entry.
    If `title` is provided it is prefixed to the message/caption as *title*.
    """
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = entry.data

    session = async_get_clientsession(hass)

    async def _post_json(url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            resp = await session.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            try:
                return await resp.json()
            except Exception:
                return None
        except Exception as err:
            _LOGGER.exception("Error POST %s: %s", url, err)
            return None

    async def _handle_send_message(call: ServiceCall) -> None:
        chat_id = call.data.get("chat_id")
        message = call.data.get("message", "") or ""
        title = call.data.get("title", "") or ""

        if not chat_id:
            _LOGGER.error("whatsapp.send_message called without chat_id")
            return

        # Prefix title if provided
        if title:
            message = f"*{title}*\n{message}"

        base = entry.data.get(CONF_BASE_URL)
        port = entry.data.get(CONF_PORT, DEFAULT_PORT)

        url = _build_target_url(base, port, chat_id)
        # match rest_command payload: {"msg": "..."} with newlines escaped
        payload = {"msg": message.replace("\n", "\\n")}
        await _post_json(url, payload)

    async def _handle_send_media(call: ServiceCall) -> None:
        chat_id = call.data.get("chat_id")
        url_media = call.data.get("url")
        caption = call.data.get("caption", "") or ""
        title = call.data.get("title", "") or ""

        if not chat_id:
            _LOGGER.error("whatsapp.send_media called without chat_id")
            return

        if not url_media:
            _LOGGER.error("whatsapp.send_media called without url")
            return

        # Prefix title if provided
        if title:
            caption = f"*{title}*\n{caption}"

        base = entry.data.get(CONF_BASE_URL)
        port = entry.data.get(CONF_PORT, DEFAULT_PORT)

        target = _build_target_url(base, port, chat_id)
        payload = {
            "url": url_media.replace("\n", ""),
            "options": {
                "caption": caption.replace("\n", "\\n"),
                "sendMediaAsDocument": bool(call.data.get("sendMediaAsDocument", False)),
                "sendAudioAsVoice": bool(call.data.get("sendAudioAsVoice", False)),
                "sendVideoAsGif": bool(call.data.get("sendVideoAsGif", False)),
                "sendMediaAsSticker": bool(call.data.get("sendMediaAsSticker", False)),
                "sendMediaAsHd": bool(call.data.get("sendMediaAsHd", False)),
                "isViewOnce": bool(call.data.get("isViewOnce", False)),
                "linkPreview": bool(call.data.get("linkPreview", False)),
            },
        }
        # Remove None values inside options (booleans remain)
        options = {k: v for k, v in payload["options"].items() if v is not None}
        payload["options"] = options

        await _post_json(target, payload)

    # Register services (domain: whatsapp)
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_MESSAGE):
        hass.services.async_register(DOMAIN, SERVICE_SEND_MESSAGE, _handle_send_message)

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_MEDIA):
        hass.services.async_register(DOMAIN, SERVICE_SEND_MEDIA, _handle_send_media)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry and remove services."""
    try:
        hass.services.async_remove(DOMAIN, SERVICE_SEND_MESSAGE)
    except Exception:
        _LOGGER.debug("Could not remove service %s.%s", DOMAIN, SERVICE_SEND_MESSAGE)

    try:
        hass.services.async_remove(DOMAIN, SERVICE_SEND_MEDIA)
    except Exception:
        _LOGGER.debug("Could not remove service %s.%s", DOMAIN, SERVICE_SEND_MEDIA)

    hass.data.get(DOMAIN, {}).pop("config", None)
    return True
