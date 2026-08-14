from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .panel import async_register_panel
from .services import async_register_services


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    async_register_services(hass)
    await async_register_panel(hass)
    return True
