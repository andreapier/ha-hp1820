import pytest

from custom_components.hp1820.const import DOMAIN, KEY_DEVICE


class TestOptionsFlow:
    @pytest.fixture(autouse=True)
    def setup(self, hass, config_entry, device):
        self.hass = hass
        self.config_entry = config_entry
        # Mock integration setup
        config_entry.add_to_hass(hass)
        hass.data[DOMAIN][config_entry.entry_id] = {
            KEY_DEVICE: device,
        }

    async def test_form_fields(self, hass, config_entry):
        # Ensure form is loaded with the correct fields
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        assert form["type"] == "form"
        assert form["step_id"] == "init"
        assert form["errors"] == {}
        assert list(form["data_schema"].schema.keys()) == [
            "scan_interval",
        ]
        assert form["data_schema"].schema["scan_interval"] == int

    async def test_form_submit_successful_empty(self, hass, config_entry):
        # Ensure an empty form can be submitted successfully
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        # Test
        result = await hass.config_entries.options.async_configure(
            form["flow_id"],
            user_input={},
        )
        await hass.async_block_till_done()
        # Check HA config
        assert result["type"] == "create_entry"
        assert result["title"] == "Hp1820"
        assert result["data"] == {"scan_interval": 120}

    # async def test_form_submit_invalid_type(self, hass, config_entry):
    #     # Ensure it fails if a user submits an option with an invalid type
    #     form = await hass.config_entries.options.async_init(
    #         config_entry.entry_id, context={"show_advanced_options": False}
    #     )
    #     # Test
    #     with pytest.raises(InvalidData) as excinfo:
    #         await hass.config_entries.options.async_configure(
    #             form["flow_id"],
    #             user_input={
    #                 "areas_arm_home": "1",
    #             },
    #         )
    #         await hass.async_block_till_done()
    #     assert excinfo.value.schema_errors["areas_arm_home"] == "Not a list"

    # async def test_form_submit_invalid_input(self, hass, config_entry):
    #     # Ensure it fails if a user submits an option not in the allowed list
    #     form = await hass.config_entries.options.async_init(
    #         config_entry.entry_id, context={"show_advanced_options": False}
    #     )
    #     # Test
    #     with pytest.raises(InvalidData) as excinfo:
    #         await hass.config_entries.options.async_configure(
    #             form["flow_id"],
    #             user_input={
    #                 "areas_arm_home": [
    #                     (3, "Garden"),
    #                 ],
    #             },
    #         )
    #         await hass.async_block_till_done()
    #     assert excinfo.value.schema_errors["areas_arm_home"] == "(3, 'Garden') is not a valid option"

    async def test_form_submit_successful_with_identifier(self, hass, config_entry):
        # Ensure users can submit an option just by using the option ID
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        # Test
        result = await hass.config_entries.options.async_configure(
            form["flow_id"],
            user_input={
                "scan_interval": 1,
            },
        )
        await hass.async_block_till_done()
        # Check HA config
        assert result["type"] == "create_entry"
        assert result["title"] == "Hp1820"
        assert result["data"] == {
            "scan_interval": 1,
        }
        assert result["result"] is True
