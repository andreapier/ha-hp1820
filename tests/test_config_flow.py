from unittest.mock import AsyncMock

from homeassistant import config_entries

from custom_components.hp1820.const import DOMAIN

from .helpers import _


async def test_form_fields(hass):
    # Ensure the form is properly generated with fields we expect
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert form["type"] == "form"
    assert form["step_id"] == "user"
    assert form["errors"] == {}
    assert form["data_schema"].schema["username"] == str
    assert form["data_schema"].schema["password"] == str
    assert form["data_schema"].schema["system_ip"] == str


async def test_form_submit_successful_with_input(hass, mocker):
    # Ensure a properly submitted form initializes an Hp1820Client
    m_client = mocker.patch(_("config_flow.Hp1820Client"))
    m_client().login = AsyncMock()
    m_client().logout = AsyncMock()
    m_setup = mocker.patch(_("async_setup"), return_value=True)
    m_setup_entry = mocker.patch(_("async_setup_entry"), return_value=True)
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "system_ip": "test-ip",
        },
    )
    await hass.async_block_till_done()
    # Check Client Authentication
    assert m_client.call_args.args[1] == "test-ip"
    assert m_client().login.call_count == 1
    assert m_client().login.call_args.args == ("test-username", "test-password")
    assert m_client().logout.call_count == 1
    assert m_client().logout.call_args.args == ()
    # Check HA setup
    assert len(m_setup.mock_calls) == 1
    assert len(m_setup_entry.mock_calls) == 1
    assert result["type"] == "create_entry"
    assert result["title"] == "Hp1820"
    assert result["data"] == {
        "username": "test-username",
        "password": "test-password",
        "system_ip": "test-ip",
    }


# async def test_form_submit_required_fields(hass, mocker):
#     # Ensure the form has the expected required fields
#     mocker.patch(_("async_setup"), return_value=True)
#     mocker.patch(_("async_setup_entry"), return_value=True)
#     form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
#     # Test
#     with pytest.raises(InvalidData) as excinfo:
#         await hass.config_entries.flow.async_configure(form["flow_id"], {})
#     await hass.async_block_till_done()
#     assert len(excinfo.value.schema_errors) == 3
#     assert excinfo.value.schema_errors["username"] == "required key not provided"
#     assert excinfo.value.schema_errors["password"] == "required key not provided"
#     assert excinfo.value.schema_errors["system_ip"] == "required key not provided"


async def test_form_submit_wrong_credential(hass, mocker, client_response_error):
    # Ensure the right error is raised for auth exception
    m_client = mocker.patch(_("config_flow.Hp1820Client"))
    m_client().login = client_response_error(401)
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "system_ip": "test-ip",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_auth"


async def test_form_client_errors(hass, mocker, client_response_error):
    # Ensure the right error is raised for 4xx API errors
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    m_client = mocker.patch(_("config_flow.Hp1820Client"))
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test 400-499 status codes
    for code in range(402, 500):
        m_client().login = client_response_error(code)
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "system_ip": "test-ip",
            },
        )
        await hass.async_block_till_done()
        assert result["type"] == "form"
        assert result["errors"]["base"] == "client_error"


async def test_form_server_errors(hass, mocker, client_response_error):
    # Ensure the right error is raised for 5xx API errors
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    m_client = mocker.patch(_("config_flow.Hp1820Client"))
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test 500-599 status codes
    for code in range(500, 600):
        m_client().login = client_response_error(code)
        result = await hass.config_entries.flow.async_configure(
            form["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "system_ip": "test-ip",
            },
        )
        await hass.async_block_till_done()
        assert result["type"] == "form"
        assert result["errors"]["base"] == "server_error"


async def test_form_unknown_errors(hass, mocker, client_response_error):
    # Ensure we catch unexpected status codes
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    m_client = mocker.patch(_("config_flow.Hp1820Client"))
    m_client().login = client_response_error(999)
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test non-error status codes
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "system_ip": "test-ip",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] == "form"
    assert result["errors"]["base"] == "unknown"


async def test_form_generic_exception(hass, mocker):
    # Ensure we catch unexpected exceptions
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    m_client = mocker.patch(_("config_flow.Hp1820Client"))
    m_client().login = AsyncMock(side_effect=Exception())
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "system_ip": "test-ip",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] == "form"
    assert result["errors"]["base"] == "unknown"
