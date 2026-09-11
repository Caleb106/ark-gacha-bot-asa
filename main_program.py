import discord
from discord.ext import commands
import asyncio
import pyautogui
import settings
import os 
from logger.logger import logger

'''starts the discord bot without a GUI'''

intents = discord.Intents.default()
pyautogui.FAILSAFE = False
bot = commands.Bot(command_prefix=settings.command_prefix, intents=intents)

async def load_cogs():
    for filename in os.listdir("./source/discord_commands"):
        logger.info(f"loading cog: {filename}")
        if filename.endswith(".py"):
            await bot.load_extension(f"source.discord_commands.{filename[:-3]}")
            
@bot.event
async def on_ready():
    await bot.tree.sync()
    
    logchannel = bot.get_channel(int(settings.log_channel_gacha))
    if logchannel:
        await logchannel.send(f'bot ready to start')
    logger.info(f'bot is logged in as  {bot.user} and is ready to start')

api_key = settings.discord_api_key

if __name__ =="__main__":
    error_str = None
    try:
        asyncio.run(load_cogs())
        bot.run(api_key, log_handler=None)

    # The UI Exception hook might catch all these errors but lets make sure its all seen
    
    except discord.LoginFailure as e: # Catches the invalid token error instead of catching all errors and assuming its the token.
        error_str = f"Your Discord API key is invalid or missing. \
              \nPlease follow the instructions in the discord server to get your api key"

    except discord.Forbidden as e: # Catches errors when the bot tries to do an action it does not have permission to do.
        error_str = f"The bot does not have permission to do an required action. \
              \nLook over your bot permissions and make sure it has the required permissions to run. \
              \n\n\nError: {e}"

    except Exception as e: # Catches all other errors that may occur we dont know what to expect and handle here 
        error_str = f"An unknown error has occured while starting the bot. Please report this to the discord server. \
              \n\n\nError: {e}"

    finally:
        if error_str:
            logger.error(error_str)