# custom_components/orphan_entity_cleaner/orphan_detector.py

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

def async_find_orphans(hass: HomeAssistant) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for entity_id, state in hass.states.async_all().items():
        attrs = state.attributes or {}
        config_entry_id = attrs.get("config_entry_id")
        device_id = attrs.get("device_id")
        orphaned_timestamp = attrs.get("orphaned_timestamp")

        reason = None
        if orphaned_timestamp:
            reason = "orphaned_timestamp"
        elif not state.state and not config_entry_id and not device_id:
            reason = "no_state_no_config_entry_no_device"

        if reason:
            results.append(
                {
                    "entity_id": entity_id,
                    "name": attrs.get("friendly_name", entity_id),
                    "platform": attrs.get("platform", "unknown"),
                    "reason": reason,
                    "config_entry_id": config_entry_id,
                    "device_id": device_id,
                }
            )

    results.sort(key=lambda item: item["entity_id"])
    return results
