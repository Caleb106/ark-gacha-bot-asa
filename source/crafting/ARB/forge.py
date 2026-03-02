import ASA.stations
import ASA.stations.custom_stations
import ASA.strucutres
import ASA.strucutres.teleporter
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
import json
#import pytesseract

def indi_forge(metadata):
    ASA.strucutres.inventory.open()
    attempt = 0
    while not ASA.strucutres.inventory.is_open():
        logs.logger.debug(f"the indiforge NAME could not be accessed retrying {attempt} / {bot.config.gacha_attempts}")
        utils.zero()
        utils.set_yaw(metadata.yaw)
        ASA.strucutres.inventory.open()
        if attempt >= bot.config.gacha_attempts:
            logs.logger.error(f"the indiforge NAME could not be accesssed after {attempt} attempts")
            break
        
    # check indi forge
    ASA.strucutres.inventory.transfer_all_from() # removing all cooked reasouces
    # check for 0 slots with OCR 
    # if not 0 slots exit forge depo ( will probably just be for metal but will do anyway)
    # then when slots are 0 we should transfer all again 
    ASA.player.player_inventory.transfer_all_inventory() 