# Orphan Cleaner

Home Assistant custom integration for finding and removing orphaned entities.

## Features
- Scan entity registry for orphaned entities
- List results in a built-in admin panel
- Search by entity_id, name, platform
- Select visible rows
- Export results
- Backup before deletion
- Protect entities with `config_entry_id`

## Install
Copy `custom_components/orphan_cleaner/` into your Home Assistant `custom_components/` folder.

## Services
- `orphan_cleaner.scan`
- `orphan_cleaner.clear_results`
- `orphan_cleaner.export_results`
- `orphan_cleaner.backup_results`
- `orphan_cleaner.delete_selected`

## Notes
This integration is designed for manual HACS-style installation.
