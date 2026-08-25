# tests/test_panel.py
from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.orphan_cleaner.panel import (
    FRONTEND_DIR,
    JS_FILENAME,
    JS_URL_PATH,
    async_register_panel,
)


def test_frontend_js_file_exists_and_is_nonempty():
    js_path = FRONTEND_DIR / JS_FILENAME
    assert js_path.is_file(), f"Panel-JS fehlt: {js_path}"
    content = js_path.read_text(encoding="utf-8")
    assert "customElements.define(" in content
    assert "orphan-cleaner-panel" in content
    assert "_describeError" in content
    assert "orphan_cleaner/results API call in _refreshResults()" in content


@pytest.mark.asyncio
async def test_async_register_panel_registers_static_path_and_frontend_panel(monkeypatch):
    static_calls = []
    panel_calls = []

    class FakeHttp:
        async def async_register_static_paths(self, configs):
            static_calls.append(configs)

    class FakeHassObj:
        def __init__(self):
            self.http = FakeHttp()

    def fake_register_built_in_panel(hass, component_name, **kwargs):
        panel_calls.append((component_name, kwargs))

    monkeypatch.setattr(
        "custom_components.orphan_cleaner.panel.frontend.async_register_built_in_panel",
        fake_register_built_in_panel,
    )

    hass = FakeHassObj()
    await async_register_panel(hass)

    assert len(static_calls) == 1
    config = static_calls[0][0]
    assert config.url_path == JS_URL_PATH
    assert Path(config.path) == FRONTEND_DIR / JS_FILENAME

    assert len(panel_calls) == 1
    component_name, kwargs = panel_calls[0]
    assert component_name == "custom"
    assert kwargs["config"]["_panel_custom"]["name"] == "orphan-cleaner-panel"
    assert kwargs["config"]["_panel_custom"]["js_url"] == JS_URL_PATH
    assert kwargs["require_admin"] is True
