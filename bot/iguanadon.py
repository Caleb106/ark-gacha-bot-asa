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

def berry_collection():
    time.sleep(0.5)
    ASA.strucutres.inventory.open()
    if ASA.strucutres.inventory.is_open():
        ASA.strucutres.inventory.transfer_all_from()
        ASA.strucutres.inventory.close()
    time.sleep(0.5)

def berry_station():
    berry_collection()
    utils.turn_down(50)
    berry_collection()
    utils.turn_up(50)

def seed(type):
    if ASA.strucutres.inventory.is_open():
        time.sleep(0.1*settings.lag_offset)
        ASA.strucutres.inventory.transfer_all_from() # doing this should prevent the seed not appearing first try
        ASA.player.player_inventory.search_in_inventory(settings.berry_type) #iguanadon has 1450 weight for the 145 stacks of berries
        ASA.player.player_inventory.transfer_all_inventory()
        if type == 2:
            time.sleep(0.2*settings.lag_offset)
            ASA.player.player_inventory.drop_all_inv() #doing this second time round to drop everything else that is not needed by the bot
        time.sleep(0.1*settings.lag_offset)
        ASA.player.player_inventory.close()
        time.sleep(0.1*settings.lag_offset)

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
    time.sleep(0.6*settings.lag_offset)
    ASA.strucutres.inventory.open()
    if ASA.strucutres.inventory.is_open():
        ASA.strucutres.inventory.search_in_object("seed")
        ASA.strucutres.inventory.transfer_all_from()
        time.sleep(0.3*settings.lag_offset)
        ASA.strucutres.inventory.close()
    time.sleep(0.2*settings.lag_offset)

def iguanadon_open(metadata):
    attempt = 0
    time.sleep(0.2*settings.lag_offset)
    ASA.strucutres.inventory.open()
    while not ASA.strucutres.inventory.is_open():
        attempt += 1
        logs.logger.debug(f"the iguanadon at {metadata.name} could not be accessed retrying {attempt} / {bot.config.iguanadon_attempts}")
        utils.zero()
        utils.set_yaw(metadata.yaw)
        time.sleep(0.2*settings.lag_offset)
        ASA.strucutres.inventory.open()
        if attempt >= bot.config.iguanadon_attempts:
            logs.logger.error(f"the iguanadon at {metadata.name} could not be accesssed after {attempt} attempts")
            break
    
def drop_seeds():
    utils.press_key("Crouch")
    ASA.player.player_inventory.open()
    if ASA.player.player_inventory.is_open():
        ASA.player.player_inventory.search_in_inventory("seed")
        time.sleep(0.2*settings.lag_offset)
        ASA.player.player_inventory.drop_all_inv()
        ASA.player.player_inventory.close()
    for x in range(3):
        utils.press_key("Run")

def pickup_seeds():
    time.sleep(0.2*settings.lag_offset)
    utils.press_key("crouch")
    utils.turn_down(80)
    time.sleep(0.2*settings.lag_offset)
    ASA.strucutres.inventory.open()
    if ASA.strucutres.inventory.is_open():
        ASA.strucutres.inventory.transfer_all_from() #this should also cause us to get out of bag
        if template.template_await_false(template.check_template,1,"inventory",0.7):
            logs.logger.warning(f"the bag we dropped on the floor for 230 seeds couldnt be fully picked up popcorning now")
            attempts = 0
            while template.check_template("inventory",0.7):
                attempts += 1
                ASA.strucutres.inventory.popcorn_top_row()
                if  attempts >= 60 : # 60 * 6  = 360 so whole inv should be popcorned with this value 
                    logs.logger.error("bot got stuck in the popcorning the bag inventory mostlikly broken")
                    break

            # popcorn the bag lateron ( will be due to inv being capped )
    for x in range(3):
        utils.press_key("Run")

def iguanadon(metadata):
    iguanadon_open(metadata)
    if settings.seeds_230:  
        seed(1)
        drop_seeds()
        iguanadon_open(metadata)
        seed(2)
        pickup_seeds()
    else:
        seed(2)