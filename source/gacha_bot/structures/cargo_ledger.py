import time
import settings
import json
from source.utility import utils ,template , windows ,variables ,screen ,local_player
from logger.logger import logger
from source.ASA.strucutres import teleporter , inventory
from source.ASA.stations import custom_stations
from source.ASA.player import player_inventory , player_state
import source.gacha_bot.config 

def is_open():
    return template.check_template_no_bounds("cargo_ledger",0.7)

def get_y_from_cargo():
    time.sleep(0.2*settings.lag_offset)
    utils.turn_down(20)
    time.sleep(0.2*settings.lag_offset)
    inventory.open()
    if is_open():
        inventory.search_in_object("Trap")
        inventory.hover_inv_slot(0,0)
        time.sleep(0.2*settings.lag_offset)
        x,y = inventory.get_inv_slot_loc(0,0)
        windows.click(x,y)
        windows.click(x,y)
        time.sleep(0.2*settings.lag_offset)
        inventory.transfer_all_from() 
    inventory.close()
    time.sleep(0.2*settings.lag_offset)
    utils.turn_up(20)
    time.sleep(0.2*settings.lag_offset)
    ...
