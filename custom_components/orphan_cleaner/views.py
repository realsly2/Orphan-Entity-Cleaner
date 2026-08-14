from __future__ import annotations

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import Request

from .panel_html import PANEL_HTML


class OrphanCleanerPanelView(HomeAssistantView):
    url = "/orphan-cleaner"
    name = "orphan_cleaner:panel"
    requires_auth = True

    async def get(self, request: Request):
        return self.html(PANEL_HTML)
