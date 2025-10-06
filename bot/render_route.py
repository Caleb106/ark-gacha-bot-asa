import time
import settings
import logs.gachalogs as logs

from ASA.player import tribelog
from ASA.strucutres import teleporter
from ASA.stations import custom_stations
import bot.render as tekpod
import utils

REST_SECONDS = getattr(settings, "render_rest_seconds", 2700)

class _TempSettings:
    def __init__(self, **kw): self.kw, self.prev = kw, {}
    def __enter__(self):
        for k, v in self.kw.items():
            self.prev[k] = getattr(settings, k, None)
            setattr(settings, k, v)
    def __exit__(self, *a):
        for k, v in self.prev.items():
            setattr(settings, k, v)

def _normalize_to_yaw(yaw):
    try:
        utils.zero()
        if yaw is not None:
            utils.set_yaw(yaw)
        time.sleep(0.1 * settings.lag_offset)
    except Exception as e:
        logs.logger.debug(f"normalize skipped: {e}")

def _teleport(meta) -> bool:
    try:
        teleporter.open()
        teleporter.teleport_not_default(meta)  # sets yaw to meta.yaw internally
        teleporter.close()
        return True
    except Exception as e:
        logs.logger.warning(f"teleport to '{getattr(meta,'name',meta)}' failed: {e}")
        try: teleporter.close()
        except Exception: pass
        return False

def _end_at_bed_and_rest():
    bed_name = getattr(settings, "render_bed_spawn",
                       getattr(settings, "bed_spawn", "GACHARENDER"))
    bed_meta = custom_stations.get_station_metadata(bed_name)

    logs.logger.info(f"RenderRoute: returning to bed '{bed_meta.name}'")
    _teleport(bed_meta)
    time.sleep(1.0 * settings.lag_offset)
    _normalize_to_yaw(bed_meta.yaw)

    overrides = {"station_yaw": bed_meta.yaw}
    if bed_meta.pushout is not None:
        overrides["render_pushout"] = bed_meta.pushout

    with _TempSettings(**overrides):
        try: tekpod.enter_tekpod()
        except Exception as e: logs.logger.error(f"enter_tekpod failed: {e}")

        try: tribelog.open()
        except Exception: pass

        sleep_s = max(0, int(getattr(settings, "render_rest_seconds", REST_SECONDS)))
        logs.logger.info(f"RenderRoute: rest {sleep_s}s")
        time.sleep(sleep_s)

        try: tribelog.close()
        except Exception: pass

def run(route, dwell_s: int = 25, loop: bool = False, end_at_bed: bool = True, settle_s: float = 1.0):
    if not isinstance(route, (list, tuple)) or not route:
        logs.logger.warning("RenderRoute: empty route provided")
        return

    dwell_s = max(0, int(dwell_s))

    while True:
        for idx, dest in enumerate(route, start=1):
            if not dest: continue
            if isinstance(dest, dict):
                tp_name = dest.get("teleporter") or dest.get("name") or str(dest)
                label = dest.get("name", tp_name)
            else:
                tp_name, label = str(dest), str(dest)

            meta = custom_stations.get_station_metadata(tp_name)
            logs.logger.info(f"RenderRoute: {idx}/{len(route)} -> {label}")

            if not _teleport(meta): continue

            time.sleep(settle_s * settings.lag_offset)
            _normalize_to_yaw(meta.yaw)

            try: from ASA.player import tribelog; tribelog.open()
            except Exception: pass

            time.sleep(dwell_s * settings.lag_offset)

            try: tribelog.close()
            except Exception: pass

        if end_at_bed: _end_at_bed_and_rest()
        if not loop: break
