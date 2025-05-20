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
    
def drop_off(metadata): #drop off for 150 stacks of seeds
    direction = metadata.side
    if direction == "right":
        turn_constant = 1
    else:
        turn_constant = -1

    utils.turn_right(40*turn_constant)
    time.sleep(0.2*settings.lag_offset)
    ASA.strucutres.inventory.open()

    attempt = 0
    while not ASA.strucutres.inventory.is_open():
        attempt += 1
        logs.logger.debug(f"the {direction} gacha at {metadata.name} could not be accessed retrying {attempt} / {bot.config.gacha_attempts}")
        utils.zero()
        utils.set_yaw(metadata.yaw)
        utils.turn_right(40*turn_constant)
        time.sleep(0.2*settings.lag_offset)
        ASA.strucutres.inventory.open()
        if attempt >= bot.config.gacha_attempts:
            logs.logger.error(f"the {direction} gacha at {metadata.name} could not be accesssed after {attempt} attempts")
            break
    temp = False
    if ASA.strucutres.inventory.is_open():
        ASA.strucutres.inventory.transfer_all_from()
        if template.template_await_true(template.check_template_no_bounds,1,"slot_capped",0.7):
            logs.logger.debug(f"player is overcapped")
            ASA.strucutres.inventory.drop_all_obj() # as our player is overcapped the gacha will also be overcapped + we have seeds in our inventory which is more important than pellets
            ASA.player.player_inventory.search_in_inventory("pell")
            if not template.template_await_true(template.check_template_no_bounds,0.5,"snow_owl_pellet",0.5):
                logs.logger.warning(f"GACHA is full of seeds") #warning the gacha is full of seeds as obviously something is wrong 
                ASA.player.player_inventory.close()
                time.sleep(0.1*settings.lag_offset)
                utils.turn_right(180)
                time.sleep(0.1*settings.lag_offset)
                ASA.player.player_inventory.open()
                ASA.player.player_inventory.search_in_inventory("seed")
                temp = True
            windows.click(variables.get_pixel_loc("inv_slot_start_x")+50,variables.get_pixel_loc("inv_slot_start_y")+70)
            for x in range(8):
                windows.move_mouse(variables.get_pixel_loc("inv_slot_start_x")+50,variables.get_pixel_loc("inv_slot_start_y")+70)
                utils.press_key("DropItem")
                time.sleep(0.3*settings.lag_offset)
            time.sleep(0.1*settings.lag_offset)

    ASA.player.player_inventory.close()
    time.sleep(0.2*settings.lag_offset)
    if temp:
        utils.turn_left(180)
    utils.turn_right(90*turn_constant)
    time.sleep(0.3*settings.lag_offset)
    ASA.strucutres.inventory.open()
    if not template.template_await_true(template.check_template,2,"crop_plot",0.7):
        logs.logger.warning(f"the {direction} crop plot at {metadata.name}tp failed to open retrying now")
        utils.zero()
        utils.set_yaw(metadata.yaw)
        utils.turn_right(130*turn_constant)
        time.sleep(0.2*settings.lag_offset)
        ASA.strucutres.inventory.open()
    if template.check_template("crop_plot",0.7):
        ASA.strucutres.inventory.transfer_all_from()
        time.sleep(0.2*settings.lag_offset)
        ASA.player.player_inventory.transfer_all_inventory() #take out all input all # refreshing owl pelletes
        time.sleep(0.2*settings.lag_offset)
        ASA.strucutres.inventory.close()
    time.sleep(0.2*settings.lag_offset)

    utils.turn_left(90*turn_constant)
    time.sleep(0.2*settings.lag_offset)
    ASA.strucutres.inventory.open()
    if template.check_template("crop_plot",0.7):
        logs.logger.debug("failed to turn away from the crop plot retrying now")
        ASA.strucutres.inventory.close()
        time.sleep(0.5*settings.lag_offset)
        utils.turn_left(90*turn_constant)
        time.sleep(0.3*settings.lag_offset)
        ASA.strucutres.inventory.open()
        time.sleep(0.3*settings.lag_offset)
    if ASA.strucutres.inventory.is_open():
        ASA.player.player_inventory.search_in_inventory("seed")
        time.sleep(0.2*settings.lag_offset)
        ASA.player.player_inventory.transfer_all_inventory()
        time.sleep(0.2*settings.lag_offset)
        if settings.seeds_230:
            ASA.strucutres.inventory.search_in_object("pell")
            time.sleep(0.2*settings.lag_offset)
            ASA.strucutres.inventory.drop_all_obj()
            ASA.player.player_inventory.search_in_inventory("seed")
            time.sleep(0.2*settings.lag_offset)
            ASA.player.player_inventory.transfer_all_inventory()
            time.sleep(0.2*settings.lag_offset)
        ASA.player.player_inventory.search_in_inventory("pell")
        time.sleep(0.2*settings.lag_offset)
        ASA.player.player_inventory.transfer_all_inventory()
        time.sleep(0.2*settings.lag_offset)

    ASA.strucutres.inventory.close()
    time.sleep(0.2*settings.lag_offset)
    utils.turn_left(40*turn_constant)

def collection(metadata):
    direction = metadata.side
    if direction == "right":
        turn_constant = 1
    else:
        turn_constant = -1

    utils.turn_right(40*turn_constant)
    time.sleep(0.2*settings.lag_offset)
    ASA.strucutres.inventory.open()

    attempt = 0
    while not ASA.strucutres.inventory.is_open():
        attempt += 1
        logs.logger.debug(f"the {direction} gacha at {metadata.name} could not be accessed retrying {attempt} / {bot.config.gacha_attempts}")
        utils.zero()
        utils.set_yaw(metadata.side)
        utils.turn_right(40*turn_constant)
        time.sleep(0.2*settings.lag_offset)
        ASA.strucutres.inventory.open()
        if attempt >= bot.config.gacha_attempts:
            logs.logger.error(f"the {direction} gacha at {metadata.name} could not be accesssed after {attempt} attempts")

    if ASA.strucutres.inventory.is_open():
        ASA.strucutres.inventory.transfer_all_from()
    ASA.strucutres.inventory.close()
    utils.turn_left(40*turn_constant)
