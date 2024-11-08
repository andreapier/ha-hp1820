from homeassistant.core import ServiceCall

from custom_components.hp1820 import services
from custom_components.hp1820.const import DOMAIN


async def test_service_update_state(hass, config_entry, device, coordinator):
    # Ensure `update_state` triggers a full refresh
    hass.data[DOMAIN][config_entry.entry_id] = {
        "device": device,
        "coordinator": coordinator,
    }
    call = ServiceCall(
        domain=DOMAIN,
        service="update_state",
        data={},
    )

    await services.update_state(hass, config_entry.entry_id, call)
    assert device.update.call_count == 1
    assert device.update.call_args == ()
