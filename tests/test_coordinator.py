from datetime import timedelta

import pytest
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.hp1820.coordinator import Hp1820Coordinator


def test_coordinator_constructor(hass, device):
    # Ensure that the coordinator is initialized correctly
    coordinator = Hp1820Coordinator(hass, device, 42)
    assert coordinator.name == "hp1820"
    assert coordinator.update_interval == timedelta(seconds=42)
    assert coordinator._device is device


@pytest.mark.asyncio
async def test_coordinator_async_update_no_data(coordinator):
    # Ensure that the coordinator returns an empty dict if no changes are detected
    coordinator._device.update.return_value = {}

    await coordinator.async_refresh()
    assert coordinator.data == {}


@pytest.mark.asyncio
async def test_coordinator_async_update_with_data(coordinator):
    # Ensure that the coordinator returns data when changes are detected
    await coordinator.async_refresh()
    assert coordinator.data == {
        "1": True,
        "2": False,
    }


@pytest.mark.asyncio
async def test_coordinator_first_refresh_update(coordinator):
    # Ensure the first refresh updates before joining the scheduler
    # This is required to avoid registering entities without a proper state
    coordinator.data = None
    coordinator._device.update.return_value = {}

    await coordinator.async_config_entry_first_refresh()
    assert coordinator._device.update.call_count == 1


@pytest.mark.asyncio
async def test_coordinator_first_refresh_auth_failed(coordinator, client_response_error):
    # Ensure a configuration exception is raised if the first refresh fails
    coordinator.data = None
    coordinator._device.update.side_effect = client_response_error(401)
    # Test
    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()


@pytest.mark.asyncio
async def test_coordinator_first_refresh_update_failed(coordinator, client_response_error):
    # Ensure a configuration exception is raised if the first refresh fails
    coordinator.data = None
    coordinator._device.update.side_effect = client_response_error(500)
    # Test
    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()
