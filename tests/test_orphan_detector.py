# tests/test_orphan_detector.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from custom_components.orphan_cleaner.orphan_detector import async_find_orphans
from tests.conftest import FakeDeletedEntityEntry, FakeEntityEntry, FakeRegistry, FakeHass


@pytest.mark.asyncio
async def test_async_find_orphans_filters_and_sorts(monkeypatch, tmp_path):
    entities = {
        "b": FakeEntityEntry(
            entity_id="sensor.b",
            original_name="B",
            platform="mqtt",
            config_entry_id=None,
            device_id=None,
        ),
        "a": FakeEntityEntry(
            entity_id="sensor.a",
            original_name="A",
            platform="template",
            config_entry_id=None,
            device_id="dev_a",  # hat device_id -> nicht "no_config_or_device"
        ),
        "c": FakeEntityEntry(
            entity_id="sensor.c",
            original_name="C",
            platform="zha",
            config_entry_id="abc",
            device_id="dev1",
        ),
    }

    registry = FakeRegistry(entities)
    fake_hass = FakeHass(registry, tmp_path)

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.orphan_detector.er.async_get",
        lambda hass: registry,
    )

    results = await async_find_orphans(fake_hass)

    assert [r["entity_id"] for r in results] == ["sensor.b"]
    assert results[0]["reason"] == "no_config_or_device"
    # sensor.a has a device_id, sensor.c has both -> neither is orphaned
    assert "sensor.a" not in [r["entity_id"] for r in results]
    assert "sensor.c" not in [r["entity_id"] for r in results]


@pytest.mark.asyncio
async def test_strict_mode_adds_platform_without_device_reason(monkeypatch, tmp_path):
    entities = {
        "a": FakeEntityEntry(
            entity_id="sensor.a",
            original_name="A",
            platform="mqtt",
            config_entry_id=None,
            device_id=None,
            orphaned_timestamp=None,
        ),
    }
    registry = FakeRegistry(entities)
    fake_hass = FakeHass(registry, tmp_path)

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.orphan_detector.er.async_get",
        lambda hass: registry,
    )

    results = await async_find_orphans(fake_hass, strict_mode=True)

    assert results[0]["orphaned_reason"] == ["no_config_or_device", "platform_without_device"]


@pytest.mark.asyncio
async def test_min_orphan_age_hours_does_not_flag_fully_linked_entities(monkeypatch, tmp_path):
    """min_orphan_age_hours betrifft nur pending_purge (deleted_entities) und
    disabled_long_term (aggressive_heuristic) - eine voll verknüpfte aktive
    Entität wird dadurch nicht plötzlich als Orphan gemeldet."""
    entities = {
        "linked": FakeEntityEntry(
            entity_id="sensor.linked",
            platform="mqtt",
            config_entry_id="abc",
            device_id="dev1",
        ),
    }
    registry = FakeRegistry(entities)
    fake_hass = FakeHass(registry, tmp_path)

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.orphan_detector.er.async_get",
        lambda hass: registry,
    )

    results = await async_find_orphans(fake_hass, min_orphan_age_hours=24)

    assert results == []


@pytest.mark.asyncio
async def test_aggressive_heuristic_flags_long_disabled_entities(monkeypatch, tmp_path):
    old_datetime = datetime.now(timezone.utc) - timedelta(hours=48)
    recent_datetime = datetime.now(timezone.utc) - timedelta(minutes=5)

    entities = {
        "long_disabled": FakeEntityEntry(
            entity_id="sensor.long_disabled",
            platform="mqtt",
            config_entry_id="abc",
            device_id="dev1",
            disabled_by="user",
            modified_at=old_datetime,
        ),
        "recently_disabled": FakeEntityEntry(
            entity_id="sensor.recently_disabled",
            platform="mqtt",
            config_entry_id="abc",
            device_id="dev1",
            disabled_by="user",
            modified_at=recent_datetime,
        ),
        "not_disabled": FakeEntityEntry(
            entity_id="sensor.not_disabled",
            platform="mqtt",
            config_entry_id="abc",
            device_id="dev1",
            disabled_by=None,
            modified_at=old_datetime,
        ),
    }
    registry = FakeRegistry(entities)
    fake_hass = FakeHass(registry, tmp_path)

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.orphan_detector.er.async_get",
        lambda hass: registry,
    )

    results = await async_find_orphans(
        fake_hass, min_orphan_age_hours=24, aggressive_heuristic=True
    )
    entity_ids = [r["entity_id"] for r in results]

    assert "sensor.long_disabled" in entity_ids
    assert "sensor.recently_disabled" not in entity_ids
    assert "sensor.not_disabled" not in entity_ids

    long_disabled_result = next(r for r in results if r["entity_id"] == "sensor.long_disabled")
    assert "disabled_long_term" in long_disabled_result["orphaned_reason"]


