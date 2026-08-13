# custom_components/orphan_entity_cleaner/services.py

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er

from .const import (
    BACKUP_KEY,
    DOMAIN,
    EXPORT_KEY,
    LAST_DELETED_KEY,
    RESULTS_KEY,
)
from .orphan_detector import async_find_orphans

_LOGGER = logging.getLogger(__name__)

async def async_scan_service(call: ServiceCall) -> None:
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][RESULTS_KEY] = async_find_orphans(hass)

async def async_clear_results_service(call: ServiceCall) -> None:
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][RESULTS_KEY] = []

async def async_export_results_service(call: ServiceCall) -> None:
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    results = hass.data[DOMAIN].get(RESULTS_KEY, [])
    hass.data[DOMAIN][EXPORT_KEY] = json.dumps(results, indent=2, ensure_ascii=False)

async def async_backup_results_service(call: ServiceCall) -> None:
    hass = call.hass
    hass.data.setdefault(DOMAIN, {})
    results = hass.data[DOMAIN].get(RESULTS_KEY, [])
    hass.data[DOMAIN][BACKUP_KEY] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }

async def async_delete_selected_service(call: ServiceCall) -> None:
    hass = call.hass
    entity_ids = call.data.get("entity_ids", [])

    hass.data.setdefault(DOMAIN, {})
    await async_backup_results_service(call)

    entity_reg = er.async_get(hass)
    deleted: list[str] = []

    for entity_id in entity_ids:
        entry = entity_reg.async_get(entity_id)
        if entry and entry.config_entry_id:
            _LOGGER.warning("Skipping protected entity %s", entity_id)
            continue

        if entry:
            entity_reg.async_remove(entity_id)
            deleted.append(entity_id)

    hass.data[DOMAIN][LAST_DELETED_KEY] = deleted

def async_register_services(hass: HomeAssistant) -> None:
    hass.services.async_register(DOMAIN, "scan", async_scan_service)
    hass.services.async_register(DOMAIN, "clear_results", async_clear_results_service)
    hass.services.async_register(DOMAIN, "export_results", async_export_results_service)
    hass.services.async_register(DOMAIN, "backup_results", async_backup_results_service)

    hass.services.async_register(
        DOMAIN,
        "delete_selected",
        async_delete_selected_service,
        schema=vol.Schema({vol.Required("entity_ids"): [str]}),
    )
