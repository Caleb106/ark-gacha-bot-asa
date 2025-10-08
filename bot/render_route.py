import os, json, time
import settings, utils, template
import logs.gachalogs as logs

from ASA.player import tribelog
from ASA.stations import custom_stations
from ASA.strucutres import teleporter
import bot.render as tekpod

DWELL = int(getattr(settings, "render_dwell_seconds", 25))
REST  = int(getattr(settings, "render_rest_seconds", 2700))

def load() -> list:
    """Load route from json_files/render_route.json (or cwd fallback)."""
    for p in ("json_files/render_route.json", "render_route.json"):
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
            except Exception as e:
                logs.logger.error(f"_load_route - render route load failed: {e}")
                return []
    logs.logger.error("_load_route - render_route.json not found")
    return []

def _normalize(yaw: float | None):
    utils.zero()
    if yaw is not None:
        utils.set_yaw(yaw)
    time.sleep(0.10 * settings.lag_offset)

def _open_tp_ui_with_wait():
    utils.turn_down(80)
    time.sleep(0.30 * settings.lag_offset)
    teleporter.open()
    if not template.template_await_true(template.teleport_icon, 10, 0.55):
        raise RuntimeError("teleport icons did not appear")

def _tp_to(meta) -> bool:
    for attempt in (1, 2):
        try:
            _open_tp_ui_with_wait()
            teleporter.teleport_not_default(meta)  # select by exact name
            teleporter.close()
            time.sleep(0.80 * settings.lag_offset)
            utils.turn_up(80)
            time.sleep(0.20 * settings.lag_offset)
            _normalize(getattr(meta, "yaw", None))
            return True
        except Exception as e:
            logs.logger.warning(f"teleport to '{getattr(meta,'name',meta)}' failed (try {attempt}): {e}")
            try: teleporter.close()
            except Exception: pass
            time.sleep(0.60 * settings.lag_offset)
    return False

def run(route: list, loop: bool = False):
    if not route:
        logs.logger.warning("render route empty")
        return

    # leave render bed using legacy sequence
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

            try: tribelog.open()
            except Exception: pass

            time.sleep(DWELL * settings.lag_offset)

            try: tribelog.close()
            except Exception: pass

        # return to render bed and rest
        bed_name = getattr(settings, "render_bed_spawn", getattr(settings, "bed_spawn", "GACHARENDER"))
        bed_meta = custom_stations.get_station_metadata(bed_name)

        if _tp_to(bed_meta):
            tekpod.enter_tekpod()
            try: tribelog.open()
            except Exception: pass
            logs.logger.info(f"RenderRoute: rest {REST}s")
            time.sleep(REST)
            try: tribelog.close()
            except Exception: pass

        if not loop:
            break
