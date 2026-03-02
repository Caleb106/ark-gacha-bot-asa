import discord
from discord.ext import commands
from typing import Callable
import asyncio
import pyautogui
import settings
import os 

intents = discord.Intents.default()
pyautogui.FAILSAFE = False
bot = commands.Bot(command_prefix=settings.command_prefix, intents=intents)

async def load_cogs():
    for filename in os.listdir("./source/discord_commands"):
        print(filename)
        if filename.endswith(".py"):
            await bot.load_extension(f"source.discord_commands.{filename[:-3]}")
            
@bot.event
async def on_ready():
    await bot.tree.sync()
    
    logchn = bot.get_channel(settings.log_channel_gacha) 
    if logchn:
        await logchn.send(f'bot ready to start')
    print (f'logged in as {bot.user}')

api_key = settings.discord_api_key

if __name__ =="__main__":
    try:
        asyncio.run(load_cogs())
        bot.run(api_key)
        
    except Exception as e:
        print(f"ERROR:{e}")
        print("you need to have a valid discord API key for the bot to run")
        print("please follow the instructions in the discord server to get your api key")
        input(f"")
        exit()