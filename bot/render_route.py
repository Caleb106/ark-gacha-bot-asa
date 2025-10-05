import time
import settings
import logs.gachalogs as logs

from ASA.player import player_state, tribelog
from ASA.strucutres import teleporter
import bot.render as tekpod
import utils

# config import for retry counts
try:
    from bot import config
except ImportError:
    import config

REST_SECONDS = getattr(settings, "render_rest_seconds", 2700)  # 45 min default


def _teleport_by_name(name: str) -> bool:
    try:
        teleporter.teleport_not_default(name)
        return True
    except Exception as e:
        logs.logger.error(f"RenderRoute: teleport to '{name}' failed: {e}")
        return False


def _tp_with_retries(dest: str) -> bool:
    attempts = int(getattr(config, "render_tp_attempts",
                           getattr(config, "render_attempts", 3)))
    attempts = max(1, attempts)
    for i in range(attempts):
        if _teleport_by_name(dest):
            return True
        logs.logger.warning(f"RenderRoute: teleport '{dest}' failed {i+1}/{attempts}")
        time.sleep(1.0 * settings.lag_offset)
    return False


def _end_at_bed_and_rest():
    try:
        if not _tp_with_retries(settings.bed_spawn):
            logs.logger.warning("RenderRoute: bed teleporter unreachable after retries")
            return
        time.sleep(1.5 * settings.lag_offset)
        tekpod.enter_tekpod()
        logs.logger.info("RenderRoute: returned to bed and entered Tek Pod")
        # Open Tribe Logs and rest
        tribelog.open()
        wait_s = max(0, int(REST_SECONDS))
        logs.logger.info(f"RenderRoute: resting with Tribe Log open for {wait_s} seconds")
        time.sleep(wait_s * settings.lag_offset)
        tribelog.close()
    except Exception as e:
        logs.logger.error(f"RenderRoute: end_at_bed_and_rest failed: {e}")


def run(route, dwell_s: int = 25, loop: bool = False, end_at_bed: bool = True, settle_s: float = 1.5):
    """
    Accepts either:
      - list[str]: each item is a teleporter name
      - list[dict]: each item may include:
            teleporter: str   (required)
            name: str         (optional label only)
            stay_s: int       (optional per-stop dwell seconds)
            yaw: float        (optional per-stop yaw)
            pitch: float      (optional per-stop pitch)
            open_tribe_logs: bool (default True)
    """
    while True:
        player_state.check_state()

        total = len(route)
        for idx, item in enumerate(route, start=1):
            # Normalize entry
            if isinstance(item, dict):
                dest = str(item.get("teleporter", "")).strip()
                stay = int(item.get("stay_s", dwell_s))
                yaw  = item.get("yaw", None)
                pitch = item.get("pitch", None)
                show_logs = bool(item.get("open_tribe_logs", True))
            else:
                dest = str(item).strip()
                stay = int(dwell_s)
                yaw = None
                pitch = None
                show_logs = True

            if not dest:
                continue

            logs.logger.info(f"RenderRoute: {idx}/{total} -> {dest}")
            if not _tp_with_retries(dest):
                logs.logger.warning(f"RenderRoute: skip '{dest}' after retries")
                continue
            time.sleep(settle_s * settings.lag_offset)

            # Orientation
            try:
                if yaw is not None:
                    utils.set_yaw(float(yaw))
                else:
                    utils.set_yaw(getattr(settings, "station_yaw", 0))
            except Exception:
                pass
            try:
                if pitch is not None:
                    utils.set_pitch(float(pitch))
            except Exception:
                pass

            # Keep Tribe Log open while rendering
            if show_logs:
                tribelog.open()
            time.sleep(max(0, int(stay)) * settings.lag_offset)
            if show_logs:
                tribelog.close()

        if end_at_bed:
            _end_at_bed_and_rest()

        if not loop:
            break
