import logging

from homeassistant.components import persistent_notification
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    KEY_COORDINATOR,
    KEY_DEVICE,
    NOTIFICATION_IDENTIFIER,
    NOTIFICATION_MESSAGE,
    NOTIFICATION_TITLE,
)
from .devices import Hp1820Device
from .helpers import generate_entity_id

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device = hass.data[DOMAIN][entry.entry_id][KEY_DEVICE]
    coordinator = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR]
    ports = []

    # Iterate through the ports of the device and create PortPoeSwitch objects
    for port_id, _ in device.ports:
        unique_id = f"{entry.entry_id}_{DOMAIN}_{port_id}"
        ports.append(PoePortSwitch(unique_id, port_id, entry, port_id.zfill(2), coordinator, device))

    async_add_entities(ports)


class PoePortSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a poe port switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        unique_id: str,
        port_id: str,
        config: ConfigEntry,
        name: str,
        coordinator: DataUpdateCoordinator,
        device: Hp1820Device,
    ) -> None:
        """Construct."""
        super().__init__(coordinator)
        self.entity_id = generate_entity_id(config, name)
        self._name = name
        self._device = device
        self._unique_id = unique_id
        self._port_id = port_id

    @property
    def unique_id(self) -> str:
        """Return the unique identifier."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of this entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the icon used by this entity."""
        return "hass:power-standby"

    @property
    def is_on(self) -> bool:
        """Return the switch status (on/off)."""
        return self._device.get_status(self._port_id)

    async def async_turn_off(self):
        """Turn the entity off."""
        result = await self._device.set_poe_status(self._port_id, False)
        if not result:
            persistent_notification.async_create(
                self.hass, NOTIFICATION_MESSAGE, NOTIFICATION_TITLE, NOTIFICATION_IDENTIFIER
            )
        else:
            self.coordinator.async_set_updated_data(self._device.ports)

    async def async_turn_on(self):
        """Turn the entity off."""
        result = await self._device.set_poe_status(self._port_id, True)
        if not result:
            persistent_notification.async_create(
                self.hass, NOTIFICATION_MESSAGE, NOTIFICATION_TITLE, NOTIFICATION_IDENTIFIER
            )
        else:
            self.coordinator.async_set_updated_data(self._device.ports)
