# tests/test_orphan_detector.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from custom_components.orphan_cleaner.orphan_detector import async_find_orphans
from tests.conftest import FakeEntityEntry, FakeRegistry, FakeHass


@pytest.mark.asyncio
async def test_async_find_orphans_filters_and_sorts(monkeypatch, tmp_path):
    entities = {
        "b": FakeEntityEntry(
            entity_id="sensor.b",
            original_name="B",
            platform="mqtt",
            config_entry_id=None,
            device_id=None,
            orphaned_timestamp=None,
        ),
        "a": FakeEntityEntry(
            entity_id="sensor.a",
            original_name="A",
            platform="template",
            config_entry_id=None,
            device_id="dev_a",
            orphaned_timestamp=1755129600.0,
        ),
        "c": FakeEntityEntry(
            entity_id="sensor.c",
            original_name="C",
            platform="zha",
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

    results = await async_find_orphans(fake_hass)

    assert [r["entity_id"] for r in results] == ["sensor.a", "sensor.b"]
    assert results[0]["reason"] == "orphaned_timestamp_exists"
    assert results[1]["reason"] == "no_config_or_device"
    # sensor.c has both config_entry_id and device_id -> not orphaned
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
async def test_min_orphan_age_hours_filters_recent_orphans(monkeypatch, tmp_path):
    now = datetime.now(timezone.utc).timestamp()
    entities = {
        "fresh": FakeEntityEntry(
            entity_id="sensor.fresh",
            platform="mqtt",
            config_entry_id="abc",
            device_id="dev1",
            orphaned_timestamp=now - 60,  # vor 1 Minute verwaist
        ),
        "old": FakeEntityEntry(
            entity_id="sensor.old",
            platform="mqtt",
            config_entry_id="abc",
            device_id="dev1",
            orphaned_timestamp=now - 48 * 3600,  # vor 48h verwaist
        ),
    }
    registry = FakeRegistry(entities)
    fake_hass = FakeHass(registry, tmp_path)

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.orphan_detector.er.async_get",
        lambda hass: registry,
    )

    results = await async_find_orphans(fake_hass, min_orphan_age_hours=24)

    entity_ids = [r["entity_id"] for r in results]
    assert "sensor.old" in entity_ids
    assert "sensor.fresh" not in entity_ids


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
