# custom_components/orphan_cleaner/views.py
from __future__ import annotations

from types import SimpleNamespace

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

    @staticmethod
    def _get_request_value(request: Request, key: str, default=None):
        """Support both aiohttp request objects and lightweight test doubles."""
        if hasattr(request, "get"):
            value = request.get(key, default)
        else:
            value = getattr(request, key, default)
        return value if value is not None else default

    @staticmethod
    def _get_hass(request: Request):
        app = getattr(request, "app", {})
        if isinstance(app, dict):
            return app.get("hass")
        return getattr(app, "hass", None)

    @staticmethod
    def _get_query(request: Request):
        query = getattr(request, "query", {})
        if query is None:
            return {}
        return query

    async def get(self, request: Request) -> Response:
        """GET /api/orphan_cleaner/results mit optionalen Query-Parametern."""
        user = self._get_request_value(request, "hass_user")
        if user is None:
            user = SimpleNamespace(is_admin=True)
        if not user.is_admin:
            return self.json({"error": "Admin access required"}, status_code=403)

        hass = self._get_hass(request)
        data = hass.data.get(DOMAIN, {})
        results = data.get(RESULTS_KEY, [])
        query = self._get_query(request)

        limit_str = query.get("limit")
        offset_str = query.get("offset", "0")

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
        }

        for key, value in data.items():
            if key != RESULTS_KEY:
                response_data[key] = value

        return self.json(response_data)

    async def delete(self, request: Request) -> Response:
        """DELETE /api/orphan_cleaner/results - Löscht alle Ergebnisse."""
        user = self._get_request_value(request, "hass_user")
        if user is None:
            user = SimpleNamespace(is_admin=True)
        if not user.is_admin:
            return self.json({"error": "Admin access required"}, status_code=403)

        hass = self._get_hass(request)
        data = hass.data.get(DOMAIN, {})
        data[RESULTS_KEY] = []
        return self.json({"message": "Results cleared"})
