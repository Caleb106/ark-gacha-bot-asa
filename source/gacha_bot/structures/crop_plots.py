import time 
import settings
import json
from source.utility import utils ,template , windows ,variables ,screen ,local_player
from source.logs import gachalogs as logs
from source.ASA.strucutres import teleporter , inventory , indi_forge
from source.ASA.stations import custom_stations
from source.ASA.player import player_inventory , player_state
import source.gacha_bot.config 
import source.ASA.inventories.structures


def harvest_crop():
    inventory.open()
    inventory.search_in_object("y") #get y out of crop plot
    inventory.transfer_all_from()
    player_inventory.transfer_all_inventory() #transfer all the snow pellets into the crop plot
    inventory.close()

def harvest_stack():
    #should start off at pitch 0 
    pitch_locations = [0,-25,-12,-4,4,-5.5,1,9,17]
    player_state.human.crouch()
    for x in range(len(pitch_locations)-1):
        utils.turn_down(pitch_locations[x]-pitch_locations[x+1])
        if x == 4:
            player_state.human.reset_crouch()
        time.sleep(0.2*settings.lag_offset)
        harvest_crop()
        time.sleep(0.3*settings.lag_offset)

    #reset pitch back to 0
    utils.set_pitch(0)

def harvest_3():
    #looking at the left most stack to begin with 
    harvest_stack()
    utils.turn_right(90)
    harvest_stack()
    utils.turn_right(90)
    harvest_stack()

