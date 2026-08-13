# custom_components/orphan_entity_cleaner/orphan_detector.py
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .const import DOMAIN, RESULTS_KEY

def is_orphan_entity(entity: Any) -> bool:
    orphaned_timestamp = getattr(entity, "orphaned_timestamp", None)
    config_entry_id = getattr(entity, "config_entry_id", None)
    device_id = getattr(entity, "device_id", None)
    state = getattr(entity, "state", None)

    if orphaned_timestamp:
        return True

    return state is None and config_entry_id is None and device_id is None

async def async_scan_orphans(hass: HomeAssistant) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    entity_registry = hass.helpers.entity_registry.async_get(hass)
    for entity_id, entry in entity_registry.entities.items():
        if getattr(entry, "orphaned_timestamp", None) or (
            entry.state is None and entry.config_entry_id is None and entry.device_id is None
        ):
            results.append(
                {
                    "entity_id": entity_id,
                    "name": entry.original_name or entry.name or entity_id,
                    "platform": entry.platform,
                    "reason": "orphaned",
                    "config_entry_id": entry.config_entry_id,
                    "device_id": entry.device_id,
                }
            )

    results.sort(key=lambda item: item["entity_id"])
    hass.data.setdefault(DOMAIN, {})[RESULTS_KEY] = results
    return results
