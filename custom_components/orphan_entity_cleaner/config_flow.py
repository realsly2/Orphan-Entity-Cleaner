# custom_components/orphan_entity_cleaner/config_flow.py
from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN

class OrphanEntityCleanerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return self.async_create_entry(title="Orphan Entity Cleaner", data={})
