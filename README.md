# Orphan Cleaner

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![License](https://img.shields.io/github/license/realsly2/Orphan-Entity-Cleaner)](LICENSE)
[![Version](https://img.shields.io/github/v/release/realsly2/Orphan-Entity-Cleaner)](https://github.com/realsly2/Orphan-Entity-Cleaner/releases)

## Was sind verwaiste Entitäten?

In Home Assistant können Entitäten "verwaisten", wenn eine Integration oder ein Gerät entfernt wird, aber die dazugehörigen Entitäten in der Registry bleiben, ein Gerät nicht mehr erreichbar ist oder abgemeldet wurde oder ein Integrations-Update die Entitäts-Struktur ändert. Diese Entitäten sind nicht mehr funktional, können aber deine Entitätsliste unübersichtlich machen, die Performance beeinträchtigen oder Fehler in Logs und Automatisierungen verursachen.

## ⚠️ Wichtiger Sicherheitshinweis

Bevor du Entitäten löschst, erstelle ein vollständiges Backup deiner Home Assistant-Konfiguration (nicht nur das automatische Backup dieser Integration), überprüfe alle Automatisierungen, Skripte und Dashboards, die diese Entitäten verwenden könnten, und nutze den Dry-Run-Modus zuerst, um die Auswirkungen zu prüfen. Gelöschte Entitäten können nicht wiederhergestellt werden (außer über ein Backup)!

## Features

- 🕵️ Erkennung verwaister Entitäten (mit erweiterten Kriterien)
- 🖥️ Integriertes Sidebar-Panel für einfache Bedienung
- 🔍 Suche nach Entitäts-ID, Name oder Plattform
- ✅ Bulk-Auswahl mit Checkboxen
- 🧪 Dry-Run-Unterstützung (teste, was passieren würde)
- 💾 Export der Scan-Ergebnisse als JSON
- 🛡️ Automatisches Backup vor jeder Lösch-Aktion
- 🔒 Schutz für Entitäten mit config_entry_id
- 📋 Allowlist für kritische Entitäten (nie löschen)
- 🔍 Erweiterte Erkennungslogik mit strict_mode für zusätzliche Prüfungen
- 📄 Paginierung für den API-Endpunkt bei großen Ergebnismengen
- 🔐 Admin-only Zugriff

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realsly2&repository=Orphan-Entity-Cleaner&category=integration)

### Via HACS (empfohlen)

1. Öffne HACS in Home Assistant.
2. Klicke auf "Integrations" und dann auf die drei Punkte (⋮) oben rechts.
3. Wähle "Custom repositories" und füge diese URL hinzu: https://github.com/realsly2/Orphan-Entity-Cleaner
4. Wähle "Integration" als Kategorie.
5. Klicke auf "Installieren".
6. Starte Home Assistant neu.

### Manuelle Installation

1. Kopiere den Ordner custom_components/orphan_cleaner/ in deinen Home Assistant custom_components/-Ordner.
2. Starte Home Assistant neu.
3. Füge die Integration in Home Assistant hinzu (Konfiguration → Integrationen → "+ Integration hinzufügen" → "Orphan Cleaner").

## Nutzung

1. Öffne Orphan Cleaner im Home Assistant Sidebar (Admin-Zugriff erforderlich).
2. Klicke auf "Scan starten".
3. Überprüfe die Liste der gefundenen verwaisten Entitäten.
4. Nutze die Suche und Filter, um die Auswahl einzugrenzen.
5. Wähle die Entitäten aus, die du löschen möchtest.
6. Exportiere oder backup die Ergebnisse (optional, aber empfohlen).
7. Führe einen Dry-Run durch, um zu testen.
8. Klicke auf "Ausgewählte löschen".

## Detection Logic

Eine Entität wird als verwaist markiert, wenn entweder orphaned_timestamp im Attribut vorhanden ist oder sowohl config_entry_id als auch device_id None sind (keine Verbindung zu einer Konfiguration oder einem Gerät). Wenn der Scan mit strict_mode: true aufgerufen wird, werden zusätzliche Prüfungen durchgeführt: Entitäten mit einer platform-Referenz aber ohne device_id werden als Warnung markiert (orphaned_reason enthält "platform_without_device"). Dies hilft, potenziell problematische Entitäten zu identifizieren, die unter bestimmten Umständen verwaist sein könnten.

## Allowlist (Schutzliste)

Bestimmte Entitäten werden nie gelöscht, selbst wenn sie als verwaist erkannt werden. Standardmäßig geschützt sind zone.home, sun.sun und binary_sensor.updater. Die Liste kann in der services.py unter ALLOWLIST erweitert werden. So fügst du eigene Entitäten hinzu:

ALLOWLIST = {
    "zone.home",
    "person.ich",  # Dein eigener Name
    "sensor.mein_wichtiger_sensor",
}

Um die aktuelle Allowlist abzurufen, nutze den Service: curl -X POST http://homeassistant.local:8123/api/services/orphan_cleaner/get_allowlist

## Services

Die folgenden Services stehen zur Verfügung:

- orphan_cleaner.scan: Startet einen neuen Scan (optional mit strict_mode: true)
- orphan_cleaner.delete_selected: Löscht die ausgewählten Entitäten (erfordert entity_ids-Parameter)
- orphan_cleaner.clear_results: Löscht die gespeicherten Scan-Ergebnisse
- orphan_cleaner.export_results: Exportiert die Ergebnisse als JSON-Datei
- orphan_cleaner.backup_results: Erstellt ein Backup der Ergebnisse
- orphan_cleaner.get_allowlist: Gibt die aktuelle Allowlist zurück (für Debugging)

### Service-Beispiele

Scan mit strict_mode:
service: orphan_cleaner.scan
data:
  strict_mode: true

Löschen von Entitäten:
service: orphan_cleaner.delete_selected
data:
  entity_ids:
    - sensor.old_device
    - binary_sensor.unused_sensor

## API-Endpunkte

- GET /api/orphan_cleaner/results: Alle Scan-Ergebnisse abrufen (mit Paginierung)
- DELETE /api/orphan_cleaner/results: Alle Ergebnisse löschen
- GET /orphan-cleaner: Das Sidebar-Panel (HTML)

### Paginierung

Für große Ergebnismengen unterstützt der Endpunkt Paginierung:

Erste 10 Ergebnisse: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10"
10 Ergebnisse ab Offset 20: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10&offset=20"

Die Antwort enthält Metadaten:
{
  "total": 150,
  "offset": 20,
  "limit": 10,
  "results": [ ... ]
}

## Fehlerbehebung

Scan findet keine Entitäten? Stelle sicher, dass du tatsächlich alte Integrationen oder Geräte entfernt hast, und prüfe, ob die Entitäten wirklich keine config_entry_id und device_id mehr haben (z.B. über den Entwickler-Tools → Zustände).

Entitäten lassen sich nicht löschen? Prüfe, ob sie in der Allowlist stehen, ob sie eine config_entry_id haben (Schutzmechanismus) und ob du als Admin angemeldet bist.

API gibt 404 zurück? Die Integration muss korrekt installiert und aktiviert sein. Prüfe die URL: http://[deine-IP]:8123/api/orphan_cleaner/results und starte Home Assistant neu.

Backup wird nicht erstellt? Prüfe die Schreibrechte im Home Assistant Konfigurationsverzeichnis – der Ordner muss beschreibbar sein.

## Development

### Voraussetzungen
- Home Assistant 2026.8.1 oder neuer
- Python 3.10 oder neuer

### Tests ausführen
pytest -q

### Workflow für Beiträge
1. Forke das Repository.
2. Erstelle einen Feature-Branch.
3. Füge Tests für neue Funktionen hinzu.
4. Stelle sicher, dass alle Tests bestehen.
5. Erstelle einen Pull Request.

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die LICENSE Datei für Details.

## Danksagung

- Home Assistant Community für die großartige Arbeit.
- Alle Nutzer, die Feedback und Verbesserungsvorschläge einbringen.
