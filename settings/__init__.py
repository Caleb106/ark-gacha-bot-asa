"""Backwards-compatible flat settings, backed by settings/store.py.

Old code does `from settings.lag_offset` etc. This keeps that
working, while store.load()/store.save() is what the Settings UI page
actually reads and writes - both go through the same settings.json.
"""
from settings import store

data = store.load()

lag_offset: float = data["lag_offset"]
iguanadon: str = data["iguanadon"]
drop_off: str = data["drop_off"]
bed_spawn: str = data["bed_spawn"]
berry_station: str = data["berry_station"]
grindables: str = data["grindables"]
cargo_pickup: str = data["cargo_pickup"]
berry_type: str = data["berry_type"]
station_yaw: float = data["station_yaw"]
render_pushout: float = data["render_pushout"]
external_berry: bool = data["external_berry"]
height_ele: int = data["height_ele"]
height_grind: int = data["height_grind"]
command_prefix: str = data["command_prefix"]
singleplayer: bool = data["singleplayer"]
server_number = data["server_number"]
crafting: bool = data["crafting"]
seeds_230: bool = data["seeds_230"]
side_crop_plot: bool = data["side_crop_plot"]
y_trap_bot: bool = data["y_trap_bot"]
use_discord: bool = data["use_discord"]
cargo_ledger: bool = data["cargo_ledger"]
ocr_path: str = data["ocr_path"]
replenish_interval: float = data["replenish_interval"]
ledger_amount: int = data["ledger_amount"]
ledger_gacha_wait: int = data["ledger_gacha_wait"]


log_channel_gacha = data["log_channel_gacha"]
log_active_queue = data["log_active_queue"]
log_wait_queue = data["log_wait_queue"]
discord_api_key = data["discord_api_key"]