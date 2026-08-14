# custom_components/orphan_cleaner/views.py
from __future__ import annotations

from aiohttp.web import Request, Response
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN, RESULTS_KEY
from .panel_html import PANEL_HTML


class OrphanCleanerPanelView(HomeAssistantView):
    """Haupt-View für das Sidebar-Panel."""
    url = "/orphan-cleaner"
    name = "orphan_cleaner:panel"
    requires_auth = True

    async def get(self, request: Request):
        return self.html(PANEL_HTML)


# ===== NEU: API-View mit Paginierung =====
class OrphanCleanerResultsView(HomeAssistantView):
    """API-Endpunkt für Scan-Ergebnisse mit Paginierung."""
    url = "/api/orphan_cleaner/results"
    name = "orphan_cleaner:api_results"
    requires_auth = True

    async def get(self, request: Request) -> Response:
        """GET /api/orphan_cleaner/results mit optionalen Query-Parametern."""
        hass = request.app["hass"]
        data = hass.data.get(DOMAIN, {})
        results = data.get(RESULTS_KEY, [])
        
        # Query-Parameter auslesen
        limit_str = request.query.get("limit")
        offset_str = request.query.get("offset", "0")
        
        # Offset validieren
        try:
            offset = int(offset_str)
            if offset < 0:
                offset = 0
        except ValueError:
            offset = 0
        
        # Limit validieren
        limit = None
        if limit_str is not None:
            try:
                limit = int(limit_str)
                if limit < 1:
                    limit = None
            except ValueError:
                pass
        
        # Paginierung anwenden
        total_count = len(results)
        paginated_results = results
        
        if limit is not None:
            paginated_results = results[offset:offset + limit]
        
        # Antwort mit Metadaten
        response_data = {
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "results": paginated_results,
        }
        
        return self.json(response_data)

    async def delete(self, request: Request) -> Response:
        """DELETE /api/orphan_cleaner/results - Löscht alle Ergebnisse."""
        hass = request.app["hass"]
        data = hass.data.get(DOMAIN, {})
        data[RESULTS_KEY] = []
        return self.json({"message": "Results cleared"})
