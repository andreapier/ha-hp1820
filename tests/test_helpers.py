import pytest
from homeassistant.core import valid_entity_id

from custom_components.hp1820.helpers import generate_entity_id


def test_generate_entity_name_empty(config_entry):
    with pytest.raises(ValueError):
        generate_entity_id(config_entry, "")


def test_generate_entity_name_space(config_entry):
    with pytest.raises(ValueError):
        generate_entity_id(config_entry, " ")


def test_generate_entity_name_with_none(config_entry):
    with pytest.raises(ValueError):
        generate_entity_id(config_entry, None)


def test_generate_entity_name_with_name(config_entry):
    entity_id = generate_entity_id(config_entry, "01")
    assert entity_id == "hp1820.test_ip_01"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_empty_system(hass, config_entry):
    hass.config_entries.async_update_entry(config_entry, data={"system_ip": "127.0.0.1"})
    with pytest.raises(ValueError):
        generate_entity_id(config_entry, "")


def test_generate_entity_name_space_system(hass, config_entry):
    hass.config_entries.async_update_entry(config_entry, data={"system_ip": "127.0.0.1"})
    with pytest.raises(ValueError):
        generate_entity_id(config_entry, " ")


def test_generate_entity_name_with_none_system(hass, config_entry):
    hass.config_entries.async_update_entry(config_entry, data={"system_ip": "127.0.0.1"})
    with pytest.raises(ValueError):
        generate_entity_id(config_entry, None)


def test_generate_entity_name_with_name_system(hass, config_entry):
    hass.config_entries.async_update_entry(config_entry, data={"system_ip": "127.0.0.1"})
    entity_id = generate_entity_id(config_entry, "01")
    assert entity_id == "hp1820.127_0_0_1_01"
    assert valid_entity_id(entity_id)
