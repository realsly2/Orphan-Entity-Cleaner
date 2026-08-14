# Orphan Cleaner

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![License](https://img.shields.io/github/license/realsly2/Orphan-Entity-Cleaner)](LICENSE)
[![Version](https://img.shields.io/github/v/release/realsly2/Orphan-Entity-Cleaner)](https://github.com/realsly2/Orphan-Entity-Cleaner/releases)

## Was sind verwaiste Entitäten?

In Home Assistant können Entitäten "verwaisten", wenn:
- Eine Integration oder ein Gerät entfernt wird, aber die dazugehörigen Entitäten in der Registry bleiben.
- Ein Gerät nicht mehr erreichbar ist oder abgemeldet wurde.
- Ein Integrations-Update die Entitäts-Struktur ändert.

Diese Entitäten sind nicht mehr funktional, können aber:
- Deine Entitätsliste unübersichtlich machen
- Die Performance beeinträchtigen
- Fehler in Logs und Automatisierungen verursachen

## ⚠️ Wichtiger Sicherheitshinweis

**Bevor du Entitäten löschst:**
1. **Erstelle ein vollständiges Backup** deiner Home Assistant-Konfiguration (nicht nur das automatische Backup dieser Integration).
2. **Überprüfe** alle Automatisierungen, Skripte und Dashboards, die diese Entitäten verwenden könnten.
3. **Nutze den Dry-Run-Modus** zuerst, um die Auswirkungen zu prüfen.

**Gelöschte Entitäten können nicht wiederhergestellt werden** (außer über ein Backup)!

## Features

- 🕵️ **Erkennung** verwaister Entitäten (mit erweiterten Kriterien)
- 🖥️ **Integriertes Sidebar-Panel** für einfache Bedienung
- 🔍 **Suche** nach Entitäts-ID, Name oder Plattform
- ✅ **Bulk-Auswahl** mit Checkboxen
- 🧪 **Dry-Run-Unterstützung** (teste, was passieren würde)
- 💾 **Export** der Scan-Ergebnisse als JSON
- 🛡️ **Automatisches Backup** vor jeder Lösch-Aktion
- 🔒 **Schutz für Entitäten mit config_entry_id**
- 📋 **Allowlist** für kritische Entitäten (nie löschen)
- 🔍 **Erweiterte Erkennungslogik** mit `strict_mode` für zusätzliche Prüfungen
- 📄 **Paginierung** für den API-Endpunkt bei großen Ergebnismengen
- 🔐 **Admin-only Zugriff**

## Installation

### Via HACS (empfohlen)

1. Öffne HACS in Home Assistant.
2. Klicke auf "Integrations" und dann auf die drei Punkte (⋮) oben rechts.
3. Wähle "Custom repositories" und füge diese URL hinzu:
