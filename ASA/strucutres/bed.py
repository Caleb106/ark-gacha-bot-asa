import template
import logs.gachalogs as logs
import utils
import windows
import variables
import time 
import settings
import ASA.config 
import ASA.stations.custom_stations
import ASA.player.tribelog
import ASA.player.player_inventory

def is_open():
    return template.check_template("beds_title",0.7) #bed title is found in both death and fast travel screens
    
def is_dead():
    return template.check_template("death_regions",0.7)
    
def close():
    attempts = 0
    while is_open():
        attempts += 1
        logs.logger.debug(f"trying to close the bed {attempts} / {ASA.config.teleporter_close_attempts}")
        windows.click(variables.get_pixel_loc("back_button_tp_x"),variables.get_pixel_loc("back_button_tp_y"))
        time.sleep(0.2*settings.lag_offset)

        if attempts >= ASA.config.teleporter_close_attempts:
            logs.logger.error(f"unable to close the bed after {ASA.config.teleporter_close_attempts} attempts")
            break
            

def spawn_in(bed_name:str):
    if not is_open():
        ASA.player.player_inventory.implant_eat()
        
    if is_open():
        state = "death screen" if is_dead() else "fast travel screen"
        logs.logger.debug(f"char is in the {state}")
        search_bar_x = variables.get_pixel_loc("search_bar_bed_dead_x" if is_dead() else "search_bar_bed_alive_x")
        windows.click(search_bar_x, variables.get_pixel_loc("search_bar_bed_y")) #search bar y axis is the same for both death/alive 
        
        utils.ctrl_a() #CTRL A removes all previous data in the search bar 
        utils.write(bed_name)

        time.sleep(0.2*settings.lag_offset)
        windows.click(variables.get_pixel_loc("first_bed_slot_x"),variables.get_pixel_loc("first_bed_slot_y"))

        if not template.template_await_true(template.check_teleporter_orange,3): # waiting for the bed to appear as ready to spawn in
            logs.logger.error(f"the bed char tried spawning on is not in the ready state or cant be found exiting out of bed screen now")
            close()
            return    # no need to continue with this therefore we should just leave func     
               
        windows.click(variables.get_pixel_loc("spawn_button_x"),variables.get_pixel_loc("spawn_button_y"))

        if template.template_await_true(template.white_flash,2):
            logs.logger.debug(f"white flash detected waiting for up too 5 seconds")
            template.template_await_false(template.white_flash,5)

        time.sleep(10) # animation spawn in is about 7 seconds 

        ASA.player.tribelog.open()
        ASA.player.tribelog.close()
