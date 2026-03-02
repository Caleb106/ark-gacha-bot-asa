from source.join_sim.source.utility import windows, recon_utils , utils
import time
from source.join_sim.source.logs import logger as logs
import pyautogui

buttons = {
    "search_x": 2230, "search_y": 260,
    "first_server_x": 2230, "first_server_y": 438,
    "join_x": 2230, "join_y": 1260,
    "refresh_x": 1240, "refresh_y": 1250,
    "back_x": 230, "back_y": 1180,
    "cancel_x":1426,"cancel_y":970,
    "red_okay_x":1270,"red_okay_y":880,
    "mod_join_x":700,"mod_join_y":1250
}

def get_pixel_loc( location):
    if windows.screen.screen_resolution == 1080:
        return round(buttons.get(location) * 0.75)
    return buttons.get(location)

def is_server_full():
    return recon_utils.check_template_no_bounds("server_full",0.7)

def is_red_fail():
    return recon_utils.check_template_no_bounds("red_fail",0.7)

def no_sessions():
    return recon_utils.check_template_no_bounds("no_session",0.7)
def has_failure():
    if is_server_full():
        logs.logger.debug("server full")
        windows.click(get_pixel_loc("cancel_x"), get_pixel_loc("cancel_y")) 
        recon_utils.window_still_open_no_bounds("server_full",0.7,2)
        time.sleep(1)
        windows.click(get_pixel_loc("back_x"), get_pixel_loc("back_y"))

    if is_red_fail():
        logs.logger.debug("red fail")
        time.sleep(1)
        pyautogui.click(get_pixel_loc("red_okay_x"), get_pixel_loc("red_okay_y")) 
        recon_utils.window_still_open_no_bounds("red_fail",0.7,2)
        time.sleep(1)
        pyautogui.click(get_pixel_loc("back_x"), get_pixel_loc("back_y")) 
    
    if no_sessions():
        logs.logger.debug("no sessions found")
        time.sleep(1)
        pyautogui.click(get_pixel_loc("back_x"), get_pixel_loc("back_y")) 
        time.sleep(1)
