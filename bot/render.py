import time
import settings
import template
import variables
import utils
import windows
import logs.gachalogs as logs

import ASA.player.player_state as player_state
import ASA.player.player_inventory as player_inventory
import ASA.player.buffs as buffs
import local_player

from compat_input import pyautogui

render_flag = False

def is_open() -> bool:
    return template.check_template_no_bounds("bed_radical", 0.6)

def _hold_use_for_radial(max_wait: float = 1.0) -> bool:
    use_vk = utils.keymap_return(local_player.get_input_settings("Use"))
    pyautogui.keyDown(chr(use_vk))
    ok = template.template_await_true(template.check_template_no_bounds, max_wait, "bed_radical", 0.6)
    pyautogui.keyUp(chr(use_vk))
    return ok

def enter_tekpod():
    from bot import config
    global render_flag
    tries = 0
    max_tries = int(getattr(config, "render_attempts", 3))

    while not render_flag and tries < max_tries:
        tries += 1
        utils.press_key(local_player.get_input_settings("Run"))
        time.sleep(0.15 * settings.lag_offset)
        utils.zero()
        utils.set_yaw(settings.station_yaw)
        utils.turn_down(15)
        time.sleep(0.30 * settings.lag_offset)

        if not _hold_use_for_radial(1.0):
            time.sleep(0.50 * settings.lag_offset)
            utils.press_key(local_player.get_input_settings("Run"))
            utils.zero()
            utils.set_yaw(settings.station_yaw)
            utils.turn_down(15)
            time.sleep(0.30 * settings.lag_offset)
            _hold_use_for_radial(0.8)

        if template.template_await_true(template.check_template_no_bounds, 1.0, "bed_radical", 0.6):
            time.sleep(0.20 * settings.lag_offset)
            windows.move_mouse(
                variables.get_pixel_loc("radical_laydown_x"),
                variables.get_pixel_loc("radical_laydown_y"),
            )
            time.sleep(0.50 * settings.lag_offset)
            try:
                pyautogui.keyUp(chr(utils.keymap_return(local_player.get_input_settings("Use"))))
            except Exception:
                pass
            time.sleep(1.00)

        if buffs.check_buffs() == 1:
            logs.logger.critical(f"in tekpod after {tries} attempt(s)")
            render_flag = True
            utils.current_pitch = 0
            return
        else:
            # only a light reset; do NOT call check_state() here
            player_state.reset_state()
            logs.logger.error(f"enter_tekpod attempt {tries} failed; retrying")

    if not render_flag and tries >= max_tries:
        logs.logger.warning("bed entry failed; using implant to respawn then retry later")
        player_inventory.implant_eat()
        player_state.reset_state()

def leave_tekpod():
    """
    Legacy choreography: pushout -> normalize to station_yaw -> short pause -> look down.
    No check_state() call here to avoid bouncing back to bed.
    """
    global render_flag
    player_state.reset_state()
    time.sleep(0.20 * settings.lag_offset)

    # stand up
    utils.press_key(local_player.get_input_settings("Use"))
    time.sleep(1.00 * settings.lag_offset)

    if buffs.check_buffs() == 1:
        time.sleep(0.60)
        logs.logger.warning("did not leave tekpod on first try; retrying")
        utils.press_key(local_player.get_input_settings("Use"))
        time.sleep(1.00 * settings.lag_offset)

    # set pushout then normalize yaw
    try:
        utils.current_yaw = settings.render_pushout
    except Exception:
        pass
    utils.zero()
    utils.set_yaw(settings.station_yaw)
    time.sleep(0.50 * settings.lag_offset)

    # do NOT call player_state.check_state() here — it can TP back to bed
    utils.turn_down(80)
    time.sleep(0.30 * settings.lag_offset)

    render_flag = False
