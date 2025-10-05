import discord
import settings
import logs.gachalogs as logs
import task_manager

MAX_ITEMS = 5
MAX_EVENTS = 10

async def _embed_queue(title, queue_obj, is_active: bool):
    embed = discord.Embed(title=title)
    if queue_obj is None or queue_obj.is_empty():
        embed.add_field(name=title, value="empty", inline=False)
        return embed

    added = 0
    for i, entry in enumerate(queue_obj.queue):
        if is_active:
            priority, _, _, task = entry
            line = f"Name: {task.name} | Priority: {priority} | Execution: READY"
        else:
            exec_time, _, priority, task = entry
            line = f"Name: {task.name} | Priority: {priority} | Execution: <t:{int(exec_time)}:R>"
        embed.add_field(name=f"Task {i+1}", value=line, inline=False)
        added += 1
        if added >= MAX_ITEMS:
            remaining = len(queue_obj.queue) - added
            if remaining > 0:
                embed.add_field(name=f"...and {remaining} more", value="\u200b", inline=False)
            break
    return embed

async def post_queues(bot: discord.Client):
    try:
        active_ch = bot.get_channel(getattr(settings, "log_active_queue", 0))
        wait_ch   = bot.get_channel(getattr(settings, "log_wait_queue", 0))
        if active_ch:
            embed = await _embed_queue("Active Queue", getattr(task_manager.scheduler, "active_queue", None), True)
            await active_ch.send(embed=embed)
        if wait_ch:
            embed = await _embed_queue("Waiting Queue", getattr(task_manager.scheduler, "waiting_queue", None), False)
            await wait_ch.send(embed=embed)
    except Exception as e:
        logs.logger.error(f"queue posting failed: {e}")

async def post_activity(bot: discord.Client):
    """Post the latest scheduler activity lines to log_channel_gacha."""
    try:
        ch = bot.get_channel(getattr(settings, "log_channel_gacha", 0))
        if not ch:
            return
        # snapshot and trim
        lines = task_manager.EVENT_LOG.tail(MAX_EVENTS)
        if not lines:
            return
        text = "\n".join(lines)
        embed = discord.Embed(title="Activity", description=f"```\n{text}\n```")
        await ch.send(embed=embed)
    except Exception as e:
        logs.logger.error(f"activity posting failed: {e}")
