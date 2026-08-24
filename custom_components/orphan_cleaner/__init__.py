from __future__ import annotations

import glob
import json
import os
import re
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .panel import async_register_panel
from .services import async_register_services
from .views import OrphanCleanerResultsView

_SETUP_DONE_KEY = "_setup_done"
_ENTITY_ID_PATTERN = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")


def _is_admin(connection: websocket_api.ActiveConnection) -> bool:
    """Prüft den Benutzer der WebSocket-Verbindung."""
    user = getattr(connection, "user", None)
    return user is not None and user.is_admin


def _find_latest_backup_path(hass: HomeAssistant) -> str | None:
    """Findet das neueste Backup sowohl im Root als auch im Unterordner."""
    candidate_dirs = [
        hass.config.path(),
        hass.config.path("orphan_cleaner_backups"),
    ]
    backup_files: list[str] = []
    for directory in candidate_dirs:
        backup_files.extend(glob.glob(os.path.join(directory, "orphan_cleaner_backup_*.json")))

    if not backup_files:
        return None

    backup_files = sorted(set(backup_files), key=os.path.getctime, reverse=True)
    return backup_files[0]


@websocket_api.websocket_command({
    vol.Required("type"): "orphan_cleaner/download_backup"
})
@websocket_api.async_response
async def ws_download_backup(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Liest das aktuellste Backup aus /config/ aus und sendet es an das Frontend."""
    if not _is_admin(connection):
        connection.send_error(msg["id"], "unauthorized", "Admin access required")
        return

    latest_backup = _find_latest_backup_path(hass)
    if latest_backup is None:
        connection.send_error(
            msg["id"],
            "not_found",
            "Keine Backup-Datei in /config/ oder /config/orphan_cleaner_backups/ gefunden.",
        )
        return

    def _read_file():
        with open(latest_backup, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        backup_data = await hass.async_add_executor_job(_read_file)
        connection.send_result(
            msg["id"],
            {
                "filename": os.path.basename(latest_backup),
                "data": backup_data,
            },
        )
    except Exception as err:
        connection.send_error(msg["id"], "read_error", f"Fehler beim Lesen des Backups: {err}")


@websocket_api.websocket_command({
    vol.Required("type"): "orphan_cleaner/restore_backup",
    vol.Required("entities"): list,
})
@websocket_api.async_response
async def ws_restore_backup(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Stellt Entitäten aus der hochgeladenen Backup-Datei in der Entity Registry wieder her."""
    if not _is_admin(connection):
        connection.send_error(msg["id"], "unauthorized", "Admin access required")
        return

    registry = er.async_get(hass)
    entities = msg["entities"]
    restored_count = 0

    for entity_data in entities:
        if not isinstance(entity_data, dict):
            continue

        entity_id = entity_data.get("entity_id")
        platform = entity_data.get("platform")
        unique_id = entity_data.get("unique_id")

        if (
            not isinstance(entity_id, str)
            or not _ENTITY_ID_PATTERN.fullmatch(entity_id)
            or not isinstance(platform, str)
            or not platform
            or (unique_id is not None and not isinstance(unique_id, str))
        ):
            continue

        domain = entity_id.split(".", 1)[0]
        suggested_object_id = entity_id.split(".", 1)[1]

        # Nur wiederherstellen, wenn die Entität nicht bereits existiert
        if not registry.async_is_registered(entity_id):
            registry.async_get_or_create(
                domain=domain,
                platform=platform,
                unique_id=unique_id or suggested_object_id,
                suggested_object_id=suggested_object_id,
                original_name=entity_data.get("name"),
            )
            restored_count += 1

    connection.send_result(msg["id"], {"success": True, "restored": restored_count})


async def _async_ensure_setup(hass: HomeAssistant) -> None:
    """Registriert Services/Views/Panel/WebSocket-Kommandos genau einmal."""
    hass.data.setdefault(DOMAIN, {})
    if hass.data[DOMAIN].get(_SETUP_DONE_KEY):
        return
    hass.data[DOMAIN][_SETUP_DONE_KEY] = True

    async_register_services(hass)
    hass.http.register_view(OrphanCleanerResultsView)

    # WebSocket-API Kommandos registrieren
    websocket_api.async_register_command(hass, ws_download_backup)
    websocket_api.async_register_command(hass, ws_restore_backup)

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
    """Config Entry entfernen."""
    return True
