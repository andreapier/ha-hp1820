import pytest
from aiohttp.client_exceptions import ClientResponseError

from custom_components.hp1820.devices import Hp1820Device


def test_device_constructor(config_entry, client):
    """Should initialize defaults attributes to run properly."""
    device = Hp1820Device(config_entry, client)
    # Test
    assert device._config == config_entry
    assert device._client == client
    assert device._ports == {}


@pytest.mark.asyncio
async def test_device_login(config_entry, client):
    """Should call login when updating data."""
    device = Hp1820Device(config_entry, client)
    client.get_poe_state.return_value = {}
    # Test
    await device.update()
    assert device._client.login.call_count == 1
    assert "test_user" == device._client.login.call_args[0][0]
    assert "test_password" == device._client.login.call_args[0][1]


@pytest.mark.asyncio
async def test_device_login_error(config_entry, client, client_response_error):
    """Should not swallow authentication errors (401)."""
    device = Hp1820Device(config_entry, client)
    client.login.side_effect = client_response_error(401)
    # Test
    with pytest.raises(ClientResponseError):
        await device.update()
    assert device._client.login.call_count == 1


@pytest.mark.asyncio
async def test_device_logout_error(config_entry, client, client_response_error):
    """Should not swallow logout errors (401)."""
    device = Hp1820Device(config_entry, client)
    client.logout.side_effect = client_response_error(401)
    # Test
    with pytest.raises(ClientResponseError):
        await device.update()
    assert device._client.login.call_count == 1
    assert device._client.logout.call_count == 1


@pytest.mark.asyncio
async def test_device_update_success(config_entry, client):
    """Should check store the ports' status in the device object."""
    device = Hp1820Device(config_entry, client)
    device._client.get_poe_state.return_value = {"1": True, "2": False}

    await device.update()

    assert device._client.get_poe_state.call_count == 1
    assert device._ports == {"1": True, "2": False}
    assert device._client.login.call_count == 1
    assert device._client.logout.call_count == 1


@pytest.mark.asyncio
async def test_device_update_http_error(config_entry, client, client_response_error):
    """Tests if device's update method raises an when querying and logout is still called."""
    device = Hp1820Device(config_entry, client)
    device._client.get_poe_state.side_effect = client_response_error(500)

    with pytest.raises(ClientResponseError):
        await device.update()

    assert device._client.get_poe_state.call_count == 1
    assert device._client.logout.call_count == 1


@pytest.mark.asyncio
async def test_device_update_generic_error(config_entry, client):
    """Should not crash if an exception is raised and logout is still called."""
    device = Hp1820Device(config_entry, client)
    device._client.get_poe_state.side_effect = Exception("Unexpected")

    with pytest.raises(Exception):
        await device.update()


def test_get_port_state_before_update(device):
    """Should rasie error if no data is available"""
    device._ports = {}

    for num in range(1, 13):
        with pytest.raises(ValueError):
            device.get_port_state(f"{num}")


def test_get_port_state_unknown_port(device):
    """Should rasie error if port is not known"""
    device._ports = {"1": True}

    with pytest.raises(ValueError):
        device.get_port_state("2")


def test_get_port_state_after_update(device):
    """Should return port status when available"""
    device._ports = {"1": True, "2": False}

    assert device.get_port_state("1") is True
    assert device.get_port_state("2") is False


@pytest.mark.asyncio
async def test_set_port_state_before_update(device):
    """Should rasie error if no data is available"""
    device._ports = {}

    for num in range(1, 13):
        with pytest.raises(ValueError):
            await device.set_port_state(f"{num}", True)


@pytest.mark.asyncio
async def test_set_port_state_unknown_port(device):
    """Should rasie error if port is not known"""
    device._ports = {"1": True}

    with pytest.raises(ValueError):
        await device.set_port_state("2", True)


@pytest.mark.asyncio
async def test_set_port_state_after_update(config_entry, client):
    """Should set port status when available"""
    device = Hp1820Device(config_entry, client)
    device._ports = {"1": True, "2": False}

    success = await device.set_port_state("1", False)

    assert success is True
    assert device._client.set_poe_state.call_count == 1
    assert device._ports == {"1": False, "2": False}
    assert device._client.login.call_count == 1
    assert device._client.logout.call_count == 1


@pytest.mark.asyncio
async def test_set_port_state_with_error(config_entry, client, client_response_error):
    """Should call logout even with errors"""
    client.set_poe_state.side_effect = client_response_error(500)
    device = Hp1820Device(config_entry, client)
    device._ports = {"1": True, "2": False}

    success = await device.set_port_state("1", False)

    assert success is False
    assert device._client.set_poe_state.call_count == 1
    assert device._ports == {"1": True, "2": False}
    assert device._client.login.call_count == 1
    assert device._client.logout.call_count == 1
