import discord
import json 
from discord import app_commands
from discord.ext import commands
import asyncio
import time 
import settings 
from source.logs import discordbot,botoptions
import task_manager
import source.gacha_bot.stations as stations
import source.ASA.player.player_inventory as inventory
from source.utility.colour_checks import console_output, output_oranage_tp_pixel
import io
import os
from logger.logger import LOG_PATH, logger
from UI.resources.render import render_resources


class discord_commands(commands.Cog):
    def __init__(self,bot):
        self.bot: commands.Bot = bot
        self.running_task = []
        self.start_time = 0
        self._log_task = None

    async def send_new_logs(self):
        log_channel = self.bot.get_channel(int(settings.log_channel_gacha))
        if log_channel is None:
            logger.warning("Log channel is unavailable; Discord log forwarding is disabled.")
            return
        # Forward new messages without truncating the shared GUI/bot log.
        last_position = os.path.getsize(LOG_PATH) if os.path.exists(LOG_PATH) else 0
        
        while True:
            try:
                with open(LOG_PATH, 'r', encoding="utf-8") as file:
                    file.seek(0, os.SEEK_END)
                    if file.tell() < last_position:
                        last_position = 0
                    file.seek(last_position)
                    new_logs = file.read()
                    last_position = file.tell()
                for start in range(0, len(new_logs), 1800):
                    await log_channel.send(f"New logs:\n```{new_logs[start:start + 1800]}```")
            except (OSError, discord.HTTPException) as error:
                logger.error("Could not forward logs to Discord: %s", error)
            await asyncio.sleep(5)

    def cog_unload(self):
        if self._log_task is not None:
            self._log_task.cancel()

    async def embed_send(self,queue_type):
        log_channel = 0
        if queue_type == "active_queue":
            log_channel = self.bot.get_channel(int(settings.log_active_queue))
        else:
            log_channel = self.bot.get_channel(int(settings.log_wait_queue))
        while True:
            embed_msg = await discordbot.embed_create(queue_type)
            await log_channel.purge()
            await log_channel.send(embed = embed_msg)
            await asyncio.sleep(30)
    
    @app_commands.command(name="pause", description="sends the bot back to render bed for X amount of seconds")
    async def pause(self,interaction: discord.Interaction,time:int):
        task = task_manager.scheduler
        pause_task = stations.pause(time)
        task.add_task(pause_task)
        await interaction.response.send_message(f"pause task added will now pause for {time} seconds once the next task finishes")


    @app_commands.command(name="start", description="Starts the bot")
    async def start(self,interaction: discord.Interaction):
        self.start_time = time.time()
        logchn = self.bot.get_channel(int(settings.log_channel_gacha))
        if logchn:
            await logchn.send(f'bot starting up now')
        
        logger.info("Bot start requested from Discord.")
        if self._log_task is None or self._log_task.done():
            self._log_task = self.bot.loop.create_task(self.send_new_logs())
        
        
        await interaction.response.send_message(f"starting up bot now you have 5 seconds before start")
        time.sleep(5)
        asyncio.create_task(botoptions.task_manager_start())
        while task_manager.started == False:
            await asyncio.sleep(1)
        self.bot.loop.create_task(self.embed_send("active_queue"))
        self.bot.loop.create_task(self.embed_send("waiting_queue"))
    
    async def get_time_diffrence(self,inital):
        time_difference = time.time() - inital
        days = time_difference / 86400
        hours = time_difference / 3600
        minutes = time_difference / 60
        seconds = time_difference

        if days >= 1:
            return f"{round(days,2)} days"
        else:
            return f"{round(hours,2)} hours"

    @app_commands.command(name="info",description="sends analytics for the bot")
    async def info(self,interaction: discord.Interaction):
        if self.start_time == 0:
            await interaction.response.send_message("bot hasnt started up yet")
        else:
            await interaction.response.send_message(f"time since start: {await self.get_time_diffrence(self.start_time)} resets : {inventory.resets}")

    @app_commands.command(name="colour_checks",description="outputs pixel values ")
    async def colour_checks(self,interaction: discord.Interaction):
        await interaction.response.send_message(f"console mean output { console_output.output_mean_colour()} orange pixel {  output_oranage_tp_pixel.get_orange_pixel()}")

    @app_commands.command(name="view_resources", description="Sends a rendered image of the resources farmed")
    async def view_resources(self,interaction: discord.Interaction):
        await interaction.response.send_message(f"Rendering image...")

        # This renders the session resources from resources.json
        resource_image = render_resources()
        buffer = io.BytesIO()
        resource_image.save(buffer, "PNG")
        buffer.seek(0)
        await interaction.channel.send(file=discord.File(buffer, filename="resource_image.png")) 

async def setup(bot: commands.Bot):
    await bot.add_cog(discord_commands(bot))
