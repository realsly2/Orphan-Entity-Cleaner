# Orphan Cleaner

[![HACS Default](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz/)
[![GitHub release](https://img.shields.io/github/v/release/realsly2/Orphan-Entity-Cleaner)](https://github.com/realsly2/Orphan-Entity-Cleaner/releases)
[![License](https://img.shields.io/github/license/realsly2/Orphan-Entity-Cleaner)](LICENSE)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realsly2&repository=Orphan-Entity-Cleaner&category=integration)

Orphan Cleaner is a Home Assistant custom integration for identifying, reviewing, backing up, exporting, and removing orphaned entities from your system.

It provides a built-in Home Assistant panel, bulk actions, safety checks, and automatic backups before deletion.

## Features

- Detect orphaned entities automatically
- Show results in a built-in Home Assistant sidebar panel
- Search by entity ID, name, or platform
- Select multiple entities for bulk actions
- Dry-run support
- Export scan results as JSON
- Create backups before destructive actions
- Protect entities with a `config_entry_id`
- Clear stored results
- Admin-only access

## Installation

### Recommended: HACS

1. Open **HACS** in Home Assistant.
2. Click the HACS install button above.
3. Add this repository as an **Integration**.
4. Install the integration.
5. Restart Home Assistant.

### Manual installation

1. Copy the `custom_components/orphan_cleaner/` folder into your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration in Home Assistant.

## Usage

1. Open **Orphan Cleaner** from the Home Assistant sidebar.
2. Run a scan.
3. Review the detected orphaned entities.
4. Use search and selection to narrow the list.
5. Export or back up results if needed.
6. Delete only the entities you want removed.

## Detection logic

An entity is marked as orphaned if:

- `orphaned_timestamp` exists, or
- both `config_entry_id` and `device_id` are `None`

Results are sorted by `entity_id`.

## Services

- `orphan_cleaner.scan`
- `orphan_cleaner.delete_selected`
- `orphan_cleaner.clear_results`
- `orphan_cleaner.export_results`
- `orphan_cleaner.backup_results`

## API endpoints

- `GET /api/orphan_cleaner/results`
- `GET /orphan-cleaner`

## Safety

Before any destructive deletion, Orphan Cleaner automatically creates a backup.

Entities that still have a `config_entry_id` are protected from deletion.

## Project structure

```text
custom\_components/orphan\_cleaner/
brand/
tests/


