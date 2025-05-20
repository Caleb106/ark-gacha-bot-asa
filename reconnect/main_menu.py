from reconnect import recon_utils
import time 
import windows
import screen
import pyautogui


buttons = {
    "accept_x": 1255, "accept_y": 980,
    "join_last_session_x": 1250 , "join_last_session_y":1260,
    "start_x":1270 , "start_y": 1150
}


def get_pixel_loc( location):
    if screen.screen_resolution == 1080:
        return round(buttons.get(location) * 0.75)
    return buttons.get(location)

def is_open(): # pretty much always true while in this screen 
    return recon_utils.check_template_no_bounds("join_last_session",0.7)

def disconnect():
    return recon_utils.check_template_no_bounds("connection_timeout",0.7)
    
def join_last():
    if not is_open():
        return
    if disconnect():
        windows.click(get_pixel_loc("accept_x"),get_pixel_loc("accept_y"))
        recon_utils.window_still_open_no_bounds("accept",0.7,1)

    windows.click(get_pixel_loc("join_last_session_x"),get_pixel_loc("join_last_session_y"))
    recon_utils.window_still_open_no_bounds("join_last_session",0.7,1)

def enter_menu():
    if not is_open():
        return
    if disconnect():
        windows.click(get_pixel_loc("accept_x"),get_pixel_loc("accept_y"))
        recon_utils.window_still_open_no_bounds("accept",0.7,1)

    windows.click(get_pixel_loc("accept_x"),get_pixel_loc("accept_y")) # pressing in case something is on screen
    windows.click(get_pixel_loc("start_x"),get_pixel_loc("start_y"))
    recon_utils.window_still_open_no_bounds("join_last_session",0.7,1)
