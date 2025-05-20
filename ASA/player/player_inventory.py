import template
import logs.gachalogs as logs
import utils
import windows
import variables
import time 
import settings
import ASA.config 
import ASA.player.player_state

def is_open():
    return template.check_template("inventory",0.7)
    
def open(): 
    attempts = 0 
    while not is_open():
        attempts += 1
        logs.logger.debug(f"trying to open player inventory {attempts} / {ASA.config.inventory_open_attempts}")
        utils.press_key("ShowMyInventory")
        if template.template_await_true(template.check_template,2,"inventory",0.7):
            logs.logger.debug("inventory opened")
            break
        
        #check state of the char before redoing
        if attempts >= ASA.config.inventory_open_attempts:
            logs.logger.error(f"unable to open up the players inventory")
            break
    time.sleep(0.3*settings.lag_offset)

def close():
    attempts = 0
    while is_open():
        attempts += 1
        logs.logger.debug(f"trying to close objects inventory {attempts} / {ASA.config.inventory_close_attempts}")
        windows.click(variables.get_pixel_loc("close_inv_x"), variables.get_pixel_loc("close_inv_y"))
        template.template_await_false(template.check_template,2,"inventory",0.7)
            

        if attempts >= ASA.config.inventory_close_attempts:
            logs.logger.error(f"unable to close the objects inventory after {attempts} attempts") 
            #check state of the char the reason we can do it now is that the latter should spam click close inv 
            break
    time.sleep(0.3*settings.lag_offset)

#these functions assume that the inventory is already open
def search_in_inventory(item:str):
    logs.logger.debug(f"searching in inventory for {item}")
    time.sleep(0.2*settings.lag_offset)
    windows.click(variables.get_pixel_loc("search_inventory_x"),variables.get_pixel_loc("transfer_all_y")) 
    utils.ctrl_a()  
    time.sleep(0.2*settings.lag_offset)
    utils.write(item)
    time.sleep(0.1*settings.lag_offset)

def drop_all_inv():  
    logs.logger.debug(f"dropping all items from our inventory ")
    time.sleep(0.2*settings.lag_offset)
    windows.click(variables.get_pixel_loc("drop_all_x"),variables.get_pixel_loc("transfer_all_y")) 
    time.sleep(0.1*settings.lag_offset)

def transfer_all_inventory(): 
    logs.logger.debug(f"transfering all from our inventory into strucutre")
    time.sleep(0.2*settings.lag_offset)
    windows.click(variables.get_pixel_loc("transfer_all_inventory_x"),variables.get_pixel_loc("transfer_all_y"))
    time.sleep(0.1*settings.lag_offset)



def implant_eat():
    attempts = 0
    while not template.check_template("death_regions",0.7):
        attempts += 1
        logs.logger.debug(f"trying to eat player implant {attempts} / {ASA.config.suicide_attempts}")
        utils.press_key("ShowMyInventory")
        open() 
        close() 
        for x in range(30):
            utils.press_key("s") # moving backwards so we dont die on tps and create bags
        open()
        windows.move_mouse(variables.get_pixel_loc("implant_eat_x"),variables.get_pixel_loc("implant_eat_y"))
        windows.click(variables.get_pixel_loc("implant_eat_x"),variables.get_pixel_loc("implant_eat_y"))
        time.sleep(10) # accounting for high ping lag
        utils.press_key("Use")

        if not template.template_await_true(template.check_template,10,"death_regions",0.7):
            #check state of the char before redoing
            ASA.player.player_state.check_state()
            ...
                
        if attempts >= ASA.config.suicide_attempts:
            logs.logger.error(f"unable to eat player implant")
            break
        