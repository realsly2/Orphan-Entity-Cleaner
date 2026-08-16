# custom_components/orphan_cleaner/panel.py
from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import PANEL_ICON, PANEL_TITLE, PANEL_URL

FRONTEND_DIR = Path(__file__).parent / "frontend"
JS_FILENAME = "orphan-cleaner-panel.js"
JS_URL_PATH = f"/api/orphan_cleaner/frontend/{JS_FILENAME}"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Registriert das Sidebar-Panel als panel_custom-Element.

    Das ist derselbe Ansatz, den z.B. HACS für sein eigenes Panel nutzt:
    Ein echtes JS-Custom-Element läuft direkt im HA-Frontend und bekommt das
    bereits authentifizierte hass-Objekt als Property übergeben
    (hass.callService / hass.callApi hängen den Bearer-Token automatisch an).

    Der vorher genutzte "iframe"-Panel-Typ ist dafür ungeeignet: HAs
    /api/*-Endpunkte akzeptieren ausschließlich einen Authorization-Header
    oder eine signierte URL, niemals Cookies - eine per iframe eingebettete
    statische HTML-Seite mit eigenem fetch() hätte dafür keinen gültigen
    Token gehabt und wäre mit 401 gescheitert.
    """
    await hass.http.async_register_static_paths(
        [StaticPathConfig(JS_URL_PATH, str(FRONTEND_DIR / JS_FILENAME), cache_headers=False)]
    )

    frontend.async_register_built_in_panel(
        hass,
        "custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL.strip("/"),
        config={
            "_panel_custom": {
                "name": "orphan-cleaner-panel",
                "embed_iframe": False,
                "trust_external": False,
                "js_url": JS_URL_PATH,
            }
        },
        require_admin=True,
    )
