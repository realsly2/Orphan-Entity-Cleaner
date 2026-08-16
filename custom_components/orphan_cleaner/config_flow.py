# custom_components/orphan_cleaner/config_flow.py
from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .const import DOMAIN, NAME


class OrphanCleanerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow für Orphan Cleaner.

    Die Integration braucht keine Benutzereingaben (kein Host, kein API-Key
    o.ä.) - ein Klick auf "Absenden" reicht, um Panel/Services zu aktivieren.
    Mehrfachinstallation ergibt keinen Sinn (ein Sidebar-Panel, eine
    Entity Registry), daher wird nach der ersten Einrichtung abgebrochen.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Einziger Schritt: bestätigen und fertig."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})

        return self.async_show_form(step_id="user")

    async def async_step_import(
        self, import_data: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Erlaubt bestehenden YAML-Nutzern (orphan_cleaner: in
        configuration.yaml) einen sauberen Umstieg auf einen Config Entry,
        falls HA das künftig anstößt."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title=NAME, data={})
