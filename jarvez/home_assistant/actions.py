from __future__ import annotations

from jarvez.home_assistant.client import client


async def ac_on() -> str:
    return await client.call_webhook("jarvez_ac_on")


async def relax_lights() -> str:
    return await client.call_webhook("jarvez_relax_lights")


async def goodnight() -> str:
    return await client.call_webhook("jarvez_goodnight")
