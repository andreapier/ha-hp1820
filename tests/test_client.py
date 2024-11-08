import pytest
from aioresponses import aioresponses

from custom_components.hp1820.client import Hp1820Client


def test_client_constructor(session):
    # Ensure that the client is initialized correctly
    client = Hp1820Client(session, "test_ip", "test_protocol")
    assert client._session == session
    assert client._base_url == "test_protocol://test_ip"


def test_client_constructor_with_default(session):
    # Ensure that the client is initialized correctly with default protocol
    client = Hp1820Client(session, "test_ip")
    assert client._session == session
    assert client._base_url == "http://test_ip"


@pytest.mark.asyncio
async def test_client_login_successful(mocker, session):
    client = Hp1820Client(session, "127.0.0.1")
    mocker.spy(session.cookie_jar, "update_cookies")
    with aioresponses() as mocked:
        mocked.post(
            "http://127.0.0.1/htdocs/login/login.lua",
            status=200,
            payload=dict(error=""),
            headers={"Set-Cookie": "SID=test_cookie"},
        )
        await client.login("test_username", "test_password")
        mocked.assert_called_once_with(
            "http://127.0.0.1/htdocs/login/login.lua",
            method="POST",
            data={"username": "test_username", "password": "test_password"},
        )
        session.cookie_jar.update_cookies.assert_called_once()
