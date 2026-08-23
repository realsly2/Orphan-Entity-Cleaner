# custom_components/orphan_cleaner/orphan_detector.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

# Kurze, ehrliche Einordnung pro Erkennungsgrund. "risk" ist bewusst NIE
# "safe" - jede Erkennung ist eine Heuristik, keine Garantie. Wird vom
# Frontend zum Filtern und als Hinweistext genutzt.
#
# - "review": Ein echtes Signal, aber IMMER manuell prüfen vor dem Löschen.
# - "info": Rein informativ, über delete_selected nicht aktionierbar
#   (pending_purge_by_ha existiert bereits nicht mehr in registry.entities).
REASON_INFO: dict[str, dict[str, str]] = {
    "no_config_or_device": {
        "risk": "review",
        "hint": (
            "Nicht mit einer Integration oder einem Gerät verknüpft. Meist "
            "ein echter Orphan - kann aber auch eine bewusst per YAML "
            "angelegte Entität sein (z.B. alter Template-Sensor). Vor dem "
            "Löschen prüfen: taucht sie in Automatisierungen, Skripten oder "
            "Dashboards auf?"
        ),
    },
    "platform_without_device": {
        "risk": "review",
        "hint": (
            "Hat eine Plattform-Referenz, aber kein Gerät. Schwächeres "
            "Signal, tritt nur zusammen mit einem anderen Grund auf "
            "(strict_mode)."
        ),
    },
    "disabled_long_term": {
        "risk": "review",
        "hint": (
            "Wurde von einem Menschen manuell deaktiviert und seither nicht "
            "verändert. Ein Mensch hat sie also bereits bewusst "
            "abgeschaltet - trotzdem vor dem Löschen prüfen, ob sie evtl. "
            "später wieder gebraucht wird."
        ),
    },
    "pending_purge_by_ha": {
        "risk": "info",
        "hint": (
            "Home Assistant hat diese Entität bereits intern als gelöscht "
            "markiert und entfernt sie automatisch endgültig (Standard: "
            "nach 30 Tagen). Hier nicht löschbar, da sie nicht mehr in der "
            "aktiven Registry steht - reine Information."
        ),
    },
}


async def async_find_orphans(
    hass: HomeAssistant,
    strict_mode: bool = False,
    min_orphan_age_hours: float = 0,
    aggressive_heuristic: bool = False,
) -> list[dict[str, Any]]:
    """Findet verwaiste Entitäten.

    WICHTIG (korrigiert): orphaned_timestamp existiert NICHT auf RegistryEntry
    (aktive Entitäten in registry.entities) - das war ein Fehler in einer
    früheren Version dieser Datei und führte zu:
    "'RegistryEntry' object has no attribute 'orphaned_timestamp'".

    Tatsächlich hat HA intern zwei getrennte Sammlungen:
    - registry.entities: aktive RegistryEntry-Objekte. Haben config_entry_id,
      device_id, disabled_by, modified_at - aber KEIN orphaned_timestamp.
    - registry.deleted_entities: DeletedRegistryEntry-Objekte für bereits von
      HA selbst als gelöscht markierte Entitäten, die HA automatisch nach
      ORPHANED_ENTITY_KEEP_SECONDS (Standard: 30 Tage) endgültig entfernt.
      NUR hier existiert orphaned_timestamp wirklich. Wichtig: Auch unser
      eigener delete_selected-Service löscht nicht sofort hart, sondern
      registry.async_remove() verschiebt die Entität zuerst genau hierhin -
      das 30-Tage-Fenster von HA ist also bereits das eingebaute
      Sicherheitsnetz.

    Args:
        strict_mode: Zusätzliche Warnung für Entitäten mit platform aber
            ohne device_id (nur wenn bereits aus anderem Grund verwaist).
        min_orphan_age_hours: Mindestalter in Stunden, bevor ein Eintrag
            gemeldet wird (gilt für disabled_long_term und pending_purge).
            0 = altes Verhalten (sofort melden).
        aggressive_heuristic: Zusätzliche, unabhängige Heuristik. Meldet
            aktive Entitäten, die manuell deaktiviert (disabled_by gesetzt)
            UND seit mindestens min_orphan_age_hours nicht mehr verändert
            wurden (modified_at). Höheres False-Positive-Risiko.
    """
    registry = er.async_get(hass)
    results: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).timestamp()
    min_age_seconds = min_orphan_age_hours * 3600

    # ===== 1) Aktive Entitäten ohne Verknüpfung zu config_entry/device =====
    for entry in registry.entities.values():
        no_links = entry.config_entry_id is None and entry.device_id is None

        reasons: list[str] = []
        if no_links:
            reasons.append("no_config_or_device")

        # STRICT-MODE: zusätzliche Warnung, nur relevant wenn bereits aus
        # anderem Grund verwaist.
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

        risk = "info" if all(REASON_INFO[r]["risk"] == "info" for r in reasons) else "review"

        results.append(
            {
                "entity_id": entry.entity_id,
                "name": entry.original_name or entry.entity_id,
                "platform": entry.platform or "unknown",
                "reason": ", ".join(reasons),
                "orphaned_reason": reasons,
                "risk": risk,
                "hints": [REASON_INFO[r]["hint"] for r in reasons],
                "orphaned_timestamp": None,
                "config_entry_id": entry.config_entry_id,
                "device_id": entry.device_id,
                "area_id": entry.area_id,
                "icon": entry.icon or entry.original_icon,
                "pending_purge": False,
            }
        )

    # ===== 2) Von HA bereits als gelöscht markierte Entitäten =====
    # Rein informativ: HA räumt diese automatisch nach ~30 Tagen selbst auf.
    # Diese Einträge existieren NICHT mehr in registry.entities und können
    # daher über delete_selected nicht gefunden/gelöscht werden (fallen dort
    # korrekt, aber etwas ungenau benannt, unter "not_found").
    for deleted_entry in registry.deleted_entities.values():
        orphaned_timestamp = deleted_entry.orphaned_timestamp
        if orphaned_timestamp is None:
            continue

        age_seconds = now - orphaned_timestamp
        if age_seconds < min_age_seconds:
            continue

        # getattr mit Fallback, da das Feldset von DeletedRegistryEntry sich
        # zwischen HA-Versionen unterscheidet (z.B. "name" existiert nicht in
        # allen Versionen) - entity_id/platform/config_entry_id/
        # orphaned_timestamp sind über alle geprüften Versionen hinweg stabil.
        name = getattr(deleted_entry, "name", None) or deleted_entry.entity_id

        results.append(
            {
                "entity_id": deleted_entry.entity_id,
                "name": name,
                "platform": deleted_entry.platform or "unknown",
                "reason": "pending_purge_by_ha",
                "orphaned_reason": ["pending_purge_by_ha"],
                "risk": "info",
                "hints": [REASON_INFO["pending_purge_by_ha"]["hint"]],
                "orphaned_timestamp": orphaned_timestamp,
                "config_entry_id": deleted_entry.config_entry_id,
                "device_id": None,
                "area_id": None,
                "icon": None,
                "pending_purge": True,
            }
        )

    return sorted(results, key=lambda x: x["entity_id"])
