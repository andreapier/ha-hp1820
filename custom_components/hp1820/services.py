import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, KEY_COORDINATOR

_LOGGER = logging.getLogger(__name__)


async def update_state(hass: HomeAssistant, config_id: str, call: ServiceCall):
    _LOGGER.debug(f"update_state | Triggered action {call.service}")
    coordinator = hass.data[DOMAIN][config_id][KEY_COORDINATOR]
    await coordinator.async_refresh()
