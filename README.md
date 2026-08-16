# Orphan Cleaner

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![License](https://img.shields.io/github/license/realsly2/Orphan-Entity-Cleaner)](LICENSE)
[![Version](https://img.shields.io/github/v/release/realsly2/Orphan-Entity-Cleaner)](https://github.com/realsly2/Orphan-Entity-Cleaner/releases)


---

## English Version

### What are orphaned entities?

In Home Assistant, entities can become "orphaned" when an integration or device is removed but the associated entities remain in the registry, a device is no longer reachable or has been unpaired, or an integration update changes the entity structure. These entities are no longer functional but can clutter your entity list, impact performance, or cause errors in logs and automations.

### ⚠️ Important Safety Notice

Before deleting entities, create a full backup of your Home Assistant configuration (not just the automatic backup from this integration), review all automations, scripts, and dashboards that might use these entities, and use the dry-run mode first to check the impact. Deleted entities cannot be recovered (except via a backup)!

### Features

- 🕵️ Detection of orphaned entities (with extended criteria)
- 🖥️ Built-in sidebar panel for easy operation
- 🔍 Search by entity ID, name, or platform
- ✅ Bulk selection with checkboxes
- 🧪 Dry-run support (test what would happen)
- 💾 Export scan results as JSON
- 🛡️ Automatic backup before any deletion action
- 🔒 Protection for entities with config_entry_id
- 📋 Allowlist for critical entities (never delete)
- 🔍 Extended detection logic with strict_mode for additional checks
- 📄 Pagination for the API endpoint with large result sets
- 🔐 Admin-only access

### Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realsly2&repository=Orphan-Entity-Cleaner&category=integration)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orphan_cleaner)


#### Option 1: Via HACS (recommended)
1. Open HACS in Home Assistant.
2. Click on "Integrations" → three dots (⋮) → "Custom repositories".
3. Add this URL: https://github.com/realsly2/Orphan-Entity-Cleaner
4. Select "Integration" as the category.
5. Click "Install" and restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration**, search for "Orphan Cleaner" and confirm. No YAML editing required.

#### Option 2: Manual Installation
1. Download the custom_components/orphan_cleaner/ folder from this repository.
2. Copy it into your Home Assistant custom_components/ directory.
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration**, search for "Orphan Cleaner" and confirm.

Alternatively, for legacy YAML setup, add the following line to your configuration.yaml instead of using the UI:
   orphan_cleaner:

After setup, you will find the Orphan Cleaner panel in your sidebar.

### Usage

1. Open Orphan Cleaner from the sidebar (admin access required).
2. Click "Start Scan".
3. Review the detected entities.
4. Use search and filters to narrow down your selection.
5. Select the entities you want to delete.
6. Export or backup the results (optional but recommended).
7. Run a dry-run to test.
8. Click "Delete Selected".

### Detection Logic

An entity is marked as orphaned if orphaned_timestamp exists in its attributes, OR both config_entry_id and device_id are None (no connection to a configuration or device). When the scan is called with strict_mode: true, additional checks are performed: entities with a platform reference but without device_id are marked as a warning (orphaned_reason contains "platform_without_device"). This helps identify potentially problematic entities that might be orphaned under certain circumstances.

### Allowlist (Protection List)

Certain entities are never deleted, even if they are detected as orphaned. By default, zone.home, sun.sun, and binary_sensor.updater are protected. The list can be extended in services.py under ALLOWLIST. To add your own entities:

ALLOWLIST = {
    "zone.home",
    "person.ich",  # Your own name
    "sensor.my_important_sensor",
}

To retrieve the current allowlist, use the service: curl -X POST http://homeassistant.local:8123/api/services/orphan_cleaner/get_allowlist

### Services

The following services are available:

- orphan_cleaner.scan: Starts a new scan (optionally with strict_mode: true)
- orphan_cleaner.delete_selected: Deletes the selected entities (requires entity_ids parameter)
- orphan_cleaner.clear_results: Clears the saved scan results
- orphan_cleaner.export_results: Exports the results as a JSON file
- orphan_cleaner.backup_results: Creates a backup of the results
- orphan_cleaner.get_allowlist: Returns the current allowlist (for debugging)

Service Examples:

Scan with strict_mode:
service: orphan_cleaner.scan
data:
  strict_mode: true

Delete entities:
service: orphan_cleaner.delete_selected
data:
  entity_ids:
    - sensor.old_device
    - binary_sensor.unused_sensor

### API Endpoints

- GET /api/orphan_cleaner/results: Retrieve all scan results (with pagination)
- DELETE /api/orphan_cleaner/results: Delete all results
- GET /orphan-cleaner: The sidebar panel (HTML)

Pagination:

First 10 results: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10"
10 results from offset 20: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10&offset=20"

The response includes metadata:
{
  "total": 150,
  "offset": 20,
  "limit": 10,
  "results": [ ... ]
}

### Troubleshooting

Scan finds no entities? Make sure you have actually removed old integrations or devices, and check if the entities really have no config_entry_id and device_id (e.g., via Developer Tools → States).

Entities cannot be deleted? Check if they are on the allowlist, if they have a config_entry_id (protection mechanism), and if you are logged in as admin.

API returns 404? The integration must be correctly installed and active. Check the URL: http://[your-IP]:8123/api/orphan_cleaner/results and restart Home Assistant.

Backup is not created? Check write permissions in the Home Assistant configuration directory – the folder must be writable.

### Development

Requirements:
- Home Assistant 2026.8.1 or newer
- Python 3.10 or newer

Run tests:
pytest -q

Contribution:
1. Fork the repository.
2. Create a feature branch.
3. Add tests for new features.
4. Ensure all tests pass.
5. Create a pull request.

### License

This project is licensed under the MIT License - see the LICENSE file for details.

### Acknowledgments

- Home Assistant Community for the great work.
- All users who provide feedback and suggestions.

---

## Deutsche Version

### Was sind verwaiste Entitäten?

In Home Assistant können Entitäten "verwaisten", wenn eine Integration oder ein Gerät entfernt wird aber die dazugehörigen Entitäten in der Registry bleiben, ein Gerät nicht mehr erreichbar ist oder abgemeldet wurde, oder ein Integrations-Update die Entitäts-Struktur ändert. Diese Entitäten sind nicht mehr funktional, können aber deine Entitätsliste unübersichtlich machen, die Performance beeinträchtigen oder Fehler in Logs und Automatisierungen verursachen.

### ⚠️ Wichtiger Sicherheitshinweis

Bevor du Entitäten löschst, erstelle ein vollständiges Backup deiner Home Assistant-Konfiguration (nicht nur das automatische Backup dieser Integration), überprüfe alle Automatisierungen, Skripte und Dashboards, die diese Entitäten verwenden könnten, und nutze den Dry-Run-Modus zuerst, um die Auswirkungen zu prüfen. Gelöschte Entitäten können nicht wiederhergestellt werden (außer über ein Backup)!

### Features

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

### Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realsly2&repository=Orphan-Entity-Cleaner&category=integration)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orphan_cleaner)


#### Option 1: Via HACS (empfohlen)
1. Öffne HACS in Home Assistant.
2. Klicke auf "Integrationen" und dann auf die drei Punkte (⋮) oben rechts.
3. Wähle "Benutzerdefinierte Repositories" und füge diese URL hinzu: https://github.com/realsly2/Orphan-Entity-Cleaner
4. Wähle "Integration" als Kategorie.
5. Klicke auf "Installieren".
6. Starte Home Assistant neu.
7. Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen**, suche nach "Orphan Cleaner" und bestätige. Keine YAML-Bearbeitung nötig.

#### Option 2: Manuelle Installation
1. Lade den Ordner custom_components/orphan_cleaner/ aus diesem Repository herunter.
2. Kopiere ihn in dein Home Assistant custom_components/-Verzeichnis.
3. Starte Home Assistant neu.
4. Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen**, suche nach "Orphan Cleaner" und bestätige.

Alternativ, für die klassische YAML-Einrichtung, füge stattdessen diese Zeile in deine configuration.yaml ein:
   orphan_cleaner:

Nach der Einrichtung findest du das Orphan Cleaner-Panel in deiner Seitenleiste.

### Nutzung

1. Öffne Orphan Cleaner über die Seitenleiste (Admin-Zugriff erforderlich).
2. Klicke auf "Scan starten".
3. Überprüfe die erkannten Entitäten.
4. Nutze die Suche und Filter, um deine Auswahl einzugrenzen.
5. Wähle die Entitäten aus, die du löschen möchtest.
6. Exportiere oder erstelle ein Backup der Ergebnisse (optional, aber empfohlen).
7. Führe einen Dry-Run durch, um zu testen.
8. Klicke auf "Ausgewählte löschen".

### Erkennungslogik

Eine Entität wird als verwaist markiert, wenn entweder orphaned_timestamp im Attribut vorhanden ist, oder sowohl config_entry_id als auch device_id None sind (keine Verbindung zu einer Konfiguration oder einem Gerät). Wenn der Scan mit strict_mode: true aufgerufen wird, werden zusätzliche Prüfungen durchgeführt: Entitäten mit einer Plattform-Referenz aber ohne device_id werden als Warnung markiert (orphaned_reason enthält "platform_without_device"). Dies hilft, potenziell problematische Entitäten zu identifizieren, die unter bestimmten Umständen verwaist sein könnten.

### Allowlist (Schutzliste)

Bestimmte Entitäten werden nie gelöscht, selbst wenn sie als verwaist erkannt werden. Standardmäßig geschützt sind zone.home, sun.sun und binary_sensor.updater. Die Liste kann in der services.py unter ALLOWLIST erweitert werden. So fügst du eigene Entitäten hinzu:

ALLOWLIST = {
    "zone.home",
    "person.ich",  # Dein eigener Name
    "sensor.mein_wichtiger_sensor",
}

Um die aktuelle Allowlist abzurufen, nutze den Service: curl -X POST http://homeassistant.local:8123/api/services/orphan_cleaner/get_allowlist

### Services

Die folgenden Services stehen zur Verfügung:

- orphan_cleaner.scan: Startet einen neuen Scan (optional mit strict_mode: true)
- orphan_cleaner.delete_selected: Löscht die ausgewählten Entitäten (erfordert entity_ids-Parameter)
- orphan_cleaner.clear_results: Löscht die gespeicherten Scan-Ergebnisse
- orphan_cleaner.export_results: Exportiert die Ergebnisse als JSON-Datei
- orphan_cleaner.backup_results: Erstellt ein Backup der Ergebnisse
- orphan_cleaner.get_allowlist: Gibt die aktuelle Allowlist zurück (für Debugging)

Service-Beispiele:

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

### API-Endpunkte

- GET /api/orphan_cleaner/results: Alle Scan-Ergebnisse abrufen (mit Paginierung)
- DELETE /api/orphan_cleaner/results: Alle Ergebnisse löschen
- GET /orphan-cleaner: Das Sidebar-Panel (HTML)

Paginierung:

Erste 10 Ergebnisse: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10"
10 Ergebnisse ab Offset 20: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10&offset=20"

Die Antwort enthält Metadaten:
{
  "total": 150,
  "offset": 20,
  "limit": 10,
  "results": [ ... ]
}

### Fehlerbehebung

Scan findet keine Entitäten? Stelle sicher, dass du tatsächlich alte Integrationen oder Geräte entfernt hast, und prüfe, ob die Entitäten wirklich keine config_entry_id und device_id mehr haben (z.B. über den Entwickler-Tools → Zustände).

Entitäten lassen sich nicht löschen? Prüfe, ob sie in der Allowlist stehen, ob sie eine config_entry_id haben (Schutzmechanismus) und ob du als Admin angemeldet bist.

API gibt 404 zurück? Die Integration muss korrekt installiert und aktiviert sein. Prüfe die URL: http://[deine-IP]:8123/api/orphan_cleaner/results und starte Home Assistant neu.

Backup wird nicht erstellt? Prüfe die Schreibrechte im Home Assistant Konfigurationsverzeichnis – der Ordner muss beschreibbar sein.

### Entwicklung

Voraussetzungen:
- Home Assistant 2026.8.1 oder neuer
- Python 3.10 oder neuer

Tests ausführen:
pytest -q

Beiträge:
1. Forke das Repository.
2. Erstelle einen Feature-Branch.
3. Füge Tests für neue Funktionen hinzu.
4. Stelle sicher, dass alle Tests bestehen.
5. Erstelle einen Pull Request.

### Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die LICENSE Datei für Details.

### Danksagung

- Home Assistant Community für die großartige Arbeit.
- Alle Nutzer, die Feedback und Verbesserungsvorschläge einbringen.
