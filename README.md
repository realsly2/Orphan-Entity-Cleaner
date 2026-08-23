# Orphan Cleaner

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![License](https://img.shields.io/github/license/realsly2/Orphan-Entity-Cleaner)](LICENSE)
[![Version](https://img.shields.io/github/v/release/realsly2/Orphan-Entity-Cleaner)](https://github.com/realsly2/Orphan-Entity-Cleaner/releases)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realsly2&repository=Orphan-Entity-Cleaner&category=integration)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orphan_cleaner)

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

#### Option 1: Via HACS (recommended)

Click the button below to open this repository directly inside HACS on your own Home Assistant instance (skips steps 1–4):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realsly2&repository=Orphan-Entity-Cleaner&category=integration)

Or manually:
1. Open HACS in Home Assistant.
2. Click on "Integrations" → three dots (⋮) → "Custom repositories".
3. Add this URL: https://github.com/realsly2/Orphan-Entity-Cleaner
4. Select "Integration" as the category.
5. Click "Install" and restart Home Assistant.
6. Then set up the integration itself — click the button below, or go to **Settings → Devices & Services → Add Integration** and search for "Orphan Cleaner". No YAML editing required.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orphan_cleaner)

#### Option 2: Manual Installation
1. Download the custom_components/orphan_cleaner/ folder from this repository.
2. Copy it into your Home Assistant custom_components/ directory.
3. Restart Home Assistant.
4. Then set up the integration — click the button below, or go to **Settings → Devices & Services → Add Integration** and search for "Orphan Cleaner".

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orphan_cleaner)

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

An entity is flagged if it has no config_entry_id AND no device_id (`no_config_or_device`). With `strict_mode: true`, entities with a platform reference but no device_id get an extra warning tag (`platform_without_device`) alongside another reason. With `aggressive_heuristic: true`, entities that were manually disabled and haven't been modified for at least `min_orphan_age_hours` are also flagged (`disabled_long_term`). Entities Home Assistant has already internally deleted and will auto-purge within ~30 days show up too (`pending_purge_by_ha`) - purely informational, not actionable here.

### How do I know what's safe to delete?

**Nothing here is a guarantee - every signal is a heuristic, not a certainty.** Each result comes with a risk badge and a plain-language hint explaining exactly why it was flagged and what to double-check before deleting:

- **`no_config_or_device`** (⚠️ Review): The strongest signal, but can also be a perfectly intentional YAML-defined entity (old-style template sensor, group, zone, input helper) that never has a config_entry_id/device_id by design. Check if the entity_id/name/domain looks familiar before deleting.
- **`platform_without_device`** (⚠️ Review): A weaker add-on signal, only shown alongside another reason.
- **`disabled_long_term`** (🟠 Review): A person already disabled it manually - but "disabled" isn't the same as "safe to permanently delete"; they might want it back later.
- **`pending_purge_by_ha`** (✅ No action needed): Home Assistant already deleted this internally and will remove it permanently on its own. Not deletable here - just informational.

Use the search box and the reason filter dropdown in the panel to narrow down what you're looking at, and read the hint text under each entry before selecting it.

### Where are backups stored, and how do I restore?

Every deletion automatically writes a backup **before** deleting, into a dedicated subfolder: `<config>/orphan_cleaner_backups/orphan_cleaner_backup_<timestamp>.json` (e.g. `/config/orphan_cleaner_backups/...`) - not directly in your config root.

**What "restore" actually means in Home Assistant:** Home Assistant doesn't hard-delete entities immediately. `delete_selected` calls the registry's soft-delete, which moves the entry into an internal "pending purge" bucket for about 30 days before Home Assistant removes it permanently on its own. During that window:

- Click **"Backups anzeigen"** in the panel (or call the `orphan_cleaner.list_backups` service) to see available backup files.
- Click **"Restore"** next to a backup entry (or call `orphan_cleaner.restore_from_backup` with the filename) to recreate a registry entry for entities that don't currently exist. This uses the same mechanism Home Assistant itself uses when an integration re-registers an entity, so it gets the **same entity_id** back.
- **Limits, stated honestly:** only `entity_id`, `name`, and the platform/unique_id link get restored. State history, statistics, area assignment, and icon are *not* restored - Home Assistant's own registry doesn't support restoring those outside of the original integration reconnecting. If you need those back, you'll need to reapply them manually (the backup JSON still has the info to remind you what they were).
- Already-existing entities are always skipped during restore, never overwritten.

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

- orphan_cleaner.scan: Starts a new scan (optional: strict_mode, min_orphan_age_hours, aggressive_heuristic)
- orphan_cleaner.delete_selected: Deletes the selected entities (requires entity_ids parameter)
- orphan_cleaner.clear_results: Clears the saved scan results
- orphan_cleaner.export_results: Exports the results as a JSON file
- orphan_cleaner.backup_results: Creates a backup of the results
- orphan_cleaner.get_allowlist: Returns the current allowlist (for debugging)
- orphan_cleaner.list_backups: Lists available backup files with their entry counts
- orphan_cleaner.restore_from_backup: Restores entities from a backup file (see limits above)

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

