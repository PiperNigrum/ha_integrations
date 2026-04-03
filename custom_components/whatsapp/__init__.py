from typing import Any, Dict, Optional
import logging
import re
import aiohttp
from urllib.parse import urlparse, urlunparse, quote

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_BASE_URL, CONF_PORT, CONF_API_KEY, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

SERVICE_SEND_MESSAGE = "send_message"
SERVICE_SEND_MEDIA = "send_media"

_CHAT_ID_RE = re.compile(r"^\d{7,15}$")


def _normalize_url(url: str) -> str:
    """Ergänzt https:// falls kein Schema angegeben ist."""
    url = url.strip().rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"
    return url


def _build_target_url(base: Optional[str], port: Optional[int], chat_id: str) -> str:
    """Build URL for POSTing to /api/chats/{chat_id}/messages."""
    base = _normalize_url(base or "")
    parsed = urlparse(base)

    scheme = parsed.scheme
    netloc = parsed.netloc or parsed.path
    host_part = netloc.split("@")[-1]

    if port and ":" not in host_part:
        netloc = f"{netloc}:{port}"

    return urlunparse((scheme, netloc, f"/api/chats/{quote(chat_id, safe='')}/messages", "", "", ""))


def _validate_chat_id(chat_id) -> bool:
    """Prüft ob chat_id nur aus Ziffern besteht (7–15 Stellen)."""
    return bool(_CHAT_ID_RE.match(str(chat_id)))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WhatsApp integration."""

    hass.data.setdefault(DOMAIN, {})

    # MIGRATION: fehlende Felder ergänzen
    updated = False
    data = dict(entry.data)

    if CONF_API_KEY not in data:
        data[CONF_API_KEY] = ""
        updated = True

    if updated:
        hass.config_entries.async_update_entry(entry, data=data)

    # Sicheres Zusammenführen von data + options
    hass.data[DOMAIN]["config"] = {
        **entry.data,
        **(entry.options or {}),
    }

    session = async_get_clientsession(hass)
    _timeout = aiohttp.ClientTimeout(total=30)

    async def _post_json(url: str, payload: Dict[str, Any], api_key: str) -> Optional[Dict[str, Any]]:
        headers = {"x-api-key": api_key} if api_key else {}

        try:
            resp = await session.post(url, json=payload, headers=headers, timeout=_timeout)
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

        chat_id = str(chat_id)
        if not _validate_chat_id(chat_id):
            _LOGGER.error("whatsapp.send_message: ungültige chat_id: %s", chat_id)
            return

        if title:
            message = f"*{title}*\n{message}"

        cfg = hass.data.get(DOMAIN, {}).get("config", {})
        base = cfg.get(CONF_BASE_URL)
        port = cfg.get(CONF_PORT, DEFAULT_PORT)
        api_key = cfg.get(CONF_API_KEY, "")

        url = _build_target_url(base, port, chat_id)
        payload = {"msg": message}

        await _post_json(url, payload, api_key)

    async def _handle_send_media(call: ServiceCall) -> None:
        chat_id = call.data.get("chat_id")
        url_media = call.data.get("url")
        caption = call.data.get("caption", "") or ""
        title = call.data.get("title", "") or ""

        if not chat_id:
            _LOGGER.error("whatsapp.send_media called without chat_id")
            return

        chat_id = str(chat_id)
        if not _validate_chat_id(chat_id):
            _LOGGER.error("whatsapp.send_media: ungültige chat_id: %s", chat_id)
            return

        if not url_media:
            _LOGGER.error("whatsapp.send_media called without url")
            return

        # URL bereinigen
        url_media = url_media.strip()

        if title:
            caption = f"*{title}*\n{caption}"

        cfg = hass.data.get(DOMAIN, {}).get("config", {})
        base = cfg.get(CONF_BASE_URL)
        port = cfg.get(CONF_PORT, DEFAULT_PORT)
        api_key = cfg.get(CONF_API_KEY, "")

        target = _build_target_url(base, port, chat_id)
        payload = {
            "url": url_media,
            "options": {
                "caption": caption,
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

        await _post_json(target, payload, api_key)

    # Services registrieren (nur einmal)
    services_registered = hass.data[DOMAIN].setdefault("services_registered", False)
    if not services_registered:
        hass.services.async_register(DOMAIN, SERVICE_SEND_MESSAGE, _handle_send_message)
        hass.services.async_register(DOMAIN, SERVICE_SEND_MEDIA, _handle_send_media)
        hass.data[DOMAIN]["services_registered"] = True

    # Update Listener
    async def _async_update_listener(hass_inner: HomeAssistant, updated_entry: ConfigEntry) -> None:
        hass_inner.data.setdefault(DOMAIN, {})
        hass_inner.data[DOMAIN]["config"] = {
            **updated_entry.data,
            **(updated_entry.options or {}),
        }
        # Maskiertes Logging – API-Key wird nicht im Klartext geloggt
        safe_config = {
            k: ("***" if k == CONF_API_KEY else v)
            for k, v in hass_inner.data[DOMAIN]["config"].items()
        }
        _LOGGER.debug("WhatsApp config updated: %s", safe_config)

    entry.add_update_listener(_async_update_listener)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        hass.services.async_remove(DOMAIN, SERVICE_SEND_MESSAGE)
    except Exception:
        pass

    try:
        hass.services.async_remove(DOMAIN, SERVICE_SEND_MEDIA)
    except Exception:
        pass

    hass.data.get(DOMAIN, {}).pop("config", None)
    # Explizit auf False setzen, damit async_setup_entry nach erneutem Laden korrekt arbeitet
    hass.data.get(DOMAIN, {})["services_registered"] = False

    return True