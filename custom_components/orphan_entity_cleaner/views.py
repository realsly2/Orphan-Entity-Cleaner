# custom_components/orphan_entity_cleaner/views.py
from __future__ import annotations

from aiohttp import web
from homeassistant.components.http import HomeAssistantView

from .const import PANEL_URL
from .panel_html import PANEL_HTML


class OrphanEntityCleanerPanelView(HomeAssistantView):
    url = PANEL_URL
    name = "api:orphan_entity_cleaner:panel"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        return web.Response(text=PANEL_HTML, content_type="text/html")
