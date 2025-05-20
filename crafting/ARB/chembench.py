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
import screen 
def craft_gunpowder():
    # open chem bench
    ASA.strucutres.inventory.open()
    if not template.template_await_true(template.check_template,1,"chem_bench",0.7):
        ASA.strucutres.inventory.close()
        utils.zero()
        #utils.set_yaw(metadata.yaw)
    # search for gun
    if template.check_template("chem_bench",0.7):
        ASA.strucutres.inventory.search_in_object("gun")
        time.sleep(0.3*settings.lag_offset)
        x = ASA.strucutres.inventory.inv_slots["x"]
        y = ASA.strucutres.inventory.inv_slots["y"]
        if screen.screen_resolution == 1080:
            windows.move_mouse(x * 0.75,y * 0.75)
            windows.click(x * 0.75,y * 0.75)
        else:
            windows.move_mouse(x,y)
            windows.click(x,y)
        
        for count in range(15):
            utils.press_key("a")
    # press hover first slot
    # hold A 

    ...
def craft_sparkpowder():
    ASA.strucutres.inventory.open()
    if not template.template_await_true(template.check_template,1,"chem_bench",0.7):
        ASA.strucutres.inventory.close()
        utils.zero()
        #utils.set_yaw(metadata.yaw)
    # search for gun
    if template.check_template("chem_bench",0.7):
        ASA.strucutres.inventory.search_in_object("spark")
        time.sleep(0.3*settings.lag_offset)
        x = ASA.strucutres.inventory.inv_slots["x"]
        y = ASA.strucutres.inventory.inv_slots["y"]
        if screen.screen_resolution == 1080:
            windows.move_mouse(x * 0.75,y * 0.75)
            windows.click(x * 0.75,y * 0.75)
        else:
            windows.move_mouse(x,y)
            windows.click(x,y)
        
        for count in range(15):
            utils.press_key("a")
    # open chem bench
    # search for gun
    # press hover first slot
    # hold A 
    ...