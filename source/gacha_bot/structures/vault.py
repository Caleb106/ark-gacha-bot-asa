import time 
import settings
import json
from source.utility import utils ,template , windows ,variables ,screen ,local_player ,ocr
from logger.logger import logger
from source.ASA.strucutres import teleporter , inventory
from source.ASA.stations import custom_stations
from source.ASA.player import player_inventory , player_state
import source.gacha_bot.config 

def load_vault_data():
    with open("json_files/vaults.json", 'r') as file:
        data = json.load(file)
    return data

def see_vault_full():
    loc = {"start_x": 1424, "start_y": 706, "width": 42, "height": 20}
    scale = screen.screen_resolution / 1440
    text = str(ocr.int_only(int(loc["start_x"] * scale), int(loc["start_y"] * scale), int(loc["width"] * scale), int(loc["height"] * scale)))
    if "350" in text:
        return True , 350
    if text == "":
        text = 0 # for some reason 0 didnt appear
    try:
        text = int(text)
    except Exception as e:
        text = 0
    return False , text