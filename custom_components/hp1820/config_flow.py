import logging

import voluptuous as vol
from aiohttp.client_exceptions import ClientResponseError
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import Hp1820Client
from .const import CONF_SCAN_INTERVAL, CONF_SYSTEM_IP, DOMAIN, SCAN_INTERVAL_DEFAULT

_LOGGER = logging.getLogger(__name__)


class Hp1820ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    """Handle a config flow for Hp1820 Switch."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Implement OptionsFlow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration."""
        errors = {}
        if user_input is not None:
            try:
                # Validate credentials
                session = async_get_clientsession(self.hass, verify_ssl=False)
                ip = user_input.get(CONF_SYSTEM_IP)
                username = user_input.get(CONF_USERNAME)
                password = user_input.get(CONF_PASSWORD)
                client = Hp1820Client(session, ip)
                await client.login(username, password)
                await client.logout()
            except ClientResponseError as err:
                if err.status == 401:
                    errors["base"] = "invalid_auth"
                elif 402 <= err.status <= 499:
                    errors["base"] = "client_error"
                elif 500 <= err.status <= 599:
                    errors["base"] = "server_error"
                else:
                    _LOGGER.error(f"Unexpected exception {err}")
                    errors["base"] = "unknown"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error(f"Unexpected exception {err}")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Hp1820", data=user_input)

        # Populate with latest changes
        user_input = {} if user_input is None else user_input
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SYSTEM_IP,
                        description={"suggested_value": user_input.get(CONF_SYSTEM_IP)},
                    ): str,
                    vol.Required(
                        CONF_USERNAME,
                        description={"suggested_value": user_input.get(CONF_USERNAME)},
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        description={"suggested_value": user_input.get(CONF_PASSWORD)},
                    ): str,
                }
            ),
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Reconfigure integration options.

    Available options are:
        * Scan interval: sets the polling time
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Construct."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Hp1820", data=user_input)

        # Populate with latest changes or previous settings
        user_input = user_input or {}
        suggest_scan_interval = user_input.get(CONF_SCAN_INTERVAL) or self.config_entry.options.get(CONF_SCAN_INTERVAL)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        description={"suggested_value": suggest_scan_interval},
                        default=SCAN_INTERVAL_DEFAULT,
                    ): int,
                }
            ),
            errors=errors,
        )