Restore from a backup:
service: orphan_cleaner.restore_from_backup
data:
  filename: orphan_cleaner_backup_20260821T060000Z.json

### API Endpoints

- GET /api/orphan_cleaner/results: Retrieve all scan results (with pagination), plus backups/last_backup_path/last_restore
- DELETE /api/orphan_cleaner/results: Delete all results
- GET /orphan-cleaner: The sidebar panel

Pagination:

First 10 results: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10"
10 results from offset 20: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10&offset=20"

The response includes metadata:
{
  "total": 150,
  "offset": 20,
  "limit": 10,
  "results": [ ... ],
  "backups": [ ... ],
  "last_backup_path": "/config/orphan_cleaner_backups/orphan_cleaner_backup_....json",
  "last_restore": null
}

### Troubleshooting

Scan finds no entities? Make sure you have actually removed old integrations or devices, and check if the entities really have no config_entry_id and device_id (e.g., via Developer Tools → States).

Entities cannot be deleted? Check if they are on the allowlist, if they have a config_entry_id (protection mechanism), and if you are logged in as admin.

API returns 404? The integration must be correctly installed and active. Check the URL: http://[your-IP]:8123/api/orphan_cleaner/results and restart Home Assistant.

Backup is not created? Check write permissions in the Home Assistant configuration directory - the orphan_cleaner_backups subfolder must be creatable/writable.

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

#### Option 1: Via HACS (empfohlen)

Klicke auf den Button, um dieses Repository direkt in HACS auf deiner eigenen Home-Assistant-Instanz zu öffnen (spart Schritte 1–4):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realsly2&repository=Orphan-Entity-Cleaner&category=integration)

Oder manuell:
1. Öffne HACS in Home Assistant.
2. Klicke auf "Integrationen" und dann auf die drei Punkte (⋮) oben rechts.
3. Wähle "Benutzerdefinierte Repositories" und füge diese URL hinzu: https://github.com/realsly2/Orphan-Entity-Cleaner
4. Wähle "Integration" als Kategorie.
5. Klicke auf "Installieren".
6. Starte Home Assistant neu.
7. Richte anschließend die Integration selbst ein — klicke auf den Button unten, oder gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen** und suche nach "Orphan Cleaner". Keine YAML-Bearbeitung nötig.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orphan_cleaner)

#### Option 2: Manuelle Installation
1. Lade den Ordner custom_components/orphan_cleaner/ aus diesem Repository herunter.
2. Kopiere ihn in dein Home Assistant custom_components/-Verzeichnis.
3. Starte Home Assistant neu.
4. Richte anschließend die Integration ein — klicke auf den Button unten, oder gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen** und suche nach "Orphan Cleaner".

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=orphan_cleaner)

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

Eine Entität wird markiert, wenn sie weder config_entry_id noch device_id hat (`no_config_or_device`). Mit `strict_mode: true` bekommen Entitäten mit Plattform-Referenz aber ohne device_id zusätzlich eine Warnung (`platform_without_device`), immer nur zusammen mit einem anderen Grund. Mit `aggressive_heuristic: true` werden zusätzlich manuell deaktivierte Entitäten gemeldet, die seit mindestens `min_orphan_age_hours` nicht verändert wurden (`disabled_long_term`). Entitäten, die Home Assistant bereits intern gelöscht hat und die innerhalb von ca. 30 Tagen automatisch endgültig entfernt werden, erscheinen ebenfalls (`pending_purge_by_ha`) - rein informativ, hier nicht aktionierbar.

### Woher weiß ich, was ich gefahrlos löschen kann?

**Nichts hier ist eine Garantie – jedes Signal ist eine Heuristik, keine Gewissheit.** Jedes Ergebnis hat ein Risiko-Badge und einen Klartext-Hinweis, warum es erkannt wurde und was du vorher prüfen solltest:

- **`no_config_or_device`** (⚠️ Prüfen): Das stärkste Signal, kann aber auch eine bewusst per YAML angelegte Entität sein (alter Template-Sensor, Gruppe, Zone, Helper), die konstruktionsbedingt nie eine config_entry_id/device_id hat. Prüfe, ob dir entity_id/Name/Domain bekannt vorkommen, bevor du löschst.
- **`platform_without_device`** (⚠️ Prüfen): Ein schwächeres Zusatzsignal, tritt nur zusammen mit einem anderen Grund auf.
- **`disabled_long_term`** (🟠 Prüfen): Ein Mensch hat sie bereits manuell deaktiviert – aber "deaktiviert" heißt nicht automatisch "kann dauerhaft weg"; vielleicht wird sie später wieder gebraucht.
- **`pending_purge_by_ha`** (✅ Keine Aktion nötig): Home Assistant hat diese Entität bereits intern gelöscht und entfernt sie von selbst endgültig. Hier nicht löschbar – nur zur Information.

