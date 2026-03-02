import discord
import task_manager
import source.logs.gachalogs

async def embed_create(queue_type):
    try:
        embed = discord.Embed(title=f"{queue_type}")
        
        queue = getattr(task_manager.scheduler, queue_type, None)

        if queue is None or queue.is_empty():
            embed.add_field(name=queue_type, value="empty")
            return embed
        
        count = 0
        for i, entry in enumerate(queue.queue):
            if count >= 5:
                embed.add_field(
                    name=f"...and {len(queue.queue) - 5} more tasks.",
                    value="",
                    inline=False
                )
                break
            if isinstance(queue, task_manager.priority_queue_prio):
                priority, exec_time, _, task = entry
                embed.add_field(
                    name=f"Task {i+1}",
                    value=f"Name: {task.name} | Priority: {priority} | Execution: READY",
                    inline=False
                )
            else:
                exec_time, _, priority, task = entry
                embed.add_field(
                    name=f"Task {i+1}",
                    value=f"Name: {task.name} | Priority: {priority} | Execution: <t:{int(exec_time)}:R>",
                    inline=False
                )
            count += 1
        return embed
    except Exception as e:
        source.logs.gachalogs.logger.error(f"error in embed_create: {e}")
        return discord.Embed(title="error", description=str(e))
if __name__ =="__main__":
    pass
