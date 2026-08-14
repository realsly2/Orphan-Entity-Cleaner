from __future__ import annotations

from aiohttp.web import Request

from homeassistant.components.http import HomeAssistantView

from .panel_html import PANEL_HTML


class OrphanCleanerPanelView(HomeAssistantView):
    url = "/orphan-cleaner"
    name = "orphan_cleaner:panel"
    requires_auth = True

    async def get(self, request: Request):
        return self.html(PANEL_HTML)
