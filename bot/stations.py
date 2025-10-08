import time
import settings
import template
import logs.gachalogs as logs

# core bot pieces
import bot.render as tekpod
from bot import render_route as rr

# ASA helpers
from ASA.player import player_state, player_inventory, tribelog
from ASA.stations import custom_stations
from ASA.strucutres import teleporter

# other task types
from bot import config, deposit, gacha, iguanadon, pego

from abc import ABC, abstractmethod

global berry_station
global last_berry
last_berry = 0
berry_station = True


class base_task(ABC):
    def __init__(self):
        self.has_run_before = False

    @abstractmethod
    def execute(self):
        ...

    @abstractmethod
    def get_priority_level(self) -> int:
        ...

    @abstractmethod
    def get_requeue_delay(self) -> int:
        ...

    def mark_as_run(self):
        self.has_run_before = True


class gacha_station(base_task):
    def __init__(self, name, teleporter_name, direction):
        super().__init__()
        self.name = name
        self.teleporter_name = teleporter_name
        self.direction = direction

    def execute(self):
        global berry_station, last_berry
        player_state.check_state()

        temp = False
        time_between = time.time() - last_berry

        gacha_meta = custom_stations.get_station_metadata(self.teleporter_name)
        gacha_meta.side = self.direction

        berry_meta = custom_stations.get_station_metadata(settings.berry_station)
        ig_meta = custom_stations.get_station_metadata(settings.iguanadon)

        if berry_station or time_between > config.time_to_reberry * 60 * 60:
            teleporter.teleport_not_default(berry_meta)
            if settings.external_berry:
                logs.logger.debug("external berry: wait 20s")
                time.sleep(20)
            iguanadon.berry_station()
            last_berry = time.time()
            berry_station = False
            temp = True

        teleporter.teleport_not_default(ig_meta)

        if settings.external_berry and temp:
            logs.logger.debug("external berry reconnect workaround; sleep 60s")
            from ASA.player import console
            console.console_write("reconnect")
            time.sleep(60)

        iguanadon.iguanadon(ig_meta)
        teleporter.teleport_not_default(gacha_meta)
        gacha.drop_off(gacha_meta)

    def get_priority_level(self): return 3
    def get_requeue_delay(self):  return 10700 if settings.seeds_230 else 6600


class pego_station(base_task):
    def __init__(self, name, teleporter_name, delay):
        super().__init__()
        self.name = name
        self.teleporter_name = teleporter_name
        self.delay = delay

    def execute(self):
        player_state.check_state()

        pego_meta = custom_stations.get_station_metadata(self.teleporter_name)
        drop_meta = custom_stations.get_station_metadata(settings.drop_off)

        teleporter.teleport_not_default(pego_meta)
        pego.pego_pickup(pego_meta)

        if template.check_template("crystal_in_hotbar", 0.7):
            teleporter.teleport_not_default(settings.open_crystals)
            deposit.open_crystals()
            deposit.dedi_deposit(settings.height_ele)
            teleporter.teleport_not_default(drop_meta)
            deposit.deposit_all(drop_meta)
        else:
            logs.logger.info("no crystals in hotbar; skip deposit")

    def get_priority_level(self): return 2
    def get_requeue_delay(self):  return self.delay


class render_station(base_task):
    """Two-phase render task:
       1) If not in bed → go to render bed and get in.
       2) If in bed     → run the render route once, then rest in the render bed.
    """
    def __init__(self):
        super().__init__()
        self.name = "render"

    def execute(self):
        global berry_station
        berry_station = True

        if not tekpod.render_flag:
            # Phase 1: ensure we are in the render bed
            player_state.reset_state()
            teleporter.teleport_not_default(settings.render_bed_spawn)
            tekpod.enter_tekpod()
            try: tribelog.open()
            except Exception: pass
            try:
                player_inventory.open(); player_inventory.drop_all_inv(); player_inventory.close()
            except Exception:
                pass
            return

        # Phase 2: run the route once, render_route handles leaving/returning/rest
        route = rr.load()
        rr.run(route, loop=False)

    def get_priority_level(self): return 8
    def get_requeue_delay(self):  return 90


class snail_pheonix(base_task):
    def __init__(self, name, teleporter_name, direction, depo):
        super().__init__()
        self.name = name
        self.teleporter_name = teleporter_name
        self.direction = direction
        self.depo_tp = depo

    def execute(self):
        gacha_meta = custom_stations.get_station_metadata(self.teleporter_name)
        gacha_meta.side = self.direction

        player_state.check_state()
        teleporter.teleport_not_default(gacha_meta)
        gacha.collection(gacha_meta)
        teleporter.teleport_not_default(self.depo_tp)
        deposit.dedi_deposit(settings.height_ele)

    def get_priority_level(self): return 4
    def get_requeue_delay(self):  return 13200


class pause(base_task):
    def __init__(self, time_seconds):
        super().__init__()
        self.name = "pause"
        self.time = time_seconds

    def execute(self):
        player_state.check_state()
        teleporter.teleport_not_default(settings.bed_spawn)
        tekpod.enter_tekpod()
        time.sleep(self.time)
        tekpod.leave_tekpod()

    def get_priority_level(self): return 1
    def get_requeue_delay(self):  return 0
