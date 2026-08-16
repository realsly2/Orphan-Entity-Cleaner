# custom_components/orphan_cleaner/__init__.py
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .panel import async_register_panel
from .services import async_register_services
from .views import OrphanCleanerResultsView

_SETUP_DONE_KEY = "_setup_done"


async def _async_ensure_setup(hass: HomeAssistant) -> None:
    """Registriert Services/Views/Panel genau einmal.

    Wird sowohl von async_setup (YAML: `orphan_cleaner:` in
    configuration.yaml) als auch von async_setup_entry (UI: Einstellungen ->
    Geräte & Dienste -> Integration hinzufügen) aufgerufen. Ohne diese
    Sperre würde bei gleichzeitiger YAML- und UI-Konfiguration alles
    doppelt registriert.
    """
    hass.data.setdefault(DOMAIN, {})
    if hass.data[DOMAIN].get(_SETUP_DONE_KEY):
        return
    hass.data[DOMAIN][_SETUP_DONE_KEY] = True

    async_register_services(hass)
    hass.http.register_view(OrphanCleanerResultsView)
    await async_register_panel(hass)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Legacy-Setup über configuration.yaml."""
    await _async_ensure_setup(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup über Einstellungen -> Geräte & Dienste -> Integration hinzufügen."""
    await _async_ensure_setup(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Config Entry entfernen.

    Services/Views/Panel werden bewusst nicht deregistriert - HA sieht dafür
    kein sauberes API vor (frontend.async_remove_panel entfernt zwar den
    Sidebar-Eintrag, aber die HTTP-Views blieben ohnehin bestehen). Ein
    Neustart räumt vollständig auf.
    """
    return True
