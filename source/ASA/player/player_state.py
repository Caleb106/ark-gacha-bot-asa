from source.ASA.inventories import inventory
from source.utility import utils ,template , windows ,variables ,screen ,local_player
from source.logs import gachalogs as logs
import time 
import settings
from source.ASA.player import tribelog , buffs , player_inventory
from source.ASA.strucutres import bed , teleporter
import source.ASA.config 
import source.gacha_bot.render
from source.join_sim.source import main

global crouched
global human
crouched = False

class charecter():
    def __init__(self):
        self.inventory = inventory.inventory()
        self.crouched = False
        self.weight = 0
        self.health = 0
        self.water = 0
        self.food = 0 

    def crouch(self):
        if not self.crouched:
            utils.press_key("Crouch")
            self.crouched = True
            time.sleep(0.1) #takes time to crouch and view angles to change

    def reset_crouch(self):
        if self.crouched:
            for x in range(3): # just ensuring that we are standing up properly 
                utils.press_key("Run")   
            time.sleep(0.1) # takes time to uncrouch ensuring that it has properly    
            self.crouched = False

human = charecter()

def check_disconnected():
    
    if main.is_menu() or main.is_crashed():
        logs.logger.critical("we are disconnected from the server")
        windows.hwnd = main.main_loop(str(settings.server_number))
        tribelog.close()
        logs.logger.critical("joined back into the server waiting 30 seconds to render everything ")
        time.sleep(60)# letting everything load back in
        utils.set_yaw(settings.station_yaw)
        

def reset_state():
    logs.logger.debug(f"resetting char state now")
    player_inventory.close()
    teleporter.close()
    tribelog.close()
    if bed.is_open():
       bed.spawn_in(settings.bed_spawn) #guessing the char died will respawn it if the char hasnt died and it just in a tekpod screen it will just exit when it cant find its target bed
    utils.press_key("Run") # makes the char stand up doing this at the end ensures we arent in any inventory

def check_state(): # mainliy checked at the start of every task to check for food / water on the char
    check_disconnected()
    reset_state()
    buff = buffs.check_buffs()
    type = buff.check_buffs()
    if type == 1 or source.gacha_bot.render.render_flag: #type 1 is when char is in the tekpod
        logs.logger.debug(f"tekpod buff found on screen leaving tekpod now reason | type : {type} render flag : {source.gacha_bot.render.render_flag}")
        source.gacha_bot.render.leave_tekpod()
    elif type == 2 or type == 3:
        logs.logger.warning(f"tping back to render bed to replenish food and water | 2= water 3= food | reason:{type}")
        teleporter.teleport_not_default(settings.bed_spawn)
        source.gacha_bot.render.enter_tekpod()
        time.sleep(30) # assuming 30 seconds should replenish the player back to 100/100
        source.gacha_bot.render.leave_tekpod()
        time.sleep(1)

