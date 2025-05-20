from reconnect import recon_utils
import time 
import screen
import windows
import pyautogui

    
buttons = {
    "join_game_x":919,"join_game_y":710,
    "back_x":1280,"back_y":1280
}

def get_pixel_loc(location):
    if screen.screen_resolution == 1080:
        return round(buttons.get(location) * 0.75)
    return buttons.get(location)
    
def is_open():
    return recon_utils.check_template_no_bounds("join_game",0.7)

def enter_menu():
    windows.click(get_pixel_loc("join_game_x"),get_pixel_loc("join_game_y"))
    recon_utils.window_still_open_no_bounds("join_game",0.7,1)

def exit_menu():
    windows.click(get_pixel_loc("back_x"),get_pixel_loc("back_y"))
    recon_utils.window_still_open_no_bounds("join_game",0.7,1)

