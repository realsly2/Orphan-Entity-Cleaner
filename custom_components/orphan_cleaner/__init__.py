# custom_components/orphan_cleaner/__init__.py
from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .panel import async_register_panel
from .services import async_register_services
from .views import OrphanCleanerPanelView, OrphanCleanerResultsView


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Initialisiert die Orphan Cleaner Integration."""
    hass.data.setdefault(DOMAIN, {})
    
    # Services registrieren
    async_register_services(hass)
    
    # Panel registrieren
    await async_register_panel(hass)
    
    # ===== NEU: API-View registrieren =====
    hass.http.register_view(OrphanCleanerPanelView)
    hass.http.register_view(OrphanCleanerResultsView)
    
    return True
