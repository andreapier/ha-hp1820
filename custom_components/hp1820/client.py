import json
import logging
import re as regex
from typing import Dict
from urllib.parse import urljoin

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError

_LOGGER = logging.getLogger(__name__)


class Hp1820Client:
    def __init__(self, session: ClientSession, host: str, protocol: str = "http"):
        self._base_url = f"{protocol}://{host}"
        self._session = session

    async def login(self, username: str, password: str):
        payload = {"username": username, "password": password}

        try:
            async with await self._httpPost("/htdocs/login/login.lua", payload) as raw_response:
                response = await raw_response.json()
                if response["error"]:
                    raise ClientResponseError(raw_response)
                self._session.cookie_jar.update_cookies({"SID": raw_response.cookies["SID"]})
        except ClientResponseError as err:
            _LOGGER.error(f"login | Login failed: {err}")
            raise err

    async def logout(self):
        async with await self._httpGet("/htdocs/pages/main/logout.lsp"):
            _LOGGER.debug("logout | logged out")

    async def get_poe_state(self) -> Dict[str, str]:
        # first_row = [
        #   'Interface', 'Admin Mode', 'Priority', 'Schedule', 'High Power Mode',
        #   'Power Detect Type', 'Power Limit Type', 'Status', 'Fault Status'
        # ]
        async with await self._httpGet("/htdocs/pages/base/poe_port_cfg.lsp") as raw_response:
            text_response = await raw_response.text()
            rows = self._parse_status(text_response)
            return {x[0]: x[1].lower() == "enabled" for x in rows}  # index 0 is port number, index 1 is enabled status

    async def set_poe_state(self, port: str, status: bool):
        config = {
            "admin_mode_sel": "enabled" if status else "disabled",
            "schedule_sel": "none",
            "priority_sel": "low",
            "high_power_mode_sel": "disable",
            "power_detect_type_sel": "4pt_dot3af",
            "power_limit_type_sel": "dot3af",
            "power_limit": "",
            "interface": port,
        }
        await self._set_poe_state_extended(config)

    async def _set_poe_state_extended(self, config):
        payload = {
            "admin_mode_sel[]": config["admin_mode_sel"],  # enabled, disabled
            "schedule_sel[]": config["schedule_sel"],  # none, 1, 2
            "priority_sel[]": config["priority_sel"],  # critical, high, low
            "high_power_mode_sel[]": config["high_power_mode_sel"],  # dot3at, disable
            "power_detect_type_sel[]": config["power_detect_type_sel"],  # 4pt_dot3af, 4pt_dot3af_leg
            "power_limit_type_sel[]": config["power_limit_type_sel"],  # dot3af, user
            "power_limit": config["power_limit"],  # 3-15.4
            "intfStr": config["interface"],  # 1-12
            "b_modal1_clicked": "b_modal1_submit",
        }

        async with await self._httpPost("/htdocs/pages/base/poe_port_cfg_modal.lsp", payload) as response:
            _LOGGER.debug(
                f"_set_poe_state_extended | Port {config['interface']}={config['admin_mode_sel']}: {response.status}"
            )

    async def _httpGet(self, url: str):
        full_url = self._getFullUrl(url)
        response = await self._session.get(full_url)
        response.raise_for_status()
        return response

    async def _httpPost(self, url: str, payload):
        full_url = self._getFullUrl(url)
        response = await self._session.post(full_url, data=payload)
        response.raise_for_status()
        return response

    def _getFullUrl(self, path: str):
        return urljoin(self._base_url, path)

    def _parse_status(self, text_response: str):
        search_result = regex.search("aDataSet = (.*)var aColumns", text_response.replace("\n", ""))
        string = "" if search_result is None else search_result.group(1)
        # swap single quote and double quote because jQuery format is not compatible with JSON
        string = string.replace("'", "`").replace('"', "'").replace("`", '"')
        string = string.rstrip().rstrip(";")
        obj = json.loads(string)
        return [i[1:] for i in obj]
