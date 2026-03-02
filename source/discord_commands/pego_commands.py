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


class pego_commands(commands.Cog): 
    def __init__(self,bot):
        self.bot = bot

    @app_commands.command(name="add_pego", description="add a new pego station to the data")

    async def add_pego(self,interaction: discord.Interaction, name: str, teleporter: str, delay: int):
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

        save_json("json_files/pego.json",data)

        await interaction.response.send_message(f"added new pego station: {name}")

    @app_commands.command(name="list_pego", description="list all pego stations")
    async def list_pego(self,interaction: discord.Interaction):

        data = load_json("json_files/pego.json")
        if not data:
            await interaction.response.send_message("no pego stations found", ephemeral=True)
            return


        response = "pego Stations:\n"
        for entry in data:
            response += f"- **{entry['name']}**: teleporter `{entry['teleporter']}`, delay `{entry['delay']}`\n"

        await interaction.response.send_message(response)#
        
async def setup(bot):
    await bot.add_cog(pego_commands(bot))