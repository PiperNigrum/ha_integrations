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


def _build_target_url(base: Optional[str], port: Optional[int], chat_id: str) -> str:
    """Build URL for POSTing to /api/chats/{chat_id}/messages, respecting optional port."""
    base = (base or "").rstrip("/")
    parsed = urlparse(base)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc or parsed.path  # handle if user passed without scheme
    host_part = netloc.split("@")[-1]
    if port and ":" not in host_part:
        netloc = f"{netloc}:{port}"
    return urlunparse((scheme, netloc, f"/api/chats/{chat_id}/messages", "", "", ""))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WhatsApp services from a single config entry.

    - Stores the config centrally in hass.data[DOMAIN]["config"] so handlers always
      read the latest values.
    - Registers two services:
        * whatsapp.send_message
        * whatsapp.send_media
    - Registers an update listener so changes via the config flow update the stored config.
    """
    hass.data.setdefault(DOMAIN, {})
    # store config centrally so handlers always read the latest values
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

        if title:
            message = f"*{title}*\n{message}"

        # Read the latest config from hass.data so updates take effect immediately
        cfg = hass.data.get(DOMAIN, {}).get("config", {})
        base = cfg.get(CONF_BASE_URL)
        port = cfg.get(CONF_PORT, DEFAULT_PORT)

        url = _build_target_url(base, port, chat_id)
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

        if title:
            caption = f"*{title}*\n{caption}"

        # Read the latest config from hass.data so updates take effect immediately
        cfg = hass.data.get(DOMAIN, {}).get("config", {})
        base = cfg.get(CONF_BASE_URL)
        port = cfg.get(CONF_PORT, DEFAULT_PORT)

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
        payload["options"] = {k: v for k, v in payload["options"].items() if v is not None}

        await _post_json(target, payload)

    # Register services (domain: whatsapp) only once
    services_registered = hass.data[DOMAIN].setdefault("services_registered", False)
    if not services_registered:
        hass.services.async_register(DOMAIN, SERVICE_SEND_MESSAGE, _handle_send_message)
        hass.services.async_register(DOMAIN, SERVICE_SEND_MEDIA, _handle_send_media)
        hass.data[DOMAIN]["services_registered"] = True

    # Update listener: keep hass.data[DOMAIN]["config"] in sync when the entry is updated
    async def _async_update_listener(hass_inner: HomeAssistant, updated_entry: ConfigEntry) -> None:
        hass_inner.data.setdefault(DOMAIN, {})
        hass_inner.data[DOMAIN]["config"] = updated_entry.data
        _LOGGER.debug("WhatsApp config entry updated, new config stored in hass.data[%s]['config']", DOMAIN)

    entry.add_update_listener(_async_update_listener)

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

    # Clean up stored data
    hass.data.get(DOMAIN, {}).pop("config", None)
    hass.data.get(DOMAIN, {}).pop("services_registered", None)

    return True
