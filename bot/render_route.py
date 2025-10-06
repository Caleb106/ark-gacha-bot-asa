# bot/render_route.py

import time
import settings
import logs.gachalogs as logs

from ASA.player import player_state, tribelog
from ASA.strucutres import teleporter  # keep project spelling
import bot.render as tekpod
import utils

REST_SECONDS = getattr(settings, "render_rest_seconds", 2700)  # 45 min default


def _normalize_view():
    """Normalize pitch and yaw so the bot always faces forward."""
    try:
        utils.zero()
        utils.set_yaw(settings.station_yaw)
        time.sleep(0.1 * settings.lag_offset)
    except Exception as e:
        logs.logger.debug(f"normalize skipped: {e}")


def _teleport_by_name(name: str) -> bool:
    """
    Open the teleporter, select the destination by name, and trigger teleport.
    Returns True if a teleport was attempted.
    """
    try:
        teleporter.open()
        teleporter.teleport_not_default(name)
        teleporter.close()
        return True
    except Exception as e:
        logs.logger.warning(f"teleport to '{name}' failed: {e}")
        try:
            teleporter.close()
        except Exception:
            pass
        return False


def _end_at_bed_and_rest():
    """
    Return to render bed and rest inside tekpod with tribelog visible.
    """
    bed_name = getattr(settings, "render_bed_spawn",
                       getattr(settings, "bed_spawn", "GACHARENDER"))
    try:
        logs.logger.info(f"RenderRoute: returning to bed '{bed_name}'")
        teleporter.open()
        teleporter.teleport_not_default(bed_name)
        teleporter.close()
    except Exception as e:
        logs.logger.error(f"bed return failed: {e}")

    # settle and normalize after last teleport
    time.sleep(1.0 * settings.lag_offset)
    _normalize_view()

    # enter tekpod and rest with tribe log open
    try:
        tekpod.enter_tekpod()
    except Exception as e:
        logs.logger.error(f"enter_tekpod failed: {e}")

    try:
        tribelog.open()
    except Exception:
        pass

    sleep_s = max(0, int(getattr(settings, "render_rest_seconds", REST_SECONDS)))
    logs.logger.info(f"RenderRoute: rest {sleep_s}s")
    time.sleep(sleep_s)

    try:
        tribelog.close()
    except Exception:
        pass


def run(route, dwell_s: int = 25, loop: bool = False, end_at_bed: bool = True, settle_s: float = 1.0):
    """
    Execute a render route.
      - route: list of teleporter destinations. Each item can be a string or a dict with key 'teleporter'.
      - dwell_s: seconds to keep the area rendered at each stop.
      - loop: if True, repeats the route indefinitely.
      - end_at_bed: if True, return to render bed and rest.
      - settle_s: extra wait right after each teleport finishes.

    Behavior:
      * After each teleport, normalize direction with utils.zero() + utils.set_yaw().
      * Open tribe logs and keep visible for the entire dwell period.
    """
    if not isinstance(route, (list, tuple)) or not route:
        logs.logger.warning("RenderRoute: empty route provided")
        return

    dwell_s = int(dwell_s)
    if dwell_s < 0:
        dwell_s = 0

    while True:
        for idx, dest in enumerate(route, start=1):
            if not dest:
                continue

            # Resolve destination name/label
            if isinstance(dest, dict):
                target = dest.get("teleporter") or dest.get("name") or str(dest)
                label = dest.get("name", target)
            else:
                target = str(dest)
                label = target

            logs.logger.info(f"RenderRoute: {idx}/{len(route)} -> {label}")

            if not _teleport_by_name(target):
                # Skip this stop on error
                continue

            # Let destination load and normalize
            time.sleep(settle_s * settings.lag_offset)
            _normalize_view()

            # Keep Tribe Log open while dwelling
            try:
                tribelog.open()
            except Exception:
                pass

            time.sleep(dwell_s * settings.lag_offset)

            try:
                tribelog.close()
            except Exception:
                pass

        if end_at_bed:
            _end_at_bed_and_rest()

        if not loop:
            break
