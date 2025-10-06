import template
import logs.gachalogs as logs
import utils, windows, variables, time, settings, bot.config
import ASA.player.player_inventory as player_inventory
import ASA.player.player_state as player_state
import ASA.player.buffs as buffs
import local_player
from compat_input import pyautogui

render_flag = False  # we start outside the pod

def is_open() -> bool:
    return template.check_template_no_bounds("bed_radical", 0.6)

def enter_tekpod():
    """
    Original behavior: uncrouch, normalize, hold Use for radial, click Lay Down,
    verify via tekpod buff. Retries up to config.render_attempts, with suicide
    fallback like the legacy flow.
    """
    global render_flag
    attempts = 0
    max_attempts = int(getattr(bot.config, "render_attempts", 3))

    while not render_flag and attempts < max_attempts:
        attempts += 1

        # legacy: if we keep failing, respawn to fix bad states
        if attempts == max_attempts:
            logs.logger.warning(f"{attempts} attempts — forcing respawn to fix bed entry")
            player_inventory.implant_eat()
            player_state.check_state()

        time.sleep(0.5 * settings.lag_offset)
        utils.press_key(local_player.get_input_settings("Run"))  # uncrouch
        utils.zero()
        utils.set_yaw(settings.station_yaw)
        utils.turn_down(15)
        time.sleep(0.3 * settings.lag_offset)

        use_key = local_player.get_input_settings("Use")
        pyautogui.keyDown(chr(utils.keymap_return(use_key)))

        if not template.template_await_true(template.check_template_no_bounds, 1.0, "bed_radical", 0.6):
            pyautogui.keyUp(chr(utils.keymap_return(use_key)))
            time.sleep(0.5 * settings.lag_offset)
            utils.press_key(local_player.get_input_settings("Run"))
            utils.zero()
            utils.set_yaw(settings.station_yaw)
            utils.turn_down(15)
            time.sleep(0.3 * settings.lag_offset)
            pyautogui.keyDown(chr(utils.keymap_return(use_key)))
            time.sleep(0.5 * settings.lag_offset)

        if template.template_await_true(template.check_template_no_bounds, 1.0, "bed_radical", 0.6):
            time.sleep(0.2 * settings.lag_offset)
            windows.move_mouse(
                variables.get_pixel_loc("radical_laydown_x"),
                variables.get_pixel_loc("radical_laydown_y"),
            )
            time.sleep(0.5 * settings.lag_offset)
            pyautogui.keyUp(chr(utils.keymap_return(use_key)))
            time.sleep(1.0)

        if buffs.check_buffs() == 1:
            logs.logger.critical(f"in tekpod after {attempts} attempt(s)")
            render_flag = True
            utils.current_pitch = 0
            return
        else:
            player_state.check_state()
            logs.logger.error(f"enter_tekpod attempt {attempts} failed; retrying")

    if not render_flag:
        logs.logger.error(f"unable to enter tekpod after {attempts} attempts; pausing this cycle")

def leave_tekpod():
    """
    Original behavior: reset state, Use to stand, verify buff cleared,
    normalize zero + station_yaw, apply render_pushout nudge, small settle.
    """
    global render_flag
    player_state.reset_state()
    time.sleep(0.2 * settings.lag_offset)

    utils.press_key(local_player.get_input_settings("Use"))
    time.sleep(1.0 * settings.lag_offset)

    if buffs.check_buffs() == 1:
        time.sleep(3.0)
        logs.logger.warning("did not leave tekpod on first try; retrying")
        utils.press_key(local_player.get_input_settings("Use"))
        time.sleep(1.0 * settings.lag_offset)

    try:
        utils.zero()
        utils.set_yaw(settings.station_yaw)
        time.sleep(0.1 * settings.lag_offset)
    except Exception:
        pass

    try:
        utils.current_yaw = settings.render_pushout
    except Exception:
        pass

    time.sleep(0.5 * settings.lag_offset)
    render_flag = False
