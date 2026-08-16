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
