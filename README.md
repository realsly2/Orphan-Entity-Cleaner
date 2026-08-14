# Orphan Cleaner

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=realsly2&repository=Orphan-Entity-Cleaner&category=integration)

Orphan Cleaner is a Home Assistant custom integration for finding, listing, backing up, exporting, and removing orphaned entities.

## Features

- Scan for orphaned entities
- Filter results by entity ID, name, or platform
- Bulk select entities
- Dry-run mode
- Export results as JSON
- Backup results before deletion
- Delete selected orphaned entities
- Clear stored scan results
- Built-in Home Assistant sidebar panel
- Admin-only access

## Installation

### Via HACS

1. Open **HACS** in Home Assistant.
2. Click the button above.
3. Add the repository as an **Integration**.
4. Install the integration.
5. Restart Home Assistant.

### Manual installation

1. Copy `custom_components/orphan_cleaner/` into your Home Assistant `custom_components/` folder.
2. Restart Home Assistant.
3. Add the integration through HACS or reload Home Assistant.

## Usage

1. Open **Orphan Cleaner** in the Home Assistant sidebar.
2. Run a scan.
3. Review the detected entities.
4. Export or back up the results.
5. Delete selected entities if needed.

## Detection logic

An entity is considered orphaned if:

- `orphaned_timestamp` exists, or
- both `config_entry_id` and `device_id` are `None`

Results are sorted by `entity_id`.

## Services

- `orphan_cleaner.scan`
- `orphan_cleaner.delete_selected`
- `orphan_cleaner.clear_results`
- `orphan_cleaner.export_results`
- `orphan_cleaner.backup_results`

## API

- `GET /api/orphan_cleaner/results`
- `GET /orphan-cleaner`

## Safety

Before any destructive deletion, Orphan Cleaner creates a backup automatically.

Entities with a `config_entry_id` are protected from deletion.

## Project structure

- `custom_components/orphan_cleaner/`
- `brand/`
- `tests/`

## Requirements

- Home Assistant 2026.8.1 or newer

## License

MIT License  
Copyright (c) 2026 Realsly

