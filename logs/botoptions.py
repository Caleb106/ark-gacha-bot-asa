import asyncio
import functools
import typing

import logs.gachalogs as logs
import settings
from logs import discordbot
import task_manager

async def run_blocking(func: typing.Callable, *args, **kwargs):
    return await asyncio.to_thread(functools.partial(func, *args, **kwargs))

async def task_manager_start():
    logs.logger.debug("task_manager_start initiated")
    await run_blocking(task_manager.main)

async def reporting_loop(bot):
    interval = int(getattr(settings, "queue_post_interval", 60))
    while True:
        await discordbot.post_queues(bot)
        await discordbot.post_activity(bot)
        await asyncio.sleep(max(10, interval))
