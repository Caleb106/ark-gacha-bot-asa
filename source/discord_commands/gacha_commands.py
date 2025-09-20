import discord
import json 
from discord import app_commands
from discord.ext import commands

def load_json(json_file:str):
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []  

def save_json(json_file:str,data):
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

class gacha_commands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @app_commands.command(name="add_gacha", description="add a new gacha station to the data")
    async def add_gacha(self,interaction: discord.Interaction, name: str, teleporter: str, resource_type: str ,direction: str):
        data = load_json("json_files/gacha.json")

        for entry in data:
            if entry["name"] == name:
                await interaction.response.send_message(f"a gacha station with the name '{name}' already exists", ephemeral=True)
                return
            
        new_entry = {
            "name": name,
            "teleporter": teleporter,
            "resource_type": resource_type,
            "side" : direction
        }
        data.append(new_entry)

        save_json("json_files/gacha.json",data)

        await interaction.response.send_message(f"added new gacha station: {name}")

    @app_commands.command(name="list_gacha", description="list all gacha stations")
    async def list_gacha(self,interaction: discord.Interaction):

        data = load_json("json_files/gacha.json")
        if not data:
            await interaction.response.send_message("no gacha stations found", ephemeral=True)
            return


        response = "gacha Stations:\n"
        for entry in data:
            response += f"- **{entry['name']}**: teleporter `{entry['teleporter']}`, resource `{entry['resource_type']}` gacha on the `{entry['side']}` side \n"

        await interaction.response.send_message(response)

async def setup(bot):
    await bot.add_cog(gacha_commands(bot))