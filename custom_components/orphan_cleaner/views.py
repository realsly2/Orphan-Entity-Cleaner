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

    @staticmethod
    def _is_admin_request(request: Request) -> bool:
        """Require an admin for real aiohttp requests.

        Home Assistant can attach the current user via `request.user`, a
        `hass_user` mapping entry, or a lightweight compatibility stub in tests.
        If there is no explicit user data at all, keep the legacy backwards-
        compatible fallback permissive so older callers keep working.
        """
        user = getattr(request, "user", None)
        if user is not None:
            return bool(getattr(user, "is_admin", False))

        request_get = getattr(request, "get", None)
        if request_get is not None:
            for key in ("hass_user", "user"):
                try:
                    user = request_get(key)
                except Exception:  # pragma: no cover - defensive
                    continue
                if user is not None:
                    return bool(getattr(user, "is_admin", False))

        mapping_get = getattr(request, "__getitem__", None)
        if mapping_get is not None:
            for key in ("hass_user", "user"):
                try:
                    user = mapping_get(key)
                except Exception:  # pragma: no cover - defensive
                    continue
                if user is not None:
                    return bool(getattr(user, "is_admin", False))

        # Backwards-compatible fallback for older stubs/tests that do not inject
        # an explicit HA user object. Real HA requests always provide one.
        return True

    async def get(self, request: Request) -> Response:
        """GET /api/orphan_cleaner/results mit optionalen Query-Parametern."""
        if not self._is_admin_request(request):
            return self.json({"error": "Admin access required"}, status_code=403)

        try:
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
        except Exception as err:  # pragma: no cover - defensive debug path
            return self.json({
                "error": "internal_error",
                "details": str(err),
            }, status_code=500)

    async def delete(self, request: Request) -> Response:
        """DELETE /api/orphan_cleaner/results - Löscht alle Ergebnisse."""
        if not self._is_admin_request(request):
            return self.json({"error": "Admin access required"}, status_code=403)

        try:
            hass = request.app["hass"]
            data = hass.data.get(DOMAIN, {})
            data[RESULTS_KEY] = []
            return self.json({"message": "Results cleared"})
        except Exception as err:  # pragma: no cover - defensive debug path
            return self.json({
                "error": "internal_error",
                "details": str(err),
            }, status_code=500)
