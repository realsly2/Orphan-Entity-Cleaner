from __future__ import annotations

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant, Request

from .const import DOMAIN, RESULTS_KEY


class OrphanEntityCleanerResultsView(HomeAssistantView):
    url = "/api/orphan_entity_cleaner/results"
    name = "api:orphan_entity_cleaner:results"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: Request):
        results = self.hass.data.get(DOMAIN, {}).get(RESULTS_KEY, [])
        return self.json(results)
