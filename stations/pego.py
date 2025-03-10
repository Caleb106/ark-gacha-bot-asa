import utils
import time
import template
import windows
import ark
import variables
import settings
import discordbot

def pego_pickup(metadata):
    utils.turn_up(15)
    time.sleep(0.5*settings.sleep_constant)
    ark.open_structure()
    if template.template_sleep("inventory",0.7,2) == False:
        discordbot.gachalogs.warning(f"the pego at {metadata.name} didnt open retrying now")
        utils.zero()
        utils.set_yaw(metadata.yaw)
        utils.press_key("Run")
        utils.turn_up(15)
        time.sleep(0.5*settings.sleep_constant)
        ark.open_structure()
    if template.check_template("inventory",0.7):
        ark.drop_all_inv()
        time.sleep(0.2*settings.sleep_constant)
        ark.transfer_all_from()
        time.sleep(0.2*settings.sleep_constant)
        ark.close_inventory() # prevents pego being FLUNG
        
    time.sleep(0.5)
    utils.turn_down(utils.current_pitch)
    time.sleep(0.2)