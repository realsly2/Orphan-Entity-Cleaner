# custom_components/orphan_cleaner/services.py
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import BACKUP_KEY, DOMAIN, EXPORT_KEY, LAST_DELETED_KEY, RESULTS_KEY
from .orphan_detector import async_find_orphans

_LOGGER = logging.getLogger(__name__)

DEFAULT_ALLOWLIST = {
    "zone.home",
    "sun.sun",
    "binary_sensor.updater",
}

# Backwards-compatible alias used by older code/tests.
ALLOWLIST = set(DEFAULT_ALLOWLIST)


def get_allowlist(hass: HomeAssistant) -> set[str]:
    """Return the allowlist for this instance, initialized from defaults if needed."""
    hass.data.setdefault(DOMAIN, {})
    stored = hass.data[DOMAIN].get("allowlist")
    if stored is None:
        hass.data[DOMAIN]["allowlist"] = sorted(DEFAULT_ALLOWLIST)
        return set(DEFAULT_ALLOWLIST)
    if isinstance(stored, set):
        allowlist = stored
    else:
        allowlist = set(stored)
    hass.data[DOMAIN]["allowlist"] = sorted(allowlist)
    return allowlist


def set_allowlist(hass: HomeAssistant, entity_ids: list[str]) -> list[str]:
    """Persist a new allowlist value for this Home Assistant instance."""
    allowlist = get_allowlist(hass)
    allowlist.update(entity_ids)
    hass.data[DOMAIN]["allowlist"] = sorted(allowlist)
    return sorted(allowlist)


async def async_scan_service(call: ServiceCall) -> None:
    """Führt einen Scan mit erweiterter Logik durch."""
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})

    strict_mode = call.data.get("strict_mode", False)
    min_orphan_age_hours = call.data.get("min_orphan_age_hours", 0)
    aggressive_heuristic = call.data.get("aggressive_heuristic", False)

    results = await async_find_orphans(
        hass,
        strict_mode=strict_mode,
        min_orphan_age_hours=min_orphan_age_hours,
        aggressive_heuristic=aggressive_heuristic,
    )

    hass.data[DOMAIN][RESULTS_KEY] = results
    _LOGGER.info("Scan completed. Found %d orphaned entities.", len(results))


async def async_clear_results_service(call: ServiceCall) -> None:
    """Löscht die gespeicherten Scan-Ergebnisse."""
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][RESULTS_KEY] = []
    _LOGGER.info("Results cleared.")


async def async_export_results_service(call: ServiceCall) -> None:
    """Exportiert die aktuellen Ergebnisse als JSON-String."""
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    results = hass.data[DOMAIN].get(RESULTS_KEY, [])
    hass.data[DOMAIN][EXPORT_KEY] = json.dumps(results, indent=2, ensure_ascii=False)
    _LOGGER.info("Results exported.")


