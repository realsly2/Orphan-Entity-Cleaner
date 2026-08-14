# Orphan Cleaner

[![HACS Default](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz/)
[![GitHub release](https://img.shields.io/github/v/release/realsly2/Orphan-Entity-Cleaner)](https://github.com/realsly2/Orphan-Entity-Cleaner/releases)
[![License](https://img.shields.io/github/license/realsly2/Orphan-Entity-Cleaner)](LICENSE)
(https://my.home-assistant.io/redirect/hacs_repository/?owner=realsly2&repository=Orphan-Entity-Cleaner&category=integration)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)]

Orphan Cleaner is a Home Assistant custom integration for finding, reviewing, backing up, exporting, and deleting orphaned entities.

It provides a built-in Home Assistant sidebar panel, bulk actions, search, and safety checks to help you clean up your system with confidence.

## Features

- Detect orphaned entities
- Built-in Home Assistant sidebar panel
- Search by entity ID, name, or platform
- Bulk selection with checkboxes
- Dry-run support
- Export scan results as JSON
- Automatic backup before destructive actions
- Protection for entities with a `config_entry_id`
- Clear stored results
- Admin-only access

## Installation

### Via HACS

1. Open HACS in Home Assistant.
2. Add this repository as an Integration.
3. Install the integration.
4. Restart Home Assistant.

### Manual installation

1. Copy `custom_components/orphan_cleaner/` into your Home Assistant `custom_components/` folder.
2. Restart Home Assistant.
3. Add the integration in Home Assistant.

## Usage

1. Open **Orphan Cleaner** from the Home Assistant sidebar.
2. Run a scan.
3. Review the detected entities.
4. Filter and select the entities you want to handle.
5. Export or back up the results if needed.
6. Delete only the entities you want to remove.

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

Before any destructive deletion, Orphan Cleaner creates a backup automatically.

Entities that still have a `config_entry_id` are protected from deletion.

## Development

Requirements:

- Home Assistant 2026.8.1 or newer

Tests:

```bash
pytest -q

