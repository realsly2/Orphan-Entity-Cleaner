# custom_components/orphan_entity_cleaner/services.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, RESULTS_KEY, EXPORT_KEY, BACKUP_KEY, LAST_DELETED_KEY


def _get_results(hass: HomeAssistant) -> list[dict[str, Any]]:
    return hass.data.setdefault(DOMAIN, {}).get(RESULTS_KEY, [])


async def async_scan_service(call: ServiceCall) -> None:
    hass = call.hass
    from .orphan_detector import async_scan_orphans

    await async_scan_orphans(hass)


async def async_clear_results_service(call: ServiceCall) -> None:
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})[RESULTS_KEY] = []


async def async_export_results_service(call: ServiceCall) -> None:
    hass = call.hass
    results = _get_results(hass)
    hass.data.setdefault(DOMAIN, {})[EXPORT_KEY] = json.dumps(results, indent=2, ensure_ascii=False)


async def async_backup_results_service(call: ServiceCall) -> None:
    hass = call.hass
    results = _get_results(hass)
    backup_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    hass.data.setdefault(DOMAIN, {})[BACKUP_KEY] = backup_payload


async def async_delete_selected_service(call: ServiceCall) -> None:
    hass = call.hass
    entity_ids = call.data.get("entity_ids", [])
    entity_registry = hass.helpers.entity_registry.async_get(hass)

    await async_backup_results_service(call)

    deleted: list[str] = []
    for entity_id in entity_ids:
        entry = entity_registry.async_get(entity_id)
        if entry is None:
            continue
        if entry.config_entry_id:
            hass.logger.warning("Skipping protected entity with config_entry_id: %s", entity_id)
            continue
        entity_registry.async_remove(entity_id)
        deleted.append(entity_id)

    hass.data.setdefault(DOMAIN, {})[LAST_DELETED_KEY] = deleted


async def async_register_services(hass: HomeAssistant) -> None:
    hass.services.async_register(DOMAIN, "scan", async_scan_service)
    hass.services.async_register(DOMAIN, "clear_results", async_clear_results_service)
    hass.services.async_register(DOMAIN, "export_results", async_export_results_service)
    hass.services.async_register(DOMAIN, "backup_results", async_backup_results_service)
    hass.services.async_register(DOMAIN, "delete_selected", async_delete_selected_service)
