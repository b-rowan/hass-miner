"""Config flow for Miner."""
import logging
from typing import Optional

import pyasic
import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_IP,
    CONF_TITLE,
    DOMAIN,
    CONF_WEB_USERNAME,
    CONF_SSH_USERNAME,
    CONF_WEB_PASSWORD,
    CONF_SSH_PASSWORD,
    CONF_RPC_PASSWORD,
)

_LOGGER = logging.getLogger(__name__)

# async def _async_has_devices(hass: HomeAssistant) -> bool:
#     """Return if there are devices that can be discovered."""
#     # TODO Check if there are any devices that can be discovered in the network.
#     devices = await hass.async_add_executor_job(my_pypi_dependency.discover)
#     return len(devices) > 0


# config_entry_flow.register_discovery_flow(DOMAIN, "Miner", _async_has_devices)


async def validate_ip_input(
    data: dict[str, str]
) -> tuple[dict[str, str], Optional[pyasic.AnyMiner]]:
    """Validate the user input allows us to connect."""
    miner_ip = data.get(CONF_IP)

    miner = await pyasic.get_miner(miner_ip)
    if miner is None:
        return {"base": "Unable to connect to Miner, is IP correct?"}, None

    return {}, miner


class MinerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Miner."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._data = {}
        self._miner = None

    async def async_step_user(self, user_input=None):
        """Get miner IP and check if it is available."""
        if user_input is None:
            user_input = {}

        schema = vol.Schema(
            {vol.Required(CONF_IP, default=user_input.get(CONF_IP, "")): str}
        )

        if not user_input:
            return self.async_show_form(step_id="user", data_schema=schema)

        errors, miner = await validate_ip_input(user_input)

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=schema, errors=errors
            )

        self._miner = miner
        self._data.update(user_input)
        return await self.async_step_login()

    async def async_step_login(self, user_input=None):
        """Get miner login credentials."""
        if user_input is None:
            user_input = {}

        schema_data = {}

        if self._miner.api is not None:
            if self._miner.api.pwd is not None:
                schema_data[
                    vol.Optional(
                        CONF_RPC_PASSWORD,
                        default=user_input.get(CONF_RPC_PASSWORD, self._miner.api.pwd),
                    )
                ] = TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.PASSWORD, autocomplete="current-password"
                    )
                )

        if self._miner.web is not None:
            schema_data[
                vol.Required(
                    CONF_WEB_USERNAME,
                    default=user_input.get(CONF_WEB_USERNAME, self._miner.web.username),
                )
            ] = str
            schema_data[
                vol.Optional(
                    CONF_WEB_PASSWORD,
                    default=user_input.get(CONF_WEB_PASSWORD, self._miner.web.pwd),
                )
            ] = TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            )

        if self._miner.ssh is not None:
            schema_data[
                vol.Required(
                    CONF_SSH_USERNAME,
                    default=user_input.get(CONF_SSH_USERNAME, self._miner.ssh.username),
                )
            ] = str
            schema_data[
                vol.Optional(
                    CONF_SSH_PASSWORD,
                    default=user_input.get(CONF_SSH_PASSWORD, self._miner.ssh.pwd),
                )
            ] = TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            )

        schema = vol.Schema(schema_data)
        if not user_input:
            return self.async_show_form(step_id="user", data_schema=schema)

        self._data.update(user_input)
        return await self.async_step_title()

    async def async_step_title(self, user_input=None):
        """Get entity title."""
        title = await self._miner.get_hostname()

        if user_input is None:
            user_input = {}

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_TITLE,
                    default=user_input.get(CONF_TITLE, title),
                ): str,
            }
        )
        if not user_input:
            return self.async_show_form(step_id="title", data_schema=data_schema)

        self._data.update(user_input)

        return self.async_create_entry(title=self._data[CONF_TITLE], data=self._data)
