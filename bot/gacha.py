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


def drop_off_nocrop(metadata): # change reberry time or you will run out of crops
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

    if ASA.strucutres.inventory.is_open():
        ASA.strucutres.inventory.transfer_all_from()
        ASA.strucutres.inventory.drop_all_obj()
        ASA.player.player_inventory.transfer_all_inventory()
    ASA.strucutres.inventory.close()
    time.sleep(0.2*settings.lag_offset)
    utils.turn_left(40*turn_constant)


def iguanadon_gacha(metadata):
    direction = metadata.side
    if direction == "right":
        turn_constant = 1
    else:
        turn_constant = -1

    utils.turn_right(180) # turning backwards to face iguaadon
    time.sleep(0.2*settings.lag_offset) # timer to prevent accidentle openings of the gachas 

    # put in mejos in current inventory into iguanadon should be 145 slots
    ASA.strucutres.inventory.open()
    if ASA.strucutres.inventory.is_open():
        time.sleep(0.1*settings.lag_offset)
        ASA.strucutres.inventory.drop_all_obj() # making sure iguanadon is empty (AT THE START ONLY - gets rid of previous seeds)
        ASA.strucutres.inventory.transfer_all_from() # doing this should prevent the seed not appearing first try
        ASA.player.player_inventory.search_in_inventory(settings.berry_type) #iguanadon has 1450 weight for the 145 stacks of berries
        ASA.player.player_inventory.transfer_all_inventory()
        #check if mejoberries are in SECOND(which is the third slot) slot therfore we dont need to take out from our shoulder mount as we have more than 100 
        # as after transfer all it resets any searched terms
    ASA.strucutres.inventory.close()
    # exit iguanadon press e to seed
    if not template.template_await_true(template.check_template,1,"seed_inv",0.7):
        logs.logger.debug("iguanadon seeding hasnt been spotted re adding berries")
        ASA.strucutres.inventory.open()
        ASA.strucutres.inventory.search_in_object(settings.berry_type)
        ASA.strucutres.inventory.transfer_all_from()
        ASA.player.player_inventory.search_in_inventory(settings.berry_type)
        ASA.player.player_inventory.transfer_all_inventory()
        ASA.strucutres.inventory.close()
        template.template_await_true(template.check_template,1,"seed_inv",0.7)
    utils.press_key("Use")
    #seeding takes about a second till we can reaccess ∴ we either get more mejos from our shoulder mount if we need to during this time 
    # if mejoberries not in the second slot (ie we have less than 100 mejos)
        # press r to get circle menu for shoulder mount
        # press the access inv
        #ASA.dinosaurs.shoulder_mounts.access_inv
        # take out 1 stack of berry from shoulder press T once 
        # check the bottom left to see the + and - to see if the berries come out IDK Lag or smth might mess it up
        # exit out of the shoulder mount  now we have 145 slots of berrries again in theory after we take out from the iguanadon 
    # take out the seeds and add the 1 stack of mejos -> descending has mejos before the seeds of mejos ∴ are at the top of the search list 
    # we are going to be using 290 slots in the gacha - 10 extra slots allows room for pellets to be picked up by gacha
    # you have 145 seeds alr in our inv + 1 stack of berries 
    # assuming pyro is full therefore we cant use it 
    # assuming gacha is black boxed cant use that and we cant deposit all
    # turn around drop all on gacha while we have 145 seeds and depo seeds ( max drop all is about 230 slots in OUR inv)
    # we put in the seeds in our inv into the gacha 
    # turn back to iguanadon 
    # seed the iguanadon again adding the +1 berries we have and getting more from our shoulder mount if nessasary during seed animation
    # take all we have 145 seeds 145 berrys at this point
    # now turn back to the gacha we have 290 slots 
    # search for seeds
    # transfer all from char we should now just have the 144 slots of seeds from the iguanadon
    # exit gacha
    # tp away 
    #  
    #
    #