from __future__ import annotations

from custom_components.orphan_cleaner.const import DOMAIN
from custom_components.orphan_cleaner.orphan_detector import async_find_orphans
from tests.conftest import FakeEntityEntry, FakeRegistry, FakeHass


def test_async_find_orphans_filters_and_sorts(monkeypatch, tmp_path):
    entities = {
        "b": FakeEntityEntry(
            entity_id="sensor.b",
            original_name="B",
            platform="mqtt",
            config_entry_id=None,
            device_id=None,
            extra={},
        ),
        "a": FakeEntityEntry(
            entity_id="sensor.a",
            original_name="A",
            platform="template",
            config_entry_id=None,
            device_id=None,
            extra={"orphaned_timestamp": "2026-08-14T00:00:00Z"},
        ),
        "c": FakeEntityEntry(
            entity_id="sensor.c",
            original_name="C",
            platform="zha",
            config_entry_id="abc",
            device_id="dev1",
            extra={},
        ),
    }

    registry = FakeRegistry(entities)
    fake_hass = FakeHass(registry, tmp_path)

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.orphan_detector.er.async_get",
        lambda hass: registry,
    )

    results = async_find_orphans(fake_hass)

    assert [r["entity_id"] for r in results] == ["sensor.a", "sensor.b"]
    assert results[0]["reason"] == "orphaned_timestamp"
    assert results[1]["reason"] == "no_config_entry_no_device"
