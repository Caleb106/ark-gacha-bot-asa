import time 
import settings
from source.utility import utils ,template , windows ,variables ,screen ,local_player
from source.logs import gachalogs as logs
from source.ASA.strucutres import teleporter , inventory
from source.ASA.stations import custom_stations
from source.ASA.player import player_inventory , player_state , buffs
import source.gacha_bot.config 
import pyautogui

global render_flag
render_flag = False #starts as false as obviously we are not rendering anything

def is_open():
    return template.check_template_no_bounds("bed_radical",0.6)

def enter_tekpod():
    global render_flag
    attempts = 0 
    while not render_flag:
        attempts += 1
        if attempts == source.gacha_bot.config.render_attempts:
            logs.logger.warning(f"{attempts} attempts however bot could not get into the render bed we are dieing and respawning to try and fix this")
            player_inventory.implant_eat()
            player_state.check_state() # this should respawn our char in the bed
        time.sleep(0.5*settings.lag_offset)    
        utils.press_key(local_player.get_input_settings("Run")) #uncrouching char just in case
        utils.zero()
        utils.set_yaw(settings.station_yaw)
        utils.turn_down(15)
        time.sleep(0.3*settings.lag_offset)
        pyautogui.keyDown(chr(utils.keymap_return(local_player.get_input_settings("Use"))))
        
        if not template.template_await_true(template.check_template_no_bounds,1,"bed_radical",0.6):
            pyautogui.keyUp(chr(utils.keymap_return(local_player.get_input_settings("Use"))))
            time.sleep(0.5*settings.lag_offset)    
            utils.press_key(local_player.get_input_settings("Run")) 
            utils.zero()
            utils.set_yaw(settings.station_yaw)
            utils.turn_down(15)
            time.sleep(0.3*settings.lag_offset)
            pyautogui.keyDown(chr(utils.keymap_return(local_player.get_input_settings("Use"))))
            time.sleep(0.5*settings.lag_offset)

        if template.template_await_true(template.check_template_no_bounds,1,"bed_radical",0.6):
            time.sleep(0.2*settings.lag_offset)
            windows.move_mouse(variables.get_pixel_loc("radical_laydown_x"), variables.get_pixel_loc("radical_laydown_y"))
            time.sleep(0.5*settings.lag_offset)
            pyautogui.keyUp(chr(utils.keymap_return(local_player.get_input_settings("Use"))))
            time.sleep(1)
        buff = buffs.check_buffs()
        if buff.check_buffs() == 1:
            logs.logger.critical(f"bot is now in the render pod rendering the station after {attempts} attempts")
            render_flag = True
            utils.current_pitch = 0 # resetting the pitch for when char leaves the tekpod
        else:
            player_state.check_state()
            logs.logger.error(f"we were unable to get into the tekpod on the {attempts} attempt retrying now")

        if attempts >= source.gacha_bot.config.render_attempts:
            logs.logger.error(f"we were unable to get into the tekpod after {attempts} attempts pausing execution to avoid unbreakable loops")
            break

def leave_tekpod():
    global render_flag
    player_state.reset_state() 
    time.sleep(0.2*settings.lag_offset)
    utils.press_key(local_player.get_input_settings("Use"))
    time.sleep(1*settings.lag_offset)
    buff = buffs.check_buffs()
    if buff.check_buffs == 1:
        time.sleep(3)
        logs.logger.warning("bot didnt leave the tekpod first try we are retrying now")
        utils.press_key(local_player.get_input_settings("Use"))
        time.sleep(1*settings.lag_offset)
    utils.current_yaw = settings.render_pushout
    utils.set_yaw(settings.station_yaw)
    time.sleep(0.5*settings.lag_offset)
    render_flag = False

def fast_travel_to_render():
    if render_flag:
        #we need to leave tekpod and look at it 
        leave_tekpod()
        return
    if player_state.human.on_tp:
        #we need to tp to render tp
        teleporter.teleport_not_default(settings.bed_spawn)
        

