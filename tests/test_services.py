# tests/test_services.py
from __future__ import annotations

import json

import pytest

from custom_components.orphan_cleaner.const import (
    BACKUP_KEY,
    DOMAIN,
    EXPORT_KEY,
    LAST_DELETED_KEY,
    RESULTS_KEY,
)
from custom_components.orphan_cleaner.services import (
    async_backup_results_service,
    async_clear_results_service,
    async_delete_selected_service,
    async_export_results_service,
    async_list_backups_service,
    async_restore_from_backup_service,
    async_scan_service,
)
from tests.conftest import FakeCall, FakeEntityEntry, FakeRegistry, FakeHass


@pytest.mark.asyncio
async def test_scan_service_stores_results(monkeypatch, tmp_path):
    registry = FakeRegistry({})
    hass = FakeHass(registry, tmp_path)

    async def fake_find_orphans(hass, strict_mode=False, min_orphan_age_hours=0, aggressive_heuristic=False):
        return [{"entity_id": "sensor.test"}]

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.services.async_find_orphans",
        fake_find_orphans,
    )

    await async_scan_service(FakeCall(hass))

    assert hass.data[DOMAIN][RESULTS_KEY] == [{"entity_id": "sensor.test"}]


@pytest.mark.asyncio
async def test_clear_results_service_clears_data(tmp_path):
    hass = FakeHass(FakeRegistry({}), tmp_path)
    hass.data = {DOMAIN: {RESULTS_KEY: [{"entity_id": "sensor.test"}]}}

    await async_clear_results_service(FakeCall(hass))

    assert hass.data[DOMAIN][RESULTS_KEY] == []


@pytest.mark.asyncio
async def test_export_results_service_creates_json(tmp_path):
    hass = FakeHass(FakeRegistry({}), tmp_path)
    hass.data = {DOMAIN: {RESULTS_KEY: [{"entity_id": "sensor.test"}]}}

    await async_export_results_service(FakeCall(hass))

    exported = hass.data[DOMAIN][EXPORT_KEY]
    assert json.loads(exported) == [{"entity_id": "sensor.test"}]


@pytest.mark.asyncio
async def test_backup_results_service_writes_file(tmp_path):
    hass = FakeHass(FakeRegistry({}), tmp_path)
    hass.data = {DOMAIN: {RESULTS_KEY: [{"entity_id": "sensor.test"}]}}

    await async_backup_results_service(FakeCall(hass))

    assert BACKUP_KEY in hass.data[DOMAIN]
    files = list((tmp_path / "orphan_cleaner_backups").glob("orphan_cleaner_backup_*.json"))
    assert len(files) == 1

    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["results"] == [{"entity_id": "sensor.test"}]
    assert "timestamp" in payload


@pytest.mark.asyncio
async def test_delete_selected_skips_protected_and_deletes_unprotected(monkeypatch, tmp_path):
    entities = {
        "sensor.keep": FakeEntityEntry(
            entity_id="sensor.keep",
            config_entry_id="abc",
        ),
        "sensor.delete": FakeEntityEntry(
            entity_id="sensor.delete",
            config_entry_id=None,
        ),
        "zone.home": FakeEntityEntry(
            entity_id="zone.home",
            config_entry_id=None,
        ),
    }
    registry = FakeRegistry(entities)
    hass = FakeHass(registry, tmp_path)
    hass.data = {DOMAIN: {RESULTS_KEY: []}}

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.services.er.async_get",
        lambda hass: registry,
    )

    await async_delete_selected_service(
        FakeCall(
            hass,
            {"entity_ids": ["sensor.keep", "sensor.delete", "zone.home", "sensor.missing"]},
        )
    )

    assert registry.removed == ["sensor.delete"]
    summary = hass.data[DOMAIN][LAST_DELETED_KEY]
    assert summary["deleted"] == ["sensor.delete"]
    assert sorted(summary["protected"]) == ["sensor.keep", "zone.home"]
    assert summary["not_found"] == ["sensor.missing"]
    assert summary["errors"] == []
    backup_files = list((tmp_path / "orphan_cleaner_backups").glob("orphan_cleaner_backup_*.json"))
    assert backup_files

    backup_payload = json.loads(backup_files[0].read_text(encoding="utf-8"))
    assert backup_payload["results"][0]["entity_id"] == "sensor.delete"
    assert backup_payload["results"][0]["unique_id"] == "fake-unique-id"
    assert backup_payload["results"][0]["domain"] == "sensor"


