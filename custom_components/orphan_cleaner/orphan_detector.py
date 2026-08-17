# custom_components/orphan_cleaner/orphan_detector.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def async_find_orphans(
    hass: HomeAssistant,
    strict_mode: bool = False,
    min_orphan_age_hours: float = 0,
    aggressive_heuristic: bool = False,
) -> list[dict[str, Any]]:
    """Findet verwaiste Entitäten.

    Wichtig: config_entry_id, device_id, orphaned_timestamp, disabled_by und
    modified_at sind Felder der Entity Registry, keine State-Attribute.
    Deshalb wird hier immer die Registry (entity_registry.async_get)
    abgefragt, nicht hass.states.

    Args:
        strict_mode: Zusätzliche Warnung für Entitäten mit platform aber
            ohne device_id (nur wenn bereits aus anderem Grund verwaist).
        min_orphan_age_hours: Mindestalter in Stunden, bevor ein per
            orphaned_timestamp erkannter Orphan gemeldet wird. Verhindert
            False Positives kurz nach einem Neustart/Reload, wenn sich
            Integrationen noch neu verknüpfen. 0 = altes Verhalten
            (sofort melden).
        aggressive_heuristic: Zusätzliche, unabhängige Heuristik (kein
            Ersatz für strict_mode). Meldet Entitäten, die manuell
            deaktiviert (disabled_by gesetzt) UND seit mindestens
            min_orphan_age_hours nicht mehr verändert wurden
            (modified_at), auch wenn sie noch an eine config_entry/device
            gebunden sind. Höheres False-Positive-Risiko als die
            Standard-Erkennung, deshalb bewusst optional.
    """
    registry = er.async_get(hass)
    results: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).timestamp()
    min_age_seconds = min_orphan_age_hours * 3600

    for entry in registry.entities.values():
        orphaned_timestamp = entry.orphaned_timestamp
        no_links = entry.config_entry_id is None and entry.device_id is None

        reasons: list[str] = []

        if orphaned_timestamp:
            age_seconds = now - orphaned_timestamp
            if age_seconds >= min_age_seconds:
                reasons.append("orphaned_timestamp_exists")

        if no_links:
            reasons.append("no_config_or_device")

        # STRICT-MODE: zusätzliche Prüfung, nur relevant wenn die Entität
        # bereits aus einem der obigen Gründe als verwaist gilt.
        if strict_mode and reasons and entry.platform and entry.device_id is None:
            reasons.append("platform_without_device")

        # AGGRESSIVE-HEURISTIC: eigenständiges, zusätzliches Signal -
        # manuell deaktiviert und lange unverändert, unabhängig davon, ob
        # die Entität noch technisch verknüpft ist.
        if aggressive_heuristic and entry.disabled_by is not None:
            modified_at = entry.modified_at
            if modified_at is not None:
                modified_age_seconds = now - modified_at.timestamp()
                if modified_age_seconds >= min_age_seconds and "disabled_long_term" not in reasons:
                    reasons.append("disabled_long_term")

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
