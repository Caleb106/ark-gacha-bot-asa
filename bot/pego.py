import ASA.strucutres
import template
import logs.gachalogs as logs
import utils
import windows
import variables
import time 
import settings
import ASA.config 
import ASA.strucutres.inventory
import ASA.player.player_inventory
import bot.config

def pego_pickup(metadata):
    attempt = 0
    utils.turn_up(15)
    time.sleep(0.2*settings.lag_offset)
    ASA.strucutres.inventory.open()
    while not ASA.strucutres.inventory.is_open():
        attempt += 1
        logs.logger.debug(f"the pego at {metadata.name} could not be accessed retrying {attempt} / {bot.config.pego_attempts}")
        utils.zero()
        utils.set_yaw(metadata.yaw)
        utils.turn_up(15)
        time.sleep(0.2*settings.lag_offset)
        ASA.strucutres.inventory.open()
        if attempt >= bot.config.pego_attempts:
            logs.logger.error(f"the pego at {metadata.name} could not be accesssed after {attempt} attempts")
            break

    if ASA.strucutres.inventory.is_open():# prevents pego being FLUNG
        ASA.player.player_inventory.drop_all_inv()
        time.sleep(0.2*settings.lag_offset)
        ASA.strucutres.inventory.transfer_all_from()
        time.sleep(0.2*settings.lag_offset)
        ASA.strucutres.inventory.close() 
        
    time.sleep(0.1*settings.lag_offset)
    utils.turn_down(utils.current_pitch)
    time.sleep(0.1*settings.lag_offset)
        