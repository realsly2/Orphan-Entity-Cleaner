# custom_components/orphan_cleaner/services.py
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path

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
async def _async_write_backup(hass: HomeAssistant, results: list[dict], 
                              backup_type: str = "deletion") -> None:
    """Erstellt ein Backup mit Metadaten."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": backup_type,
        "results": results,
    }
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][BACKUP_KEY] = payload

    filename = f"orphan_cleaner_backup_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    try:
        await hass.async_add_executor_job(
            Path(hass.config.path(filename)).write_text,
            json.dumps(payload, indent=2, ensure_ascii=False),
            "utf-8",
        )
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

    # Ergebnisse für das Backup und die Rückmeldung sammeln
    backup_data = []
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
        current_is_orphan = bool(
            entry is not None and entry.config_entry_id is None and entry.device_id is None
        )

        if entity_id not in deletable_ids and not current_is_orphan:
            not_found.append(entity_id)
            continue

        # 1. Prüfe, ob die Entität existiert
        if entry is None:
            not_found.append(entity_id)
            continue

        # 2. Allowlist prüfen
        if entity_id in current_allowlist:
            protected.append(entity_id)
            _LOGGER.info("Protected by allowlist: %s", entity_id)
            continue

        # 3. Schutz durch config_entry_id (bestehend)
        if entry.config_entry_id:
            protected.append(entity_id)
            _LOGGER.info("Protected by config_entry_id: %s", entity_id)
            continue

        # 4. Backup-Daten sammeln
        backup_data.append({
            "entity_id": entry.entity_id,
            "name": entry.original_name or entry.entity_id,
            "platform": entry.platform or "unknown",
            "config_entry_id": entry.config_entry_id,
            "device_id": entry.device_id,
        })

        if dry_run:
            continue

        # 5. Löschversuch mit Fehlerbehandlung
        try:
            registry.async_remove(entity_id)
            deleted.append(entity_id)
            _LOGGER.info("Deleted: %s", entity_id)
        except Exception as e:
            errors.append({"entity_id": entity_id, "error": str(e)})
            _LOGGER.error("Failed to delete %s: %s", entity_id, e)

    # Backup erstellen (auch wenn nichts gelöscht wurde, für Transparenz)
    if backup_data and not dry_run:
        await _async_write_backup(hass, backup_data, backup_type="deletion")
    else:
        _LOGGER.info("No entities to back up for deletion.")

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
async def async_get_allowlist_service(call: ServiceCall) -> list[str]:
    """Return the current allowlist as a normal service response."""
    allowlist = sorted(get_allowlist(call.hass))
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["allowlist"] = allowlist
    _LOGGER.info("Allowlist retrieved: %s", allowlist)
    return allowlist


async def async_update_allowlist_service(call: ServiceCall) -> list[str]:
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
    return sorted(allowlist)


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
