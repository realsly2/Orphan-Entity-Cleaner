# custom_components/orphan_entity_cleaner/api.py
from __future__ import annotations

from aiohttp import web
from homeassistant.core import HomeAssistant

from .const import DOMAIN, RESULTS_KEY


async def async_results_handler(request: web.Request) -> web.Response:
    hass: HomeAssistant = request.app["hass"]
    results = hass.data.setdefault(DOMAIN, {}).get(RESULTS_KEY, [])
    return web.json_response({"results": results})
