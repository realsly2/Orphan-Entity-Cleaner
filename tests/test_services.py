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
    files = list(tmp_path.glob("orphan_cleaner_backup_*.json"))
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
    hass.data = {
        DOMAIN: {
            RESULTS_KEY: [
                {"entity_id": "sensor.delete", "pending_purge": False},
                {"entity_id": "sensor.keep", "pending_purge": False},
            ]
        }
    }

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
    assert summary["protected"] == ["sensor.keep"]
    assert summary["not_found"] == ["zone.home", "sensor.missing"]
    assert summary["errors"] == []
    assert list(tmp_path.glob("orphan_cleaner_backup_*.json"))


@pytest.mark.asyncio
async def test_delete_selected_dry_run_does_not_remove_or_backup(monkeypatch, tmp_path):
    registry = FakeRegistry({
        "sensor.delete": FakeEntityEntry(entity_id="sensor.delete"),
    })
    hass = FakeHass(registry, tmp_path)
    hass.data = {DOMAIN: {RESULTS_KEY: [{"entity_id": "sensor.delete"}]}}

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.services.er.async_get",
        lambda hass: registry,
    )

    await async_delete_selected_service(
        FakeCall(hass, {"entity_ids": ["sensor.delete"], "dry_run": True})
    )

    assert registry.removed == []
    assert hass.data[DOMAIN][LAST_DELETED_KEY]["would_delete"] == ["sensor.delete"]
    assert not list(tmp_path.glob("orphan_cleaner_backup_*.json"))
