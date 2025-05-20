import ASA.player.player_state
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

def is_open():
    return template.check_template("teleporter_title",0.7)
    
def open():
    """
    player should already be looking down at the teleporter this just opens and WILL try and correct if there are issues 
    """
    attempts = 0 
    while not is_open():
        attempts += 1
        logs.logger.debug(f"trying to open teleporter {attempts} / {ASA.config.teleporter_open_attempts}")
        utils.press_key("Use")
    
        if not template.template_await_true(template.check_template,2,"teleporter_title",0.7):
            logs.logger.warning("teleporter didnt open retrying now")
            ASA.player.player_state.check_state()
            # check state of char which should close out of any windows we are in or rejoin the game
            utils.pitch_zero() # reseting the chars pitch/yaw
            utils.turn_down(80)
            time.sleep(0.2*settings.lag_offset) 
        else:
            logs.logger.debug(f"teleporter opened")   

        if attempts >= ASA.config.teleporter_open_attempts:
            logs.logger.error(f"unable to open up the teleporter after {ASA.config.teleporter_open_attempts} attempts")
            break
            
def close():
    attempts = 0
    while is_open():
        attempts += 1
        logs.logger.debug(f"trying to close the teleporter {attempts} / {ASA.config.teleporter_close_attempts}")
        windows.click(variables.get_pixel_loc("back_button_tp_x"),variables.get_pixel_loc("back_button_tp_y"))
        time.sleep(0.2*settings.lag_offset)

        if attempts >= ASA.config.teleporter_close_attempts:
            logs.logger.error(f"unable to close the teleporter after {ASA.config.teleporter_close_attempts} attempts")
            break
    
def teleport_not_default(arg):

    if isinstance(arg, ASA.stations.custom_stations.station_metadata):
        stationdata = arg
    else:
        stationdata = ASA.stations.custom_stations.get_station_metadata(arg)

    teleporter_name = stationdata.name
    time.sleep(0.3*settings.lag_offset)
    utils.turn_down(80)
    time.sleep(0.3*settings.lag_offset)
    open() 
    time.sleep(0.2*settings.lag_offset) #waiting for teleport_icon to populate on the screen before we check
    if is_open():
        if template.teleport_icon(0.55):
            start = time.time()
            logs.logger.debug(f"teleport icons are not on the teleport screen waiting for up to 10 seconds for them to appear")
            template.template_await_true(template.teleport_icon,10,0.55)
            logs.logger.debug(f"time taken for teleporter icon to appear : {time.time() - start}")

        windows.click(variables.get_pixel_loc("search_bar_bed_alive_x"),variables.get_pixel_loc("search_bar_bed_y")) #im lazy this is the same position as the teleporter search bar
        utils.ctrl_a()
        utils.write(teleporter_name)
        time.sleep(0.2*settings.lag_offset)
        windows.click(variables.get_pixel_loc("first_bed_slot_x"),variables.get_pixel_loc("first_bed_slot_y"))
        time.sleep(0.3*settings.lag_offset) #preventing the orange text from the starting teleport screen messing things up
        if not template.template_await_true(template.check_teleporter_orange,3):
            logs.logger.warning(f"orange pixel for teleporter ready not found likely already on the tp we are just exiting the tp treating it as the tp we should be on")
            close() # closing out as either the TP couldnt be found however we still want to change to the station yaw so we still continue

        else:
            time.sleep(0.2*settings.lag_offset)
            windows.click(variables.get_pixel_loc("first_bed_slot_x"),variables.get_pixel_loc("first_bed_slot_y"))
            time.sleep(0.2*settings.lag_offset)
            windows.click(variables.get_pixel_loc("spawn_button_x"),variables.get_pixel_loc("spawn_button_y"))

            if template.template_await_true(template.white_flash,2):
                logs.logger.debug(f"white flash detected waiting for up too 5 seconds")
                template.template_await_false(template.white_flash,5)
            ASA.player.tribelog.open() 
            ASA.player.tribelog.close()
        time.sleep(0.5*settings.lag_offset)
        if settings.singleplayer: # single player for some reason changes view angles when you tp 
            utils.current_pitch = 0
            utils.turn_down(80)
            time.sleep(0.2)
        utils.turn_up(80)
        time.sleep(0.2) 
        utils.set_yaw(stationdata.yaw)
        
            


                
                              

                
                