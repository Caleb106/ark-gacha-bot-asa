import source.logs.gachalogs 
import asyncio
import typing 
import functools
import task_manager

#Use this for commands that take a long time to respond to prevent bot from disconnecting.
async def run_blocking(blocking_func: typing.Callable, *args, **kwargs) -> typing.Any:
    func = functools.partial(blocking_func,*args, **kwargs)
    return await asyncio.to_thread(func)

async def task_manager_start():
    source.logs.gachalogs.logger.debug(f"task_manager_start initiated")
    await run_blocking(task_manager.main)


if __name__ =="__main__":
    pass
