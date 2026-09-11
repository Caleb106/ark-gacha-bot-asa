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
    if screen.screen_height != 1440:
        roi = screen.get_screen_roi(int(loc["start_x"] * 0.75), int(loc["start_y"] * 0.75), int(loc["width"] * 0.75), int(loc["height"] * 0.75))
    text = ocr.int_only(loc["start_x"], loc["start_y"], loc["width"], loc["height"])
    if "350" in text:
        return True , 350
    if text == "":
        text = 0 # for some reason 0 didnt appear
    try:
        text = int(text)
    except Exception as e:
        text = 0
    return False , text