@pytest.mark.asyncio
async def test_aggressive_heuristic_off_by_default(monkeypatch, tmp_path):
    old_datetime = datetime.now(timezone.utc) - timedelta(hours=48)
    entities = {
        "long_disabled": FakeEntityEntry(
            entity_id="sensor.long_disabled",
            platform="mqtt",
            config_entry_id="abc",
            device_id="dev1",
            disabled_by="user",
            modified_at=old_datetime,
        ),
    }
    registry = FakeRegistry(entities)
    fake_hass = FakeHass(registry, tmp_path)

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.orphan_detector.er.async_get",
        lambda hass: registry,
    )

    results = await async_find_orphans(fake_hass)

    assert results == []


@pytest.mark.asyncio
async def test_no_crash_when_registry_entry_lacks_orphaned_timestamp_attribute(monkeypatch, tmp_path):
    """Regressionstest: RegistryEntry hat in echtem HA KEIN orphaned_timestamp
    -Attribut. Diese FakeEntityEntry hat zwar ein orphaned_timestamp-Feld
    (wird von anderen Tests gebraucht), aber async_find_orphans darf es für
    aktive Entitäten (registry.entities) niemals lesen - sonst würde es in
    echtem HA mit AttributeError crashen, so wie real gemeldet."""
    entities = {
        "a": FakeEntityEntry(
            entity_id="sensor.a",
            platform="mqtt",
            config_entry_id="abc",
            device_id="dev1",
            orphaned_timestamp=None,
        ),
    }
    registry = FakeRegistry(entities)
    fake_hass = FakeHass(registry, tmp_path)

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.orphan_detector.er.async_get",
        lambda hass: registry,
    )

    # Darf nicht crashen, egal was orphaned_timestamp enthält - da diese
    # Entität voll verknüpft ist (config_entry_id + device_id gesetzt),
    # sollte sie ohnehin nicht als Orphan erscheinen.
    results = await async_find_orphans(fake_hass)
    assert results == []


@pytest.mark.asyncio
async def test_deleted_entities_are_reported_as_pending_purge(monkeypatch, tmp_path):
    now = datetime.now(timezone.utc).timestamp()
    entities = {}
    deleted_entities = {
        "old_deleted": FakeDeletedEntityEntry(
            entity_id="sensor.old_deleted",
            name="Old Deleted",
            platform="pfsense",
            config_entry_id=None,
            orphaned_timestamp=now - 48 * 3600,
        ),
        "fresh_deleted": FakeDeletedEntityEntry(
            entity_id="sensor.fresh_deleted",
            name="Fresh Deleted",
            platform="pfsense",
            config_entry_id=None,
            orphaned_timestamp=now - 60,
        ),
        "no_timestamp": FakeDeletedEntityEntry(
            entity_id="sensor.no_timestamp",
            name="No Timestamp",
            platform="pfsense",
            config_entry_id="abc",
            orphaned_timestamp=None,
        ),
    }
    registry = FakeRegistry(entities, deleted_entities)
    fake_hass = FakeHass(registry, tmp_path)

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.orphan_detector.er.async_get",
        lambda hass: registry,
    )

    results = await async_find_orphans(fake_hass, min_orphan_age_hours=24)
    entity_ids = [r["entity_id"] for r in results]

    assert "sensor.old_deleted" in entity_ids
    assert "sensor.fresh_deleted" not in entity_ids  # zu jung für min_orphan_age_hours
    assert "sensor.no_timestamp" not in entity_ids  # kein orphaned_timestamp -> nicht "pending purge"

    old_result = next(r for r in results if r["entity_id"] == "sensor.old_deleted")
    assert old_result["pending_purge"] is True
    assert old_result["reason"] == "pending_purge_by_ha"
