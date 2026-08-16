# custom_components/orphan_cleaner/orphan_detector.py
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def async_find_orphans(hass: HomeAssistant, strict_mode: bool = False) -> list[dict[str, Any]]:
    """Findet verwaiste Entitäten.

    Wichtig: config_entry_id, device_id und orphaned_timestamp sind Felder
    der Entity Registry, keine State-Attribute. Deshalb wird hier immer die
    Registry (entity_registry.async_get) abgefragt, nicht hass.states.
    """
    registry = er.async_get(hass)
    results: list[dict[str, Any]] = []

    for entry in registry.entities.values():
        orphaned_timestamp = entry.orphaned_timestamp
        no_links = entry.config_entry_id is None and entry.device_id is None

        reasons: list[str] = []
        if orphaned_timestamp:
            reasons.append("orphaned_timestamp_exists")
        if no_links:
            reasons.append("no_config_or_device")

        # STRICT-MODE: zusätzliche Prüfung, nur relevant wenn die Entität
        # bereits aus einem der obigen Gründe als verwaist gilt.
        if strict_mode and reasons and entry.platform and entry.device_id is None:
            reasons.append("platform_without_device")

        if not reasons:
            continue

        results.append(
            {
                "entity_id": entry.entity_id,
                "name": entry.original_name or entry.entity_id,
                "platform": entry.platform or "unknown",
                "reason": ", ".join(reasons),
                "orphaned_reason": reasons,
                "orphaned_timestamp": orphaned_timestamp,
                "config_entry_id": entry.config_entry_id,
                "device_id": entry.device_id,
            }
        )

    return sorted(results, key=lambda x: x["entity_id"])
