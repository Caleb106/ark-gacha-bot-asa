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

class dedi_select(discord.ui.Select):
    def __init__(self, data):
        options = [
            discord.SelectOption(label=item["dediID"], value=item["dediID"])
            for item in data
        ]
        super().__init__(placeholder="choose a dediID", options=options)
        self.data = data

    async def callback(self, interaction: discord.Interaction):
        chosen = self.values[0]
        entry = next((item for item in self.data if item["dediID"] == chosen), None)

        if entry:
            boxes = entry["dediBoxes"]
            msg_lines = [f"**{chosen}** contains:"]
            x = 0
            for box in boxes:
                x += 1
                resource = box["resource"]
                msg_lines.append(f"{x} {resource} ")

            await interaction.response.send_message("\n".join(msg_lines))
        else:
            await interaction.response.send_message("no data found")

class dedi_view(discord.ui.View):
    def __init__(self, data):
        super().__init__() 
        self.add_item(dedi_select(data))

class dedi_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="list_dedi", description="list the dedis in json_files")
    async def list_dedi(self, interaction: discord.Interaction):
        dedi_data = load_json("json_files/dedis.json")

        await interaction.response.send_message(
            "Select a dediID from the menu below:",
            view=dedi_view(dedi_data),
        )
    @app_commands.command(name="change_resource", description="add the resource from the dediID and location")
    async def change_resource(self, interaction: discord.Interaction,resource:str,dedi_id:str,location:int):
        dedi_data = load_json("json_files/dedis.json")
        for x in range(len(dedi_data)):
            if dedi_id == dedi_data[x]["dediID"]:
                previous = dedi_data[x]["dediBoxes"][location-1]["resource"]
                dedi_data[x]["dediBoxes"][location-1]["resource"] = resource
                save_json("json_files/dedis.json",dedi_data)
                await interaction.response.send_message(
                    f"changed {previous} to {resource} at position {location} in the dedi stack"
                )
                return
        await interaction.response.send_message("unable to change the dedi type")



'''    
class dedi_commands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @app_commands.command(name="list_dedi", description="list the dedis in json_files")
    async def list_dedi(self,interaction: discord.Interaction):
        data = load_json(f"json_files/dedis.json")
        for x in range(len(data)):
            print(data[x]["dediID"])

'''


async def setup(bot):
    await bot.add_cog(dedi_commands(bot))