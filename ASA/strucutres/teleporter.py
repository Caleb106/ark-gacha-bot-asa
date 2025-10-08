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
    return template.check_template("teleporter_title", 0.7)

def open():
    """
    Player should already be looking down at the teleporter.
    Opens TP UI with retries and re-stabilizes camera if needed.
    """
    attempts = 0
    while not is_open():
        attempts += 1
        logs.logger.debug(f"trying to open teleporter {attempts} / {ASA.config.teleporter_open_attempts}")
        utils.press_key("Use")

        # wait up to ~2s for the title to show
        if template.template_await_true(template.check_template, 2, "teleporter_title", 0.7):
            logs.logger.debug("teleporter opened")
            break

        logs.logger.warning("teleporter didnt open retrying now")
        ASA.player.player_state.check_state()
        # re-stabilize view
        utils.pitch_zero()
        utils.turn_down(80)
        time.sleep(0.2 * settings.lag_offset)

        if attempts >= ASA.config.teleporter_open_attempts:
            logs.logger.error(f"unable to open up the teleporter after {ASA.config.teleporter_open_attempts} attempts")
            break

def close():
    attempts = 0
    while is_open():
        attempts += 1
        logs.logger.debug(f"trying to close the teleporter {attempts} / {ASA.config.teleporter_close_attempts}")
        windows.click(variables.get_pixel_loc("back_button_tp_x"), variables.get_pixel_loc("back_button_tp_y"))
        time.sleep(0.2 * settings.lag_offset)
        if attempts >= ASA.config.teleporter_close_attempts:
            logs.logger.error(f"unable to close the teleporter after {ASA.config.teleporter_close_attempts} attempts")
            break

def teleport_not_default(arg):
    """
    Selects the exact teleporter by name. No fallback to any bed.
    Keeps legacy yaw normalization post-TP.
    """
    if isinstance(arg, ASA.stations.custom_stations.station_metadata):
        stationdata = arg
    else:
        stationdata = ASA.stations.custom_stations.get_station_metadata(arg)

    teleporter_name = stationdata.name

    time.sleep(0.3 * settings.lag_offset)
    utils.turn_down(80)
    time.sleep(0.3 * settings.lag_offset)

    open()
    time.sleep(0.2 * settings.lag_offset)  # allow list to populate

    if is_open():
        # Corrected logic: wait for icons only if NOT present yet
        if not template.teleport_icon(0.55):
            start = time.time()
            logs.logger.debug("teleport icons are not on the teleport screen waiting for up to 10 seconds for them to appear")
            template.template_await_true(template.teleport_icon, 10, 0.55)
            logs.logger.debug(f"time taken for teleporter icon to appear : {time.time() - start:.2f}s")

        # focus search, type exact name, click first result
        windows.click(variables.get_pixel_loc("search_bar_bed_alive_x"), variables.get_pixel_loc("search_bar_bed_y"))
        utils.ctrl_a()
        utils.write(teleporter_name)
        time.sleep(0.2 * settings.lag_offset)

        windows.click(variables.get_pixel_loc("first_bed_slot_x"), variables.get_pixel_loc("first_bed_slot_y"))
        time.sleep(0.3 * settings.lag_offset)  # allow orange “ready” text to materialize

        if not template.template_await_true(template.check_teleporter_orange, 3):
            logs.logger.warning(
                "orange pixel for teleporter ready not found; likely already on this TP — closing TP and continuing"
            )
            close()
        else:
            time.sleep(0.2 * settings.lag_offset)
            windows.click(variables.get_pixel_loc("first_bed_slot_x"), variables.get_pixel_loc("first_bed_slot_y"))
            time.sleep(0.2 * settings.lag_offset)
            windows.click(variables.get_pixel_loc("spawn_button_x"), variables.get_pixel_loc("spawn_button_y"))

            if template.template_await_true(template.white_flash, 2):
                logs.logger.debug("white flash detected waiting for up to 5 seconds")
                template.template_await_false(template.white_flash, 5)

            # small log poke to lock render
            ASA.player.tribelog.open()
            ASA.player.tribelog.close()

        time.sleep(0.5 * settings.lag_offset)

        # singleplayer view correction if needed
        if settings.singleplayer:
            utils.current_pitch = 0
            utils.turn_down(80)
            time.sleep(0.2)

        utils.turn_up(80)
        time.sleep(0.2)
        # normalize to station yaw for this TP
        utils.set_yaw(stationdata.yaw)
