import time 
import settings
import json
from source.utility import utils ,template , windows ,variables ,screen ,local_player
from source.logs import gachalogs as logs
from source.ASA.strucutres import teleporter , inventory
from source.ASA.stations import custom_stations
from source.ASA.player import player_inventory , player_state
import source.gacha_bot.config 


def is_open():
    return template.check_template_no_bounds("crop_plot") 

def tek_plot():
    inventory.open()
    if is_open():
        inventory.transfer_all_from() # takeing all from the crop plot
        time.sleep(0.2*settings.lag_offset)
        player_inventory.transfer_all_inventory() # tranfering all back should put back pellets
    inventory.close()
    ...

def plots_stack():
    ...
    
def plots_360():
    ...