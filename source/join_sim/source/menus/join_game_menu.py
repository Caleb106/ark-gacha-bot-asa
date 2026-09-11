from source.join_sim.source.utility import windows, recon_utils
from logger.logger import logger
import time
buttons = {
    "join_game_x":919,"join_game_y":710,
    "back_x":1280,"back_y":1280
}

def get_pixel_loc(location):
    if windows.screen.screen_resolution == 1080:
        return round(buttons.get(location) * 0.75)
    return buttons.get(location)
    
def is_open():
    return recon_utils.check_template_no_bounds("join_game",0.55)

def click_join_game():
    windows.move_mouse(100,100)
    time.sleep(0.05)
    if is_open():
        logger.debug("click join game")
        location = recon_utils.template_find("join_game")
        windows.click(location[0],location[1])
        recon_utils.window_still_open_no_bounds("join_game",0.55,1)

def exit_menu():
    if is_open():
        windows.click(get_pixel_loc("back_x"),get_pixel_loc("back_y"))
        recon_utils.window_still_open_no_bounds("join_game",0.55,1)

