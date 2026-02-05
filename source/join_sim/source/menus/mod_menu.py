from source.join_sim.source.utility import windows, recon_utils
from source.join_sim.source.logs import logger as logs

buttons = {
    "mod_join_x":700,"mod_join_y":1250
}

def get_pixel_loc( location):
    if windows.screen.screen_resolution == 1080:
        return round(buttons.get(location) * 0.75)
    return buttons.get(location)

def is_open():
    return recon_utils.check_template_no_bounds("req_mods",0.7)

def mod_menu_join():
    if is_open():
        logs.logger.debug("mod menu click")
        windows.click(get_pixel_loc("mod_join_x"), get_pixel_loc("mod_join_y"))
        recon_utils.window_still_open_no_bounds("req_mods",0.7,1)