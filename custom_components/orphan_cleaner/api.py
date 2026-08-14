from __future__ import annotations

from aiohttp.web import Request

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, RESULTS_KEY


class OrphanCleanerResultsView(HomeAssistantView):
    url = "/api/orphan_cleaner/results"
    name = "api:orphan_cleaner:results"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: Request):
        return self.json(self.hass.data.get(DOMAIN, {}).get(RESULTS_KEY, []))
