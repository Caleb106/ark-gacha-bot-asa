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
    return template.check_template_no_bounds("replicator")