@pytest.mark.asyncio
async def test_list_backups_reads_files_from_config_dir(tmp_path):
    hass = FakeHass(FakeRegistry({}), tmp_path)
    hass.data = {DOMAIN: {}}

    payload = {
        "timestamp": "2026-08-20T00:00:00+00:00",
        "type": "deletion",
        "results": [{"entity_id": "sensor.a"}, {"entity_id": "sensor.b"}],
    }
    backup_dir = tmp_path / "orphan_cleaner_backups"
    backup_dir.mkdir()
    (backup_dir / "orphan_cleaner_backup_20260820T000000Z.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    await async_list_backups_service(FakeCall(hass))

    backups = hass.data[DOMAIN]["backups"]
    assert len(backups) == 1
    assert backups[0]["filename"] == "orphan_cleaner_backup_20260820T000000Z.json"
    assert backups[0]["count"] == 2


@pytest.mark.asyncio
async def test_restore_from_backup_recreates_entry(monkeypatch, tmp_path):
    registry = FakeRegistry({})
    hass = FakeHass(registry, tmp_path)
    hass.data = {DOMAIN: {}}

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.services.er.async_get",
        lambda hass: registry,
    )

    created = []

    def fake_get_or_create(domain, platform, unique_id, suggested_object_id=None, original_name=None):
        entity_id = f"{domain}.{suggested_object_id}"
        created.append((entity_id, unique_id, platform))
        return type("Obj", (), {"entity_id": entity_id})()

    registry.async_get_or_create = fake_get_or_create

    payload = {
        "timestamp": "2026-08-20T00:00:00+00:00",
        "type": "deletion",
        "results": [
            {
                "entity_id": "sensor.ghost",
                "unique_id": "abc123",
                "domain": "sensor",
                "platform": "mqtt",
                "name": "Ghost",
            }
        ],
    }
    backup_dir = tmp_path / "orphan_cleaner_backups"
    backup_dir.mkdir()
    (backup_dir / "orphan_cleaner_backup_test.json").write_text(json.dumps(payload), encoding="utf-8")

    await async_restore_from_backup_service(
        FakeCall(hass, {"filename": "orphan_cleaner_backup_test.json"})
    )

    result = hass.data[DOMAIN]["last_restore"]
    assert result["restored"] == ["sensor.ghost"]
    assert result["skipped_existing"] == []
    assert result["errors"] == []
    assert created == [("sensor.ghost", "abc123", "mqtt")]


@pytest.mark.asyncio
async def test_restore_from_backup_skips_already_existing_entities(monkeypatch, tmp_path):
    entities = {
        "sensor.ghost": FakeEntityEntry(entity_id="sensor.ghost", unique_id="abc123"),
    }
    registry = FakeRegistry(entities)
    hass = FakeHass(registry, tmp_path)
    hass.data = {DOMAIN: {}}

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.services.er.async_get",
        lambda hass: registry,
    )

    payload = {
        "results": [
            {"entity_id": "sensor.ghost", "unique_id": "abc123", "domain": "sensor", "platform": "mqtt"}
        ]
    }
    backup_dir = tmp_path / "orphan_cleaner_backups"
    backup_dir.mkdir()
    (backup_dir / "orphan_cleaner_backup_test.json").write_text(json.dumps(payload), encoding="utf-8")

    await async_restore_from_backup_service(
        FakeCall(hass, {"filename": "orphan_cleaner_backup_test.json"})
    )

    result = hass.data[DOMAIN]["last_restore"]
    assert result["restored"] == []
    assert result["skipped_existing"] == ["sensor.ghost"]


@pytest.mark.asyncio
async def test_restore_from_backup_rejects_path_traversal(tmp_path):
    hass = FakeHass(FakeRegistry({}), tmp_path)
    hass.data = {DOMAIN: {}}

    await async_restore_from_backup_service(
        FakeCall(hass, {"filename": "../../etc/passwd"})
    )

    assert "last_restore" not in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_restore_from_backup_missing_file(tmp_path):
    hass = FakeHass(FakeRegistry({}), tmp_path)
    hass.data = {DOMAIN: {}}

    await async_restore_from_backup_service(
        FakeCall(hass, {"filename": "does_not_exist.json"})
    )

    assert "last_restore" not in hass.data[DOMAIN]
