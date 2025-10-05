import discord
from discord.ext import commands
import asyncio
from logs import botoptions
import settings
import json
import time
from logs import discordbot
import bot.stations as stations
import task_manager
import win32gui
import win32con
import sys
import pygetwindow as gw
from compat_input import pyautogui  # 3.13-safe input shim

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=settings.command_prefix, intents=intents)

running_tasks = []

def load_json(json_file: str):
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_json(json_file: str, data):
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

async def send_new_logs():
    log_channel = bot.get_channel(settings.log_channel_gacha)
    last_position = 0
    while True:
        try:
            with open("logs/logs.txt", 'r') as file:
                file.seek(last_position)
                new_logs = file.read()
                if new_logs and log_channel:
                    await log_channel.send(f"New logs:\n```{new_logs}```")
                last_position = file.tell()
        except FileNotFoundError:
            pass
        await asyncio.sleep(5)

@bot.tree.command(name="add_gacha", description="add a new gacha station to the data")
async def add_gacha(interaction: discord.Interaction, name: str, teleporter: str, resource_type: str, direction: str):
    data = load_json("json_files/gacha.json")
    for entry in data:
        if entry["name"] == name:
            await interaction.response.send_message(f"a gacha station with the name '{name}' already exists", ephemeral=True)
            return
    new_entry = {
        "name": name,
        "teleporter": teleporter,
        "resource_type": resource_type,
        "side": direction
    }
    data.append(new_entry)
    save_json("json_files/gacha.json", data)
    await interaction.response.send_message(f"added new gacha station: {name}")

@bot.tree.command(name="list_gacha", description="list all gacha stations")
async def list_gacha(interaction: discord.Interaction):
    data = load_json("json_files/gacha.json")
    if not data:
        await interaction.response.send_message("no gacha stations found", ephemeral=True)
        return
    response = "gacha Stations:\n"
    for entry in data:
        response += f"- **{entry['name']}**: teleporter `{entry['teleporter']}`, resource `{entry['resource_type']} gacha on the `{entry['side']}` side `\n"
    await interaction.response.send_message(response)

@bot.tree.command(name="add_pego", description="add a new pego station to the data")
async def add_pego(interaction: discord.Interaction, name: str, teleporter: str, delay: int):
    data = load_json("json_files/pego.json")
    for entry in data:
        if entry["name"] == name:
            await interaction.response.send_message(f"a pego station with the name '{name}' already exists", ephemeral=True)
            return
    new_entry = {
        "name": name,
        "teleporter": teleporter,
        "delay": delay
    }
    data.append(new_entry)
    save_json("json_files/pego.json", data)
    await interaction.response.send_message(f"added new pego station: {name}")

@bot.tree.command(name="list_pego", description="list all pego stations")
async def list_pego(interaction: discord.Interaction):
    data = load_json("json_files/pego.json")
    if not data:
        await interaction.response.send_message("no pego stations found", ephemeral=True)
        return
    response = "pego Stations:\n"
    for entry in data:
        response += f"- **{entry['name']}**: teleporter `{entry['teleporter']}`, delay `{entry['delay']}`\n"
    await interaction.response.send_message(response)

@bot.tree.command(name="pause", description="sends the bot back to render bed for X amount of seconds")
async def reset(interaction: discord.Interaction, time: int):
    task = task_manager.scheduler
    pause_task = stations.pause(time)
    task.add_task(pause_task)
    await interaction.response.send_message(f"pause task added will now pause for {time} seconds once the next task finishes")

async def embed_send(queue_type):
    if queue_type == "active_queue":
        log_channel = bot.get_channel(settings.log_active_queue)
    else:
        log_channel = bot.get_channel(settings.log_wait_queue)
    interval = int(getattr(settings, "queue_post_interval", 60))
    while True:
        embed_msg = await discordbot.embed_create(queue_type)
        if log_channel:
            try:
                await log_channel.purge()
            except Exception:
                pass
            await log_channel.send(embed=embed_msg)
        await asyncio.sleep(max(10, interval))

@bot.tree.command()
async def start(interaction: discord.Interaction):
    global running_tasks
    logchn = bot.get_channel(settings.log_channel_gacha)
    if logchn:
        await logchn.send('bot starting up now')

    # reset log file
    try:
        with open("logs/logs.txt", 'w') as file:
            file.write("")
    except FileNotFoundError:
        pass

    running_tasks.append(bot.loop.create_task(send_new_logs()))

    await interaction.response.send_message("starting up bot now you have 5 seconds before start")
    await asyncio.sleep(5)
    running_tasks.append(asyncio.create_task(botoptions.task_manager_start()))
    while task_manager.started is False:
        await asyncio.sleep(1)
    running_tasks.append(bot.loop.create_task(embed_send("active_queue")))
    running_tasks.append(bot.loop.create_task(embed_send("waiting_queue")))

@bot.tree.command()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down script...")
    print("Shutting down script...")
    cmd_windows = [win for win in gw.getAllWindows() if "cmd" in win.title.lower() or "system32" in win.title.lower()]
    if cmd_windows:
        cmd_window = cmd_windows[0]
        hwnd = cmd_window._hWnd
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(1)
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        print("Shutting down...")
        sys.exit()
    else:
        print("No CMD window found.")

@bot.event
async def on_ready():
    await bot.tree.sync()
    logchn = bot.get_channel(settings.log_channel_gacha)
    if logchn:
        await logchn.send('bot ready to start')
    print(f'logged in as {bot.user}')

api_key = settings.discord_api_key

if __name__ == "__main__":
    if len(api_key) < 4:
        print("you need to have a valid discord API key for the bot to run")
        print("please follow the instructions in the discord server to get your api key")
        raise SystemExit(1)
    bot.run(api_key)
