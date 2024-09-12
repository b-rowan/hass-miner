"""The Miner component services."""
from __future__ import annotations

import logging

import pyasic
from homeassistant.const import CONF_MAC, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.core import ServiceCall
from voluptuous import Schema

from .const import CONF_IP, CONF_RPC_PASSWORD, CONF_WEB_USERNAME, CONF_WEB_PASSWORD, CONF_SSH_USERNAME, \
    CONF_SSH_PASSWORD
from .const import DOMAIN
from .const import SERVICE_REBOOT
from .const import SERVICE_RESTART_BACKEND

LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Service handler setup."""

    async def get_miners(call: ServiceCall):
        miners = hass.data[DOMAIN]
        miner_ids = call.data[CONF_DEVICE_ID]

        if miner_id is None or miner_id not in miners:
            LOGGER.error(
                f"Cannot get miner, must specify a miner from [{miners}]",
            )
            return
        return await asyncio.gather(*[miners[miner_id].get_miner() for miner_id in miner_ids])

    async def reboot(call: ServiceCall) -> None:
        miners = await get_miners(call)
        await asyncio.gather(*[m.reboot() for m in miners if m is not None else asyncio.sleep(0, False)])

    hass.services.async_register(DOMAIN, SERVICE_REBOOT, reboot)

    async def restart_backend(call: ServiceCall) -> None:
        miner = await get_miner(call)
        await asyncio.gather(*[m.restart_backend() for m in miners if m is not None else asyncio.sleep(0, False)])


    hass.services.async_register(DOMAIN, SERVICE_RESTART_BACKEND, restart_backend)
