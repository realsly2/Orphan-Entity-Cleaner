# custom_components/orphan_cleaner/orphan_detector.py
from __future__ import annotations

from homeassistant.core import HomeAssistant


async def async_find_orphans(hass: HomeAssistant, strict_mode: bool = False) -> list[dict]:
    """
    Findet verwaiste Entitäten mit erweiterter Logik.
    
    Args:
        hass: Home Assistant Instanz
        strict_mode: Wenn True, werden zusätzliche Prüfungen durchgeführt
    """
    entities = []
    
    for entity_id, state in hass.states.async_all():
        is_orphaned = False
        orphan_reason = []
        attrs = state.attributes
        
        # 1. Prüfe orphaned_timestamp
        if "orphaned_timestamp" in attrs:
            is_orphaned = True
            orphan_reason.append("orphaned_timestamp_exists")
        
        # 2. Prüfe config_entry_id und device_id
        config_entry_id = attrs.get("config_entry_id")
        device_id = attrs.get("device_id")
        
        if config_entry_id is None and device_id is None:
            is_orphaned = True
            if "orphaned_timestamp_exists" not in orphan_reason:
                orphan_reason.append("no_config_or_device")
        
        # 3. STRICT-MODE: Zusätzliche Prüfungen
        if strict_mode and is_orphaned:
            # Entitäten mit platform-Referenz aber ohne device_id
            platform = attrs.get("platform")
            if platform and device_id is None:
                # Markiere als Warnung, aber behandle als orphaned
                orphan_reason.append("platform_without_device")
        
        # Wenn als verwaist erkannt, zur Liste hinzufügen
        if is_orphaned:
            entities.append({
                "entity_id": entity_id,
                "state": state.state,
                "friendly_name": attrs.get("friendly_name", entity_id),
                "platform": attrs.get("platform"),
                "orphaned_reason": orphan_reason,
                "orphaned_timestamp": attrs.get("orphaned_timestamp"),
                "config_entry_id": config_entry_id,
                "device_id": device_id,
            })
    
    # Nach entity_id sortieren
    return sorted(entities, key=lambda x: x["entity_id"])
