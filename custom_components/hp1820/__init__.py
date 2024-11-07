"""Hp1820 integration."""

from functools import partial
import logging

from homeassistant.config_entries import ConfigEntry, ConfigType
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import services
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_IP,
    DOMAIN,
    KEY_COORDINATOR,
    KEY_DEVICE,
    KEY_UNSUBSCRIBER,
    SCAN_INTERVAL_DEFAULT,
)
from .coordinator import Hp1820Coordinator
from .devices import Hp1820Device
from .hp1820_client import Hp1820Client

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SWITCH]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Initialize the Hp1820 integration.

    This method exposes eventual YAML configuration options under the DOMAIN key.
    """
    hass.data[DOMAIN] = config.get(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up a configuration entry for the Hp1820 device in Home Assistant.

    This asynchronous method initializes an Hp1820Device instance to access the LAN service.
    It uses a DataUpdateCoordinator to aggregate status updates from different entities
    into a single request. The method also registers a listener to track changes in the configuration options.

    Args:
        hass (HomeAssistant): The Home Assistant instance.
        config (ConfigEntry): The configuration entry containing the setup details for the device.

    Returns:
        bool: True if the setup was successful, False otherwise.

    Raises:
        Any exceptions raised by the coordinator or the setup process will be propagated up to the caller.
    """

    # Initialize Components
    scan_interval = config.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL_DEFAULT)
    session = async_get_clientsession(hass, verify_ssl=False)
    ip = config.data[CONF_SYSTEM_IP]
    client = Hp1820Client(session, ip)
    device = Hp1820Device(config, client)
    coordinator = Hp1820Coordinator(hass, device, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    # Store a device instance to access the LAN service.
    # It includes a DataUpdateCoordinator shared across entities to get a full
    # status update with a single request.
    hass.data[DOMAIN][config.entry_id] = {
        KEY_DEVICE: device,
        KEY_COORDINATOR: coordinator,
    }

    # Register a listener when option changes
    unsub = config.add_update_listener(options_update_listener)
    hass.data[DOMAIN][config.entry_id][KEY_UNSUBSCRIBER] = unsub

    # Register services
    hass.services.async_register(DOMAIN, "update_state", partial(services.update_state, hass, config.entry_id))

    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config: ConfigEntry):
    """Unload a config entry."""
    unload_ok =  await hass.config_entries.async_unload_platforms(config, PLATFORMS)
    if unload_ok:
        # Call the options unsubscriber and remove the configuration
        hass.data[DOMAIN][config.entry_id][KEY_UNSUBSCRIBER]()
        hass.data[DOMAIN].pop(config.entry_id)

    return unload_ok


async def options_update_listener(hass: HomeAssistant, config: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config.entry_id)
