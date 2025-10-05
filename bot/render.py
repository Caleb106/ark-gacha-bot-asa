import template
import logs.gachalogs as logs
import utils
import windows
import variables
import time
import settings
import bot.config
import ASA.player.player_inventory as player_inventory
import ASA.player.player_state as player_state
from compat_input import pyautogui
import local_player
import ASA.player.buffs as buffs

# Render state flag
render_flag = False  # we start outside the pod


def is_open() -> bool:
    """Return True if the bed radial is visible."""
    return template.check_template_no_bounds("bed_radical", 0.6)


def enter_tekpod():
    """
    Enter the tekpod from the render bed area.
    Uses 'Use' key, waits for bed radial, clicks laydown, and verifies via buff.
    """
    global render_flag
    attempts = 0
    max_attempts = int(getattr(bot.config, "render_attempts", 3))

    while not render_flag and attempts < max_attempts:
        attempts += 1

        time.sleep(0.5 * settings.lag_offset)
        # normalize first so movement is deterministic
        utils.zero()
        utils.set_yaw(settings.station_yaw)
        time.sleep(0.2 * settings.lag_offset)

        # ensure not crouched
        utils.press_key(local_player.get_input_settings("Run"))
        time.sleep(0.1 * settings.lag_offset)

        # hold use to bring up bed radial
        use_key = local_player.get_input_settings("Use")
        pyautogui.keyDown(chr(utils.keymap_return(use_key)))

        # wait for radial to appear
        if not template.template_await_true(template.check_template_no_bounds, 1.5, "bed_radical", 0.6):
            # release and try again
            pyautogui.keyUp(chr(utils.keymap_return(use_key)))
            time.sleep(0.5 * settings.lag_offset)
            continue

        # move mouse to lie down
        time.sleep(0.2 * settings.lag_offset)
        windows.move_mouse(
            variables.get_pixel_loc("radical_laydown_x"),
            variables.get_pixel_loc("radical_laydown_y"),
        )
        time.sleep(0.2 * settings.lag_offset)
        pyautogui.keyUp(chr(utils.keymap_return(use_key)))
        time.sleep(1.0 * settings.lag_offset)

        # verify tekpod buff
        if buffs.check_buffs() == 1:
            logs.logger.critical(f"Bot is now in the render pod after {attempts} attempt(s)")
            render_flag = True
            utils.current_pitch = 0
            return
        else:
            player_state.check_state()
            logs.logger.error(f"Unable to enter tekpod on attempt {attempts}; retrying")

    if not render_flag:
        logs.logger.error(f"Unable to enter tekpod after {attempts} attempts; giving up this cycle")


def leave_tekpod():
    """
    Leave the tekpod safely and normalize view.
    """
    global render_flag
    player_state.reset_state()
    time.sleep(0.2 * settings.lag_offset)
    utils.press_key(local_player.get_input_settings("Use"))
    time.sleep(1.0 * settings.lag_offset)

    # if still in pod, retry once
    if buffs.check_buffs() == 1:
        time.sleep(3.0)
        logs.logger.warning("Did not leave tekpod on first try; retrying now")
        utils.press_key(local_player.get_input_settings("Use"))
        time.sleep(1.0 * settings.lag_offset)

    # normalize direction after leaving
    try:
        utils.zero()
        utils.set_yaw(settings.station_yaw)
        time.sleep(0.1 * settings.lag_offset)
    except Exception:
        pass

    # small pushout calibration kept from previous behavior
    try:
        utils.current_yaw = settings.render_pushout
    except Exception:
        pass

    time.sleep(0.4 * settings.lag_offset)
    render_flag = False