# ===== NEU: Verbesserte Backup-Funktion mit Fehlerbehandlung =====
async def _async_write_backup(hass: HomeAssistant, results: list[dict], backup_type: str = "deletion") -> None:
    """Erstellt ein Backup mit Metadaten."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": backup_type,
        "results": results,
    }
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][BACKUP_KEY] = payload

    import uuid

    # Use high-resolution UTC timestamp plus a UUID suffix to avoid collisions
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    filename = f"orphan_cleaner_backup_{timestamp}_{uuid.uuid4().hex}.json"
    root_path = Path(hass.config.path())
    backup_dir = root_path / "orphan_cleaner_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    root_target = root_path / filename
    subdir_target = backup_dir / filename

    def _atomic_write_file(path_str: str, text: str):
        p = Path(path_str)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        # Use rename which is atomic on most OSes when target on same filesystem
        tmp.replace(p)

    try:
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)
        # Write only into the backup subdirectory (avoid writing directly into root by default)
        await hass.async_add_executor_job(_atomic_write_file, str(subdir_target), serialized)
        # Also keep a copy in the config root for compatibility with older expectations
        await hass.async_add_executor_job(_atomic_write_file, str(root_target), serialized)
        hass.data[DOMAIN]["last_backup_path"] = str(subdir_target)
        _LOGGER.info("Backup created: %s", filename)
    except OSError as err:
        _LOGGER.error("Failed to write backup file: %s", err)
        raise HomeAssistantError("Backup file could not be written") from err


async def async_backup_results_service(call: ServiceCall) -> None:
    """Erstellt ein Backup der aktuellen Scan-Ergebnisse."""
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    results = hass.data[DOMAIN].get(RESULTS_KEY, [])
    await _async_write_backup(hass, results, backup_type="scan")


# ===== NEU: Erweiterte Lösch-Funktion mit Allowlist und besseren Rückgaben =====
async def async_delete_selected_service(call: ServiceCall) -> None:
    """Löscht ausgewählte Entitäten mit erweiterten Sicherheitschecks."""
    hass = call.hass
    entity_ids = call.data.get("entity_ids", [])
    dry_run = call.data.get("dry_run", False)

    if not entity_ids:
        _LOGGER.warning("No entity_ids provided for deletion.")
        return

    registry = er.async_get(hass)
    scan_results = hass.data.get(DOMAIN, {}).get(RESULTS_KEY, [])
    current_allowlist = get_allowlist(hass)
    deletable_ids = {
        result["entity_id"]
        for result in scan_results
        if result.get("entity_id") and not result.get("pending_purge", False)
    }

    # Ergebnisse für das Backup und die Rückmeldung sammeln.
    backup_data = []
    to_delete: list[tuple[str, object]] = []
    deleted = []
    protected = []
    not_found = []
    errors = []

    for entity_id in entity_ids:
        entry = registry.async_get(entity_id)
        scan_result = next(
            (result for result in scan_results if result.get("entity_id") == entity_id),
            None,
        )

        # 1. Prüfe, ob die Entität existiert
        if entry is None:
            not_found.append(entity_id)
            continue

        # 2. Schutz durch config_entry_id (bestehend)
        if entry.config_entry_id:
            protected.append(entity_id)
            _LOGGER.info("Protected by config_entry_id: %s", entity_id)
            continue

        # 3. Allowlist hat absolute Priorität und schützt die Entität immer.
        if entity_id in current_allowlist:
            protected.append(entity_id)
            _LOGGER.info("Protected by allowlist: %s", entity_id)
            continue

        # 4. Prüfe, ob die Entität überhaupt zur Löschung vorgesehen ist
        #    (nur gemeldete Scan-Ergebnisse gelten).
        if entity_id not in deletable_ids and scan_result is None:
            not_found.append(entity_id)
            continue

        entity_entry = {
            "entity_id": entry.entity_id,
            "name": entry.original_name or entry.entity_id,
            "platform": entry.platform or "unknown",
            "config_entry_id": entry.config_entry_id,
            "device_id": entry.device_id,
            "unique_id": getattr(entry, "unique_id", None),
            "domain": getattr(entry, "domain", entry.entity_id.split('.', 1)[0]),
        }
        backup_data.append(entity_entry)
        if not dry_run:
            to_delete.append((entity_id, entry))

    # Backup vor dem eigentlichen Entfernen erzeugen, damit keine Löschung ohne
    # Sicherung erfolgen kann.
    if backup_data and not dry_run:
        await _async_write_backup(hass, backup_data, backup_type="deletion")
    elif not dry_run:
        _LOGGER.info("No entities to back up for deletion.")

    if not dry_run:
        for entity_id, _entry in to_delete:
            try:
                registry.async_remove(entity_id)
                deleted.append(entity_id)
                _LOGGER.info("Deleted: %s", entity_id)
            except Exception as exc:
                errors.append({"entity_id": entity_id, "error": str(exc)})
                _LOGGER.error("Failed to delete %s: %s", entity_id, exc)

    # Ergebnisse speichern (für das Frontend)
    hass.data[DOMAIN][LAST_DELETED_KEY] = {
        "deleted": deleted,
        "would_delete": [item["entity_id"] for item in backup_data] if dry_run else [],
        "protected": protected,
        "not_found": not_found,
        "errors": errors,
        "dry_run": dry_run,
    }

    # Zusammenfassung loggen
    _LOGGER.info(
        "Deletion summary: %d deleted, %d protected, %d not found, %d errors",
        len(deleted), len(protected), len(not_found), len(errors)
    )


# ===== Service zur Überprüfung der Allowlist =====


async def async_get_allowlist_service(call: ServiceCall) -> Dict[str, Any]:
    """Return the current allowlist as a normal service response."""
    allowlist = sorted(get_allowlist(call.hass))
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["allowlist"] = allowlist
    _LOGGER.info("Allowlist retrieved: %s", allowlist)
    # Return a dict to satisfy Home Assistant's typed service response shape
    return {"allowlist": allowlist}


async def async_update_allowlist_service(call: ServiceCall) -> Dict[str, Any]:
    """Add or remove entities from the allowlist."""
    hass = call.hass
    entity_ids = call.data.get("entity_ids", [])
    mode = call.data.get("mode", "add")
    allowlist = set(get_allowlist(hass))

    if mode == "remove":
        allowlist.difference_update(entity_ids)
    else:
        allowlist.update(entity_ids)

    hass.data[DOMAIN]["allowlist"] = sorted(allowlist)
    return {"allowlist": sorted(allowlist)}


def async_register_services(hass: HomeAssistant) -> None:
    """Registriert alle Services mit erweiterten Schemas."""
    hass.services.async_register(
        DOMAIN,
        "scan",
        async_scan_service,
        schema=vol.Schema({
            vol.Optional("strict_mode", default=False): bool,
            vol.Optional("min_orphan_age_hours", default=0): vol.All(
                vol.Coerce(float), vol.Range(min=0)
            ),
            vol.Optional("aggressive_heuristic", default=False): bool,
        })
    )
    hass.services.async_register(DOMAIN, "clear_results", async_clear_results_service)
    hass.services.async_register(DOMAIN, "export_results", async_export_results_service)
    hass.services.async_register(DOMAIN, "backup_results", async_backup_results_service)
    hass.services.async_register(
        DOMAIN,
        "delete_selected",
        async_delete_selected_service,
        schema=vol.Schema({
            vol.Required("entity_ids"): [str],
            vol.Optional("dry_run", default=False): bool,
        }),
    )
    # Service für Allowlist
    hass.services.async_register(
        DOMAIN,
        "get_allowlist",
        async_get_allowlist_service,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "update_allowlist",
        async_update_allowlist_service,
        schema=vol.Schema({
            vol.Required("entity_ids"): [str],
            vol.Optional("mode", default="add"): vol.In(["add", "remove"]),
        }),
        supports_response=SupportsResponse.ONLY,
    )

    # Backup-related services
    hass.services.async_register(DOMAIN, "list_backups", async_list_backups_service)
    hass.services.async_register(
        DOMAIN,
        "restore_from_backup",
        async_restore_from_backup_service,
        schema=vol.Schema({vol.Required("filename"): str}),
    )


# ===== Services for backup listing and restore =====
async def async_list_backups_service(call: ServiceCall) -> None:
    """List backup files in the configured backup directory and store summary in hass.data."""
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    root_dir = Path(hass.config.path())
    backup_dir = Path(hass.config.path("orphan_cleaner_backups"))
    backups_summary: list[dict] = []
    seen: set[Path] = set()

    for search_dir in (root_dir, backup_dir):
        if not search_dir.exists() or not search_dir.is_dir():
            continue
        for p in sorted(search_dir.glob("orphan_cleaner_backup_*.json")):
            if p in seen:
                continue
            seen.add(p)
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
                results = payload.get("results") or []
                backups_summary.append({"filename": p.name, "count": len(results)})
            except Exception:  # pragma: no cover - defensive
                backups_summary.append({"filename": p.name, "count": 0})

    hass.data[DOMAIN]["backups"] = backups_summary


async def async_restore_from_backup_service(call: ServiceCall) -> None:
    """Restore entities from a named backup file located in the configured backup directory.

    The function rejects path-traversal attempts and missing files silently (no last_restore set).
    """
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    # Be explicit about the expected data typing to satisfy type checkers
    data: dict[str, Any] = call.data or {}
    filename = data.get("filename")
    if not filename or Path(filename).name != filename or ".." in filename:
        _LOGGER.warning("Refusing to restore from suspicious filename: %s", filename)
        return

    candidate_paths = [
        Path(hass.config.path("orphan_cleaner_backups", filename)),
        Path(hass.config.path(filename)),
    ]
    backup_path = next((p for p in candidate_paths if p.exists() and p.is_file()), None)
    if backup_path is None:
        _LOGGER.warning("Backup file not found for: %s", filename)
        return

    try:
        payload = json.loads(backup_path.read_text(encoding="utf-8"))
    except Exception as err:
        _LOGGER.error("Failed to read backup file %s: %s", backup_path, err)
        return

    results = payload.get("results") or []
    registry = er.async_get(hass)
    restored: list[str] = []
    skipped_existing: list[str] = []
    errors: list[dict] = []

    for item in results:
        entity_id = item.get("entity_id")
        if not entity_id:
            continue
        # If already exists, skip
        if registry.async_get(entity_id):
            skipped_existing.append(entity_id)
            continue

        domain = item.get("domain") or entity_id.split(".", 1)[0]
        suggested_object_id = entity_id.split(".", 1)[1] if "." in entity_id else None
        unique_id = item.get("unique_id")
        platform = item.get("platform")
        original_name = item.get("name")

        try:
            created = registry.async_get_or_create(
                domain=domain,
                platform=platform,
                unique_id=unique_id,
                suggested_object_id=suggested_object_id,
                original_name=original_name,
            )
            restored.append(created.entity_id)
        except Exception as err:  # pragma: no cover - defensive
            errors.append({"entity_id": entity_id, "error": str(err)})

    if restored or skipped_existing or errors:
        hass.data[DOMAIN]["last_restore"] = {
            "restored": restored,
            "skipped_existing": skipped_existing,
            "errors": errors,
        }
