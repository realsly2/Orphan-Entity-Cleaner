from __future__ import annotations

from custom_components.orphan_cleaner.api import OrphanCleanerResultsView
from custom_components.orphan_cleaner.const import DOMAIN, RESULTS_KEY
from custom_components.orphan_cleaner.views import OrphanCleanerPanelView


def test_results_view_url():
    assert OrphanCleanerResultsView.url == "/api/orphan_cleaner/results"


def test_panel_view_url():
    assert OrphanCleanerPanelView.url == "/orphan-cleaner"


def test_results_view_reads_results(fake_hass):
    fake_hass.data = {DOMAIN: {RESULTS_KEY: [{"entity_id": "sensor.test"}]}}
    view = OrphanCleanerResultsView(fake_hass)

    assert view.hass.data[DOMAIN][RESULTS_KEY] == [{"entity_id": "sensor.test"}]
