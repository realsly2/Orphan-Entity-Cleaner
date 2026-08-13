# custom_components/orphan_entity_cleaner/panel.py
from __future__ import annotations

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_URL, PANEL_TITLE, PANEL_ICON
from .panel_html import PANEL_HTML


async def async_register_panel(hass: HomeAssistant) -> None:
    async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL.strip("/"),
        require_admin=True,
        config={"url": PANEL_HTML, "title": PANEL_TITLE},
    )
