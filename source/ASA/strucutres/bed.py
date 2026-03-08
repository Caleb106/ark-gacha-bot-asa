from source.gacha_bot import render
from source.utility import utils ,template , windows ,variables ,screen ,local_player
from source.logs import gachalogs as logs
from source.ASA.player import player_inventory , tribelog , player_state
import time 
import settings
import source.ASA.config 

def is_open():
    return template.check_template("beds_title",0.7) #bed title is found in both death and fast travel screens
    
def is_dead():
    return template.check_template("death_regions",0.7)
    
def close():
    attempts = 0
    while is_open():
        attempts += 1
        logs.logger.debug(f"trying to close the bed {attempts} / {source.ASA.config.teleporter_close_attempts}")
        windows.click(variables.get_pixel_loc("back_button_tp_x"),variables.get_pixel_loc("back_button_tp_y"))
        time.sleep(0.2*settings.lag_offset)

        if attempts >= source.ASA.config.teleporter_close_attempts:
            logs.logger.error(f"unable to close the bed after {source.ASA.config.teleporter_close_attempts} attempts")
            break
            

def spawn_in(bed_name:str):
    if not is_open():
        player_inventory.implant_eat()
        
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

        tribelog.open()
        tribelog.close()

def fast_travel(bed_name:str):
    
    if player_state.human.on_bed == False:
        #need to go to render bed if on tp 
        if player_state.human.on_tp:
            logs.logger.debug(f"char is on a teleporter going to render bed to fast travel")
            render.fast_travel_to_render()
            time.sleep(0.2*settings.lag_offset)
            utils.turn_down(15)
    else:
        utils.turn_down(80)
    time.sleep(0.2*settings.lag_offset)
    utils.press_key(local_player.get_input_settings("Use"))
    print(bed_name)    
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

        player_state.human.is_on_bed()
        time.sleep(2) #spawn in animation is shorter than spawning in 

        tribelog.open()
        tribelog.close()    