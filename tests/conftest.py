from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


@dataclass
class FakeEntityEntry:
    entity_id: str
    original_name: str | None = None
    platform: str | None = None
    config_entry_id: str | None = None
    device_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class FakeRegistry:
    def __init__(self, entities: dict[str, FakeEntityEntry]):
        self.entities = entities
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
        self.config = SimpleNamespace(path=lambda name: str(config_dir / name))
        self.services = FakeServices()


class FakeCall:
    def __init__(self, hass: FakeHass, data: dict[str, Any] | None = None):
        self.hass = hass
        self.data = data or {}


@pytest.fixture
def fake_registry():
    return FakeRegistry({})


@pytest.fixture
def fake_hass(tmp_path, fake_registry):
    return FakeHass(fake_registry, tmp_path)


@pytest.fixture
def fake_call(fake_hass):
    return FakeCall(fake_hass)
