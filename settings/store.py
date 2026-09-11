"""Reads and writes settings.json - the bot's configuration.

The file is the user's, not ours: it can be missing, hand-edited, or
half-corrupt, and none of those may stop the app from starting. load()
therefore always returns a complete, usable dict.

Paired with UI/resources/store.py, which does the same job for the resource
counts. The two differ deliberately in one respect: this one keeps keys it
doesn't recognise (see load), the resources store drops them."""
import json
import os

from logger.logger import logger
from tools.recovery import quarantine

SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "settings.json"
)

# Defaults + canonical key order, used both to seed a fresh settings.json
# and to backfill any keys missing from an older one on load.
DEFAULTS = {
    "lag_offset": 1.0,
    "iguanadon": "Gacha - Iguanadon",
    "drop_off": "Gacha - Dedi",
    "bed_spawn": "Gacha - Render",
    "berry_station": "Gacha - Berrystation",
    "grindables": "Gacha - Grindables",
    "cargo_pickup":"Gacha - Cargoledger",
    "berry_type": "mejoberry",
    "station_yaw": 0.0,
    "render_pushout": 0.0,
    "replenish_interval": 0.0,
    "height_ele": 3,
    "height_grind": 3,
    "command_prefix": "%",
    "server_number": 0,
    "singleplayer": False,
    "external_berry": False,
    "crafting": True,
    "seeds_230": False,
    "side_crop_plot": False,
    "y_trap_bot": True,
    "cargo_ledger": True,
    "use_discord": True,
    "log_channel_gacha": "",
    "log_active_queue": "",
    "log_wait_queue": "",
    "discord_api_key": "",
    "ocr_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe"
}

# Non-string fields need to be cast back to their real type when they come
# out of a Tk entry/switch as text - anything not listed here stays a str.
# The bool entries are only safe because a CTkSwitch's .get() returns 0 or 1,
# not "0"/"1": bool() of any non-empty string is True, so a bool field fed a
# string would come out True whatever it said.
FIELD_TYPES = {
    "lag_offset": float,
    "station_yaw": float,
    "render_pushout": float,
    "height_ele": int,
    "height_grind": int,
    "server_number": int,
    "singleplayer": bool,
    "external_berry": bool,
    "crafting": bool,
    "seeds_230": bool,
    "side_crop_plot": bool,
    "y_trap_bot": bool,
    "use_discord": bool,
    "cargo_ledger": bool,
    "replenish_interval":float, 
    "ocr_path":str,
    "cargo_pickup":str
}


def load() -> dict:
    """Load settings.json, backfilling any keys missing from an older file
    with their default so new settings don't crash old save files.

    The app ships without a settings.json at all, so a missing file is the
    normal first-launch case - and a corrupt one must not crash the app
    either. Both fall back to the defaults and write them to disk.

    Keys the app no longer knows about are kept rather than dropped, so a
    file written by a newer build survives being opened by an older one.
    They only disappear once the settings page saves, which writes the keys
    it has widgets for."""
    data = dict(DEFAULTS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if not isinstance(saved, dict):
            raise TypeError("settings.json root is not an object")
        data.update(saved)
    except FileNotFoundError:
        save(data)
        logger.info("settings.json not found - created it with defaults.")
    except (OSError, ValueError, TypeError) as error:
        backup = quarantine(SETTINGS_PATH)
        save(data)
        recovered = (f"the old file was saved to {backup}" if backup
                     else "the old file could not be backed up")
        logger.warning(f"settings.json unreadable ({error}) - "
                       f"reset to defaults; {recovered}.")
    return data


def save(data: dict) -> None:
    """Write settings.json, casting each field back to its real type first -
    values arriving straight from Tk widgets are strings, and saving them as
    such would turn every number in the file into a quoted one."""
    cast = {}
    for key, value in data.items():
        field_type = FIELD_TYPES.get(key)
        cast[key] = field_type(value) if field_type else value
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(cast, f, indent=4)
