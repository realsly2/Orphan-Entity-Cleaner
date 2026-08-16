# tests/test_config_flow.py
from __future__ import annotations

import pytest

from custom_components.orphan_cleaner.config_flow import OrphanCleanerConfigFlow
from custom_components.orphan_cleaner.const import DOMAIN, NAME


@pytest.mark.asyncio
async def test_user_step_shows_form_then_creates_entry(monkeypatch):
    flow = OrphanCleanerConfigFlow()
    monkeypatch.setattr(flow, "_async_current_entries", lambda include_ignore=True: [])

    # Erster Aufruf ohne Eingabe -> Formular
    result = await flow.async_step_user(None)
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    # Bestätigung -> Entry wird erstellt
    result = await flow.async_step_user({})
    assert result["type"] == "create_entry"
    assert result["title"] == NAME
    assert result["data"] == {}


@pytest.mark.asyncio
async def test_user_step_aborts_if_already_configured(monkeypatch):
    flow = OrphanCleanerConfigFlow()
    monkeypatch.setattr(flow, "_async_current_entries", lambda include_ignore=True: ["existing"])

    result = await flow.async_step_user(None)

    assert result["type"] == "abort"
    assert result["reason"] == "single_instance_allowed"


def test_config_flow_registered_for_domain():
    from homeassistant import config_entries

    assert config_entries.HANDLERS.get(DOMAIN) is OrphanCleanerConfigFlow
