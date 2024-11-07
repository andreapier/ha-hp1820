from aiohttp.client_exceptions import ClientResponseError
import logging
from typing import Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .hp1820_client import Hp1820Client

_LOGGER = logging.getLogger(__name__)


class Hp1820Device:
    """Hp1820Device class represents an Hp1820 switch. This method wraps around
    a Hp1820Client so that it can be stateless and just return data,
    while this class persists the status of the switch.
    """

    def __init__(self, config: ConfigEntry, client: Hp1820Client):
        self._ports : Dict[str, bool] = {}
        self._config = config
        self._client = client

    @property
    def ports(self):
        """Iterate over the device's ports.
        This property provides an iterator over the device's inventory, where each item is a tuple
        containing the port's ID and its name.
        Yields:
            tuple: A tuple where the first item is the port ID and the second item is the port name.
        Example:
            >>> device = Hp1820Device()
            >>> list(device.ports)
            [(1, 'enabled'), (2, 'disabled')]
        """
        _LOGGER.debug(f"ports | Ports: {self._ports.items()}")
        return self._ports.items()

    async def update(self):
        """Updates the internal state of the device based on the latest data.

        This method performs the following actions:
        1. Queries for the latest port status using the client.
        2. Updates internal state for ports' status.

        Returns:
            dict: A dictionary containing the latest retrieved port status.

        Raises:
            ClientResponseError: If there's an error while making the HTTP request.

        Attributes updated:
            _ports (dict): Updated ports.
        """
        try:
            await self._login()
            ports = await self._client.get_poe_status()
            _LOGGER.debug(f"update | Succesfully fetched ports status: {ports}")
            self._ports.update(ports)
        except ClientResponseError as err:
            _LOGGER.error(f"update | Error getting ports status: {err.response.text}")
            raise err
        finally:
            await self._logout()
        return self._ports

    def get_status(self, port: str) -> bool:
        """Get the status of a port specified by id.

        Parameters:
            port (str): The port ID.

        Returns:
            bool: True if enabled, False if disabled.
        """

        if port not in self._ports:
            raise ValueError(f"get_status | Port {port} not found")
        
        return self._ports[port]
    
    async def set_poe_status(self, port: str, status: bool):
        """
        Set poe status for a specified port.

        Args:
            port: The ID of the port to change.
            status: The status to set the port to.

        Raises:
            ClientResponseError: If there is an error in the HTTP request to set the port.

        Example:
            To turn off a port with ID '1', use:
            >>> device._set_pos_status(1, False)

            To turn on a port with ID '1', use:
            >>> device._set_pos_status(1, True)
        """
        
        if port not in self._ports:
            raise ValueError(f"set_poe_status | Port {port} not found")
        
        try:
            await self._login()
            await self._client.set_poe_status(port, status)
            self._ports[port] = status
            _LOGGER.debug(f"_set_poe_status | Succesfully set poe status for port: {port} to {status}")
            return True
        except ClientResponseError as err:
            _LOGGER.error(f"_set_poe_status | Error while setting poe status for port {port} to {status}: {err.message}")
            return False
        finally:
            await self._logout()

    async def _login(self):
        """Establish a connection with the Hp1820 switch, to retrieve an access
        token. This method stores the auth information in the client object
        and is used automatically when other methods are called.
        """
        try:
            username = self._config.data[CONF_USERNAME]
            password = self._config.data[CONF_PASSWORD]
            await self._client.login(username, password)
            _LOGGER.debug("_login | Succesfully logged in")
        except ClientResponseError as err:
            _LOGGER.error(f"_login | Error while logging: {err}")
            raise err

    async def _logout(self):
        """Close the connection with the Hp1820 switch.
        """
        try:
            await self._client.logout()
            _LOGGER.debug("_logout | Succesfully logged out")
        except ClientResponseError as err:
            _LOGGER.error(f"_logout | Error while logging out: {err}")
            raise err
