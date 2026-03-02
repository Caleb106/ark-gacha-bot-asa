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



'''
forge placed infront of the tp
2 dedis faced behind the tp 180* from the forge
gunpowder ontop
fungal wood on the bottom
165 minuets to do 100 stacks of wood 
2500 weight
'''

class forge():
    def __init__(self,metadata):
        self.items:int = 0 #use ocr to find the amount of slots used by the fungal wood added
        self.last_time_visited = 0
        self.forge_inventory = indi_forge.forge()
        self.metadata = metadata

    def turn_to_dedis(self,resource:str):    
        yaw_of_dedis = utils.normalize_yaw(self.metadata.yaw + 180)
        if resource == "fungal":
            player_state.human.crouch()
            utils.turn_to(yaw_of_dedis,-15)
        else:
            player_state.human.reset_crouch() # just incase
            utils.turn_to(yaw_of_dedis,0) # charcoal dedi 
            player_state.human.reset_crouch()

    def turn_to_forge(self):
        utils.turn_to(self.metadata.yaw,0)

    def input_all_into_forge(self):
        self.turn_to_forge()
        self.forge_inventory.open_forge()
        time.sleep(0.2*settings.lag_offset)
        self.forge_inventory.transfer_all_inventory()
        # maybe ocr slots 

    def put_fungal_into_dedi(self):
        self.turn_to_dedis("fungal")
        time.sleep(0.2*settings.lag_offset)
        utils.press_key("Use")
        time.sleep(0.2*settings.lag_offset)
        self.turn_to_forge()
        time.sleep(0.2*settings.lag_offset)

    def take_fungal_from_dedi(self):
        self.turn_to_dedis("fungal")
        dedi = source.ASA.inventories.structures.structure_inventory()
        dedi.open()
        # open dedi
        # take all from 
        # close

    def put_char_into_dedi(self):
        self.forge_inventory.open_forge()
        time.sleep(0.1*settings.lag_offset)
        self.forge_inventory.search_in_object("char")
        time.sleep(0.1*settings.lag_offset)
        self.forge_inventory.transfer_all_from()
        # ocr slots or check that weight != 0 or check that that second slot is not empty
        self.forge_inventory.close()
        self.turn_to_dedis("charcoal")
        time.sleep(0.2*settings.lag_offset)
        utils.press_key("Use")
        time.sleep(0.2*settings.lag_offset)
        self.turn_to_forge()
        time.sleep(0.2*settings.lag_offset)

