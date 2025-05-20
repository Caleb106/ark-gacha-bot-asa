from reconnect import recon_utils
import time 
import screen
import windows 
import utils
import pyautogui
import template


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
    if screen.screen_resolution == 1080:
        return round(buttons.get(location) * 0.75)
    return buttons.get(location)

def join_server(server_name):

    if not recon_utils.check_template_no_bounds("multiplayer", 0.7):
        utils.press_key("ShowTribeManager")
        return
    time.sleep(0.3)
    windows.click(get_pixel_loc("search_x"), get_pixel_loc("search_y"))
    time.sleep(0.3)
    utils.ctrl_a()
    time.sleep(0.2)
    utils.write(server_name)
    time.sleep(0.3)    
    windows.click(get_pixel_loc("first_server_x"), get_pixel_loc("first_server_y"))
    
    if recon_utils.check_template_no_bounds("join_button", 0.7):
        time.sleep(0.2) 
        windows.click(get_pixel_loc("join_x"), get_pixel_loc("join_y"))
        time.sleep(0.5) # inital wait for the text to appear 
    recon_utils.window_still_open("join_text",0.7,20) # long wait as it can be on the screen for a long time 

    if recon_utils.check_template_no_bounds("mod_join",0.7):
        if recon_utils.template_sleep_no_bounds("req_mods",0.7,10): # idk maybe mods take a while to load
            time.sleep(0.5)
            windows.click(get_pixel_loc("mod_join_x"), get_pixel_loc("mod_join_y")) 
            time.sleep(2)
            recon_utils.window_still_open("join_text",0.7,20)
            time.sleep(2)

    if recon_utils.template_sleep_no_bounds("loading_screen",0.7,0.5):
        recon_utils.window_still_open_no_bounds("loading_screen",0.7,10)
        
        count = 0
        while template.check_template_no_bounds("tribelog_check",0.8) == False and count < 600: # stopping inf loops 
            utils.press_key("ShowTribeManager")
            time.sleep(0.1)
            count += 1
        
        time.sleep(5)
        return 

    if recon_utils.check_template("server_full",0.7):
        windows.click(get_pixel_loc("cancel_x"), get_pixel_loc("cancel_y")) 
        recon_utils.window_still_open_no_bounds("server_full",0.7,2)
        time.sleep(0.5)
        windows.click(get_pixel_loc("back_x"), get_pixel_loc("back_y")) 
        return 
    
    if recon_utils.check_template("red_fail",0.7):
        windows.click(get_pixel_loc("red_okay_x"), get_pixel_loc("red_okay_y")) 
        recon_utils.window_still_open_no_bounds("red_fail",0.7,2)
        time.sleep(0.5)
        windows.click(get_pixel_loc("back_x"), get_pixel_loc("back_y")) 
        return 
    
    time.sleep(0.5)
    #windows.click(get_pixel_loc("refresh_x"), get_pixel_loc("refresh_y")) #if it cant see we refresh the page
    windows.click(get_pixel_loc("back_x"), get_pixel_loc("back_y"))
    if recon_utils.template_sleep_no_bounds("searching",0.7,0.5):
        recon_utils.window_still_open_no_bounds("searching",0.7,10)
        time.sleep(2)

    if recon_utils.check_template_no_bounds("no_session",0.7):
        time.sleep(2)
        windows.click(get_pixel_loc("back_x"), get_pixel_loc("back_y"))
        time.sleep(2)
    
    utils.press_key("ShowTribeManager") # if there is a special event going on the loading screen changes this might fix that