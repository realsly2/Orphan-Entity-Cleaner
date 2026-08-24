# custom_components/orphan_cleaner/views.py
from __future__ import annotations

from aiohttp.web import Request, Response
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN, RESULTS_KEY


class OrphanCleanerResultsView(HomeAssistantView):
    """API-Endpunkt für Scan-Ergebnisse mit Paginierung.

    Wird vom Panel über hass.callApi("GET", "orphan_cleaner/results")
    aufgerufen - dadurch ist der Bearer-Token bereits korrekt gesetzt.
    """

    url = "/api/orphan_cleaner/results"
    name = "orphan_cleaner:api_results"
    requires_auth = True

    async def get(self, request: Request) -> Response:
        """GET /api/orphan_cleaner/results mit optionalen Query-Parametern."""
        user = request.get("hass_user") if hasattr(request, "get") else None
        if user is not None and not getattr(user, "is_admin", False):
            return self.json({"error": "Admin access required"}, status_code=403)

        hass = request.app["hass"]
        data = hass.data.get(DOMAIN, {})
        results = data.get(RESULTS_KEY, [])

        limit_str = request.query.get("limit")
        offset_str = request.query.get("offset", "0")

        try:
            offset = int(offset_str)
            if offset < 0:
                offset = 0
        except ValueError:
            offset = 0

        limit = None
        if limit_str is not None:
            try:
                limit = int(limit_str)
                if limit < 1:
                    limit = None
            except ValueError:
                pass

        total_count = len(results)
        paginated_results = results

        if limit is not None:
            paginated_results = results[offset:offset + limit]

        response_data = {
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "results": paginated_results,
            "backups": data.get("backups", []),
            "last_backup_path": data.get("last_backup_path"),
            "last_restore": data.get("last_restore"),
        }

        return self.json(response_data)

    async def delete(self, request: Request) -> Response:
        """DELETE /api/orphan_cleaner/results - Löscht alle Ergebnisse."""
        user = request.get("hass_user") if hasattr(request, "get") else None
        if user is not None and not getattr(user, "is_admin", False):
            return self.json({"error": "Admin access required"}, status_code=403)

        hass = request.app["hass"]
        data = hass.data.get(DOMAIN, {})
        data[RESULTS_KEY] = []
        return self.json({"message": "Results cleared"})