Nutze die Suche und den Grund-Filter im Panel, um die Liste einzugrenzen, und lies den Hinweistext unter jedem Eintrag, bevor du ihn auswählst.

### Wohin wird das Backup gespeichert, und wie stelle ich wieder her?

Jede Löschung schreibt automatisch **vor** dem Löschen ein Backup, in einen eigenen Unterordner: `<config>/orphan_cleaner_backups/orphan_cleaner_backup_<Zeitstempel>.json` (z.B. `/config/orphan_cleaner_backups/...`) – nicht direkt in deinem config-Root.

**Was "Wiederherstellen" in Home Assistant technisch bedeutet:** Home Assistant löscht Entitäten nicht sofort hart. `delete_selected` nutzt das Soft-Delete der Registry, das den Eintrag zunächst für ca. 30 Tage in einen internen "wartet auf endgültige Entfernung"-Zustand verschiebt, bevor Home Assistant ihn von selbst endgültig entfernt. In diesem Zeitfenster:

- Klicke im Panel auf **"Backups anzeigen"** (oder rufe den Service `orphan_cleaner.list_backups` auf), um verfügbare Backup-Dateien zu sehen.
- Klicke bei einem Backup-Eintrag auf **"Restore"** (oder rufe `orphan_cleaner.restore_from_backup` mit dem Dateinamen auf), um für aktuell nicht existierende Entitäten wieder einen Registry-Eintrag anzulegen. Das nutzt denselben Mechanismus, den Home Assistant selbst verwendet, wenn eine Integration eine Entität neu registriert – du bekommst also dieselbe entity_id zurück.
- **Grenzen, ehrlich benannt:** Nur entity_id, Name und die Plattform-/unique_id-Verknüpfung werden wiederhergestellt. Zustandsverlauf, Statistiken, Bereichszuordnung und Icon werden **nicht** wiederhergestellt – das unterstützt die Home-Assistant-Registry außerhalb einer echten Neu-Registrierung durch die ursprüngliche Integration schlicht nicht. Falls du das brauchst, musst du es manuell nachtragen (die Backup-JSON-Datei zeigt dir immerhin, was es vorher war).
- Bereits existierende Entitäten werden beim Restore immer übersprungen, nie überschrieben.

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

- orphan_cleaner.scan: Startet einen neuen Scan (optional: strict_mode, min_orphan_age_hours, aggressive_heuristic)
- orphan_cleaner.delete_selected: Löscht die ausgewählten Entitäten (erfordert entity_ids-Parameter)
- orphan_cleaner.clear_results: Löscht die gespeicherten Scan-Ergebnisse
- orphan_cleaner.export_results: Exportiert die Ergebnisse als JSON-Datei
- orphan_cleaner.backup_results: Erstellt ein Backup der Ergebnisse
- orphan_cleaner.get_allowlist: Gibt die aktuelle Allowlist zurück (für Debugging)
- orphan_cleaner.list_backups: Listet verfügbare Backup-Dateien mit Anzahl der Einträge
- orphan_cleaner.restore_from_backup: Stellt Entitäten aus einer Backup-Datei wieder her (siehe Grenzen oben)

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

Aus einem Backup wiederherstellen:
service: orphan_cleaner.restore_from_backup
data:
  filename: orphan_cleaner_backup_20260821T060000Z.json

### API-Endpunkte

- GET /api/orphan_cleaner/results: Alle Scan-Ergebnisse abrufen (mit Paginierung), zusätzlich backups/last_backup_path/last_restore
- DELETE /api/orphan_cleaner/results: Alle Ergebnisse löschen
- GET /orphan-cleaner: Das Sidebar-Panel

Paginierung:

Erste 10 Ergebnisse: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10"
10 Ergebnisse ab Offset 20: curl -X GET "http://homeassistant.local:8123/api/orphan_cleaner/results?limit=10&offset=20"

Die Antwort enthält Metadaten:
{
  "total": 150,
  "offset": 20,
  "limit": 10,
  "results": [ ... ],
  "backups": [ ... ],
  "last_backup_path": "/config/orphan_cleaner_backups/orphan_cleaner_backup_....json",
  "last_restore": null
}

### Fehlerbehebung

Scan findet keine Entitäten? Stelle sicher, dass du tatsächlich alte Integrationen oder Geräte entfernt hast, und prüfe, ob die Entitäten wirklich keine config_entry_id und device_id mehr haben (z.B. über den Entwickler-Tools → Zustände).

Entitäten lassen sich nicht löschen? Prüfe, ob sie in der Allowlist stehen, ob sie eine config_entry_id haben (Schutzmechanismus) und ob du als Admin angemeldet bist.

API gibt 404 zurück? Die Integration muss korrekt installiert und aktiviert sein. Prüfe die URL: http://[deine-IP]:8123/api/orphan_cleaner/results und starte Home Assistant neu.

Backup wird nicht erstellt? Prüfe die Schreibrechte im Home Assistant Konfigurationsverzeichnis – der Unterordner orphan_cleaner_backups muss anlegbar/beschreibbar sein.

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
