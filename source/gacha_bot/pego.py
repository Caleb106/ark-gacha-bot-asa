import time 
import settings
from source.utility import utils ,template , windows ,variables ,screen ,local_player
from source.logs import gachalogs as logs
from source.ASA.strucutres import teleporter , inventory
from source.ASA.stations import custom_stations
from source.ASA.player import player_inventory , player_state
import source.gacha_bot.config 

def pego_pickup(metadata):
    attempt = 0
    utils.turn_up(15)
    time.sleep(0.2*settings.lag_offset)
    inventory.open()
    while not inventory.is_open():
        attempt += 1
        logs.logger.debug(f"the pego at {metadata.name} could not be accessed retrying {attempt} / {source.gacha_bot.config.pego_attempts}")
        utils.zero()
        utils.set_yaw(metadata.yaw)
        utils.turn_up(15)
        time.sleep(0.2*settings.lag_offset)
        inventory.open()
        if attempt >= source.gacha_bot.config.pego_attempts:
            logs.logger.error(f"the pego at {metadata.name} could not be accesssed after {attempt} attempts")
            break

    if inventory.is_open():# prevents pego being FLUNG
        player_inventory.drop_all_inv()
        time.sleep(0.2*settings.lag_offset)
        inventory.transfer_all_from()
        time.sleep(0.2*settings.lag_offset)
        inventory.close() 
        
    time.sleep(0.1*settings.lag_offset)
    utils.turn_down(utils.current_pitch)
    time.sleep(0.1*settings.lag_offset)
        