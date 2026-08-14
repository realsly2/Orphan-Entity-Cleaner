# custom_components/orphan_cleaner/orphan_detector.py
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


def async_find_orphans(hass: HomeAssistant) -> list[dict[str, Any]]:
    registry = er.async_get(hass)
    results: list[dict[str, Any]] = []

    for entry in registry.entities.values():
        orphaned_timestamp = entry.orphaned_timestamp
        no_links = entry.config_entry_id is None and entry.device_id is None

        if not orphaned_timestamp and not no_links:
            continue

        results.append(
            {
                "entity_id": entry.entity_id,
                "name": entry.original_name or entry.entity_id,
                "platform": entry.platform or "unknown",
                "reason": "orphaned_timestamp" if orphaned_timestamp else "no_config_entry_no_device",
                "config_entry_id": entry.config_entry_id,
                "device_id": entry.device_id,
            }
        )

    return sorted(results, key=lambda x: x["entity_id"])
