# tests/test_views.py
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from custom_components.orphan_cleaner.const import DOMAIN, RESULTS_KEY
from custom_components.orphan_cleaner.views import OrphanCleanerResultsView


def test_results_view_url():
    assert OrphanCleanerResultsView.url == "/api/orphan_cleaner/results"


@pytest.mark.asyncio
async def test_results_view_reads_results(fake_hass):
    fake_hass.data = {DOMAIN: {RESULTS_KEY: [{"entity_id": "sensor.test"}]}}
    view = OrphanCleanerResultsView()
    request = SimpleNamespace(app={"hass": fake_hass}, query={})

    response = await view.get(request)
    payload = json.loads(response.body)

    assert payload["results"] == [{"entity_id": "sensor.test"}]
    assert payload["total"] == 1


@pytest.mark.asyncio
async def test_results_view_delete_clears_results(fake_hass):
    fake_hass.data = {DOMAIN: {RESULTS_KEY: [{"entity_id": "sensor.test"}]}}
    view = OrphanCleanerResultsView()
    request = SimpleNamespace(app={"hass": fake_hass}, query={})

    await view.delete(request)

    assert fake_hass.data[DOMAIN][RESULTS_KEY] == []


@pytest.mark.asyncio
async def test_results_view_includes_backup_and_restore_info(fake_hass):
    fake_hass.data = {
        DOMAIN: {
            RESULTS_KEY: [],
            "backups": [{"filename": "orphan_cleaner_backup_x.json", "count": 3}],
            "last_backup_path": "/config/orphan_cleaner_backups/orphan_cleaner_backup_x.json",
            "last_restore": {"restored": ["sensor.a"], "skipped_existing": [], "errors": []},
        }
    }
    view = OrphanCleanerResultsView()
    request = SimpleNamespace(app={"hass": fake_hass}, query={})

    response = await view.get(request)
    payload = json.loads(response.body)

    assert payload["backups"] == [{"filename": "orphan_cleaner_backup_x.json", "count": 3}]
    assert payload["last_backup_path"] == "/config/orphan_cleaner_backups/orphan_cleaner_backup_x.json"
    assert payload["last_restore"]["restored"] == ["sensor.a"]
