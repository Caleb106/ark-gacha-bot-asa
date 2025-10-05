import template
import logs.gachalogs as logs
import utils
import windows
import variables
import time
import settings
import bot.config
import ASA.player.player_inventory
import ASA.player.player_state
from compat_input import pyautogui  # 3.13-safe input shim
import local_player
import ASA.player.buffs

global render_flag
render_flag = False  # starts false; not rendering yet


def is_open():
    return template.check_template_no_bounds("bed_radical", 0.6)


def enter_tekpod():
    global render_flag
    attempts = 0
    while not render_flag:
        attempts += 1
        if attempts == bot.config.render_attempts:
            logs.logger.warning(
                f"{attempts} attempts; could not get into render bed. Eating implant and respawning to recover."
            )
            ASA.player.player_inventory.implant_eat()
            ASA.player.player_state.check_state()  # should respawn at bed

        time.sleep(0.5 * settings.lag_offset)
        utils.press_key(local_player.get_input_settings("Run"))  # uncrouch
        utils.zero()
        utils.set_yaw(settings.station_yaw)
        utils.turn_down(15)
        time.sleep(0.3 * settings.lag_offset)

        pyautogui.keyDown(chr(utils.keymap_return(local_player.get_input_settings("Use"))))

        if not template.template_await_true(
            template.check_template_no_bounds, 1, "bed_radical", 0.6
        ):
            pyautogui.keyUp(chr(utils.keymap_return(local_player.get_input_settings("Use"))))
            time.sleep(0.5 * settings.lag_offset)
            utils.press_key(local_player.get_input_settings("Run"))
            utils.zero()
            utils.set_yaw(settings.station_yaw)
            utils.turn_down(15)
            time.sleep(0.3 * settings.lag_offset)
            pyautogui.keyDown(chr(utils.keymap_return(local_player.get_input_settings("Use"))))
            time.sleep(0.5 * settings.lag_offset)

        if template.template_await_true(
            template.check_template_no_bounds, 1, "bed_radical", 0.6
        ):
            time.sleep(0.2 * settings.lag_offset)
            windows.move_mouse(
                variables.get_pixel_loc("radical_laydown_x"),
                variables.get_pixel_loc("radical_laydown_y"),
            )
            time.sleep(0.5 * settings.lag_offset)
            pyautogui.keyUp(chr(utils.keymap_return(local_player.get_input_settings("Use"))))
            time.sleep(1)

        # check buff to confirm we are inside the tekpod
        if ASA.player.buffs.check_buffs() == 1:
            logs.logger.critical(
                f"Bot is now in the render pod after {attempts} attempts"
            )
            render_flag = True
            utils.current_pitch = 0  # reset pitch for when leaving the pod
        else:
            ASA.player.player_state.check_state()
            logs.logger.error(
                f"Unable to enter tekpod on attempt {attempts}; retrying"
            )

        if attempts >= bot.config.render_attempts:
            logs.logger.error(
                f"Unable to enter tekpod after {attempts} attempts; pausing to avoid loops"
            )
            break


def leave_tekpod():
    global render_flag
    ASA.player.player_state.reset_state()
    time.sleep(0.2 * settings.lag_offset)
    utils.press_key(local_player.get_input_settings("Use"))
    time.sleep(1 * settings.lag_offset)

    # if still in pod, try once more
    if ASA.player.buffs.check_buffs() == 1:
        time.sleep(3)
        logs.logger.warning("Did not leave tekpod on first try; retrying now")
        utils.press_key(local_player.get_input_settings("Use"))
        time.sleep(1 * settings.lag_offset)

    utils.current_yaw = settings.render_pushout
    utils.set_yaw(settings.station_yaw)
    time.sleep(0.5 * settings.lag_offset)
    render_flag = False
