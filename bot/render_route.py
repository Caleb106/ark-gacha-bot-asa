import time
import settings
import utils
import logs.gachalogs as logs

from ASA.player import tribelog
from ASA.stations import custom_stations
from ASA.strucutres import teleporter
import bot.render as tekpod

DWELL = int(getattr(settings, "render_dwell_seconds", 25))
REST  = int(getattr(settings, "render_rest_seconds", 2700))

class _Override:
    """Temporarily override settings fields."""
    def __init__(self, **vals):
        self.vals = vals
        self.prev = {}
    def __enter__(self):
        for k, v in self.vals.items():
            self.prev[k] = getattr(settings, k, None)
            setattr(settings, k, v)
    def __exit__(self, *exc):
        for k, v in self.prev.items():
            setattr(settings, k, v)

def _normalize(yaw: float | None):
    # zero then snap to desired yaw; tiny settle to mimic legacy pacing
    utils.zero()
    if yaw is not None:
        utils.set_yaw(yaw)
    time.sleep(0.10 * settings.lag_offset)

def _tp_to(meta) -> bool:
    """Open teleporter UI, pick destination by name, wait, post-TP view fix."""
    try:
        teleporter.open()
        teleporter.teleport_not_default(meta)  # legacy selector logic
        teleporter.close()
        # settle, then look up and normalize to meta yaw like the original flow
        time.sleep(0.80 * settings.lag_offset)
        utils.turn_up(80)
        time.sleep(0.20 * settings.lag_offset)
        _normalize(meta.yaw)
        return True
    except Exception as e:
        logs.logger.warning(f"teleport to '{getattr(meta,'name',meta)}' failed: {e}")
        try: teleporter.close()
        except Exception: pass
        return False

def run(route: list, loop: bool = False):
    """
    Sequence:
    - leave bed with legacy pacing
    - for each stop: open tribelog, dwell, close tribelog
    - return to render bed, enter it, open tribelog, rest, close tribelog
    """
    if not route:
        logs.logger.warning("render route empty")
        return

    # ensure we start cleanly
    tekpod.leave_tekpod()
    time.sleep(0.30 * settings.lag_offset)

    while True:
        for idx, stop in enumerate(route, 1):
            tp_name = stop.get("teleporter") if isinstance(stop, dict) else str(stop)
            label   = stop.get("name", tp_name) if isinstance(stop, dict) else tp_name

            meta = custom_stations.get_station_metadata(tp_name)
            logs.logger.info(f"RenderRoute: {idx}/{len(route)} -> {label}")

            if not _tp_to(meta):
                continue

            # open tribelog for the dwell; close after
            try: tribelog.open()
            except Exception: pass

            time.sleep(DWELL * settings.lag_offset)

            try: tribelog.close()
            except Exception: pass

        # back to render bed and rest
        bed_name = getattr(settings, "render_bed_spawn", getattr(settings, "bed_spawn", "GACHARENDER"))
        bed_meta = custom_stations.get_station_metadata(bed_name)

        if _tp_to(bed_meta):
            # use bed-specific yaw and pushout while entering the pod
            with _Override(station_yaw=bed_meta.yaw, render_pushout=getattr(bed_meta, "pushout", getattr(settings, "render_pushout", 0))):
                tekpod.enter_tekpod()
                try: tribelog.open()
                except Exception: pass
                logs.logger.info(f"RenderRoute: rest {REST}s")
                time.sleep(REST)
                try: tribelog.close()
                except Exception: pass

        if not loop:
            break
