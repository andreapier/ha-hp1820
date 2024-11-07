import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .devices import Hp1820Device

_LOGGER = logging.getLogger(__name__)


class Hp1820Coordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, device: Hp1820Device, scan_interval: int) -> None:
        self._device = device
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> Optional[Dict[str, Any]]:
        """Update device data asynchronously.

        Returns:
            A dictionary containing the updated data.

        Raises:
            InvalidToken: When the token used for the connection is invalid.
            UpdateFailed: When there's an error in updating the data.
        """

        return await self._device.update()
