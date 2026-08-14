from __future__ import annotations

from homeassistant.core import HomeAssistant

from .api import OrphanCleanerResultsView
from .const import PANEL_ICON, PANEL_TITLE, PANEL_URL
from .views import OrphanCleanerPanelView


async def async_register_panel(hass: HomeAssistant) -> None:
    hass.http.register_view(OrphanCleanerPanelView())
    hass.http.register_view(OrphanCleanerResultsView(hass))
    hass.components.frontend.async_register_built_in_panel(
        hass,
        PANEL_URL.strip("/"),
        PANEL_TITLE,
        PANEL_ICON,
        require_admin=True,
        frontend_url_path=PANEL_URL.strip("/"),
    )
