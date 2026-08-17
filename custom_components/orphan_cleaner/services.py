# custom_components/orphan_cleaner/services.py
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er

from .const import BACKUP_KEY, DOMAIN, EXPORT_KEY, LAST_DELETED_KEY, RESULTS_KEY
from .orphan_detector import async_find_orphans

_LOGGER = logging.getLogger(__name__)

# ===== NEU: Allowlist für geschützte Entitäten =====
ALLOWLIST = {
    "zone.home",
    "sun.sun",
    "binary_sensor.updater",
    # Füge hier weitere Entitäten hinzu, die nie gelöscht werden sollen
    # z.B. "person.ich", "person.me"
}


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
    except Exception as e:
        _LOGGER.error("Failed to write backup file: %s", e)


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
    
    if not entity_ids:
        _LOGGER.warning("No entity_ids provided for deletion.")
        return

    registry = er.async_get(hass)
    
    # Ergebnisse für das Backup und die Rückmeldung sammeln
    backup_data = []
    deleted = []
    protected = []
    not_found = []
    errors = []

    for entity_id in entity_ids:
        entry = registry.async_get(entity_id)
        
        # 1. Prüfe, ob die Entität existiert
        if entry is None:
            not_found.append(entity_id)
            continue
        
        # 2. Allowlist prüfen (NEU)
        if entity_id in ALLOWLIST:
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
        
        # 5. Löschversuch mit Fehlerbehandlung
        try:
            registry.async_remove(entity_id)
            deleted.append(entity_id)
            _LOGGER.info("Deleted: %s", entity_id)
        except Exception as e:
            errors.append({"entity_id": entity_id, "error": str(e)})
            _LOGGER.error("Failed to delete %s: %s", entity_id, e)

    # Backup erstellen (auch wenn nichts gelöscht wurde, für Transparenz)
    if backup_data:
        await _async_write_backup(hass, backup_data, backup_type="deletion")
    else:
        _LOGGER.info("No entities to back up for deletion.")

    # Ergebnisse speichern (für das Frontend)
    hass.data[DOMAIN][LAST_DELETED_KEY] = {
        "deleted": deleted,
        "protected": protected,
        "not_found": not_found,
        "errors": errors,
    }
    
    # Zusammenfassung loggen
    _LOGGER.info(
        "Deletion summary: %d deleted, %d protected, %d not found, %d errors",
        len(deleted), len(protected), len(not_found), len(errors)
    )


# ===== NEU: Service zur Überprüfung der Allowlist =====
async def async_get_allowlist_service(call: ServiceCall) -> None:
    """Gibt die aktuelle Allowlist zurück (für Debugging)."""
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["allowlist"] = list(ALLOWLIST)
    _LOGGER.info("Allowlist retrieved: %s", ALLOWLIST)


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
        schema=vol.Schema({vol.Required("entity_ids"): [str]}),
    )
    # NEU: Service für Allowlist
    hass.services.async_register(DOMAIN, "get_allowlist", async_get_allowlist_service)
