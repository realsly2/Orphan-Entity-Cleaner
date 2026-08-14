# custom_components/orphan_cleaner/panel.py
from __future__ import annotations

from homeassistant.components import frontend
from homeassistant.core import HomeAssistant

from .api import OrphanCleanerResultsView
from .const import PANEL_ICON, PANEL_TITLE, PANEL_URL
from .views import OrphanCleanerPanelView


async def async_register_panel(hass: HomeAssistant) -> None:
    hass.http.register_view(OrphanCleanerPanelView())
    hass.http.register_view(OrphanCleanerResultsView(hass))
    frontend.async_register_built_in_panel(
        hass,
        "iframe",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL.strip("/"),
        config={"url": PANEL_URL},
        require_admin=True,
    )
