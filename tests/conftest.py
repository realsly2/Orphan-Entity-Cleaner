# tests/conftest.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


@dataclass
class FakeEntityEntry:
    entity_id: str
    unique_id: str = "fake-unique-id"
    domain: str = field(init=False)
    original_name: str | None = None
    platform: str | None = None
    config_entry_id: str | None = None
    device_id: str | None = None
    orphaned_timestamp: float | None = None
    disabled_by: str | None = None
    modified_at: object | None = None
    area_id: str | None = None
    icon: str | None = None
    original_icon: str | None = None

    def __post_init__(self):
        self.domain = self.entity_id.split(".", 1)[0]


@dataclass
class FakeDeletedEntityEntry:
    entity_id: str
    name: str | None = None
    platform: str | None = None
    config_entry_id: str | None = None
    orphaned_timestamp: float | None = None


class FakeRegistry:
    def __init__(
        self,
        entities: dict[str, FakeEntityEntry],
        deleted_entities: dict[str, FakeDeletedEntityEntry] | None = None,
    ):
        self.entities = entities
        self.deleted_entities = deleted_entities or {}
        self.removed: list[str] = []

    def async_get(self, entity_id: str):
        return self.entities.get(entity_id)

    def async_remove(self, entity_id: str):
        self.removed.append(entity_id)


class FakeServices:
    def async_register(self, *args, **kwargs):
        return None


class FakeHass:
    def __init__(self, registry: FakeRegistry, config_dir: Path):
        self.data: dict[str, Any] = {}
        self._registry = registry
        self.config = SimpleNamespace(path=lambda *names: str(Path(config_dir, *names)))
        self.services = FakeServices()

    async def async_add_executor_job(self, func, *args):
        return func(*args)


class FakeCall:
    def __init__(self, hass: FakeHass, data: dict[str, Any] | None = None):
        self.hass = hass
        self.data = data or {}


class FakeRequest:
    def __init__(self, hass: FakeHass, is_admin: bool):
        self.app = {"hass": hass}
        self.query = {}
        self._hass_user = SimpleNamespace(is_admin=is_admin)

    def get(self, key: str, default=None):
        if key == "hass_user":
            return self._hass_user
        return default


@pytest.fixture
def fake_registry():
    return FakeRegistry({})


@pytest.fixture
def fake_hass(tmp_path, fake_registry):
    return FakeHass(fake_registry, tmp_path)


@pytest.fixture
def fake_call(fake_hass):
    return FakeCall(fake_hass)
