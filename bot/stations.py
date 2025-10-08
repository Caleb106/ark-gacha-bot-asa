import settings
import time
import template
import logs.gachalogs as logs
import bot.render
from ASA.strucutres import bed, teleporter, inventory
from ASA.player import buffs, console, player_state, tribelog, player_inventory
from ASA.stations import custom_stations
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
        pass

    @abstractmethod
    def get_priority_level(self):
        pass

    @abstractmethod
    def get_requeue_delay(self):
        pass

    def mark_as_run(self):
        self.has_run_before = True


class gacha_station(base_task):
    def __init__(self, name, teleporter_name, direction):
        super().__init__()
        self.name = name
        self.teleporter_name = teleporter_name
        self.direction = direction

    def execute(self):
        player_state.check_state()
        global berry_station
        global last_berry

        temp = False
        time_between = time.time() - last_berry

        gacha_metadata = custom_stations.get_station_metadata(self.teleporter_name)
        gacha_metadata.side = self.direction

        berry_metadata = custom_stations.get_station_metadata(settings.berry_station)
        iguanadon_metadata = custom_stations.get_station_metadata(settings.iguanadon)

        # Re-berry if flagged or > threshold
        if berry_station or time_between > config.time_to_reberry * 60 * 60:
            teleporter.teleport_not_default(berry_metadata)
            if settings.external_berry:
                logs.logger.debug("sleeping for 20 seconds as external")
                time.sleep(20)
            iguanadon.berry_station()
            last_berry = time.time()
            berry_station = False
            temp = True

        teleporter.teleport_not_default(iguanadon_metadata)

        if settings.external_berry and temp:
            logs.logger.debug(
                "reconnecting because of level 1 bug - external berry; sleep 60s"
            )
            console.console_write("reconnect")
            time.sleep(60)

        iguanadon.iguanadon(iguanadon_metadata)
        teleporter.teleport_not_default(gacha_metadata)
        gacha.drop_off(gacha_metadata)

    def get_priority_level(self):
        return 3

    def get_requeue_delay(self):
        if settings.seeds_230:
            return 10700
        return 6600


class pego_station(base_task):
    def __init__(self, name, teleporter_name, delay):
        super().__init__()
        self.name = name
        self.teleporter_name = teleporter_name
        self.delay = delay

    def execute(self):
        player_state.check_state()

        pego_metadata = custom_stations.get_station_metadata(self.teleporter_name)
        dropoff_metadata = custom_stations.get_station_metadata(settings.drop_off)

        teleporter.teleport_not_default(pego_metadata)
        pego.pego_pickup(pego_metadata)
        if template.check_template("crystal_in_hotbar", 0.7):
            teleporter.teleport_not_default(settings.open_crystals)
            deposit.open_crystals()
            deposit.dedi_deposit(settings.height_ele)
            teleporter.teleport_not_default(dropoff_metadata)
            deposit.deposit_all(dropoff_metadata)
        else:
            logs.logger.info("no crystals in hotbar; skipping deposit")

    def get_priority_level(self):
        return 2

    def get_requeue_delay(self):
        return self.delay


class render_station(base_task):
    def __init__(self):
        super().__init__()
        # FIX: use the dedicated render bed, not the generic bed
        self.name = settings.render_bed_spawn

    def execute(self):
        global berry_station
        berry_station = True  # we’ll be away a while

        if bot.render.render_flag is False:
            logs.logger.debug(
                f"render flag:{bot.render.render_flag} attempting to get into tekpod now"
            )
            player_state.reset_state()
            # FIX: teleport to the render bed specifically
            teleporter.teleport_not_default(settings.render_bed_spawn)
            bot.render.enter_tekpod()
            player_inventory.open()
            player_inventory.drop_all_inv()
            player_inventory.close()
            tribelog.open()

    def get_priority_level(self):
        return 8

    def get_requeue_delay(self):
        return 90


class snail_pheonix(base_task):
    def __init__(self, name, teleporter_name, direction, depo):
        super().__init__()
        self.name = name
        self.teleporter_name = teleporter_name
        self.direction = direction
        self.depo_tp = depo

    def execute(self):
        gacha_metadata = custom_stations.get_station_metadata(self.teleporter_name)
        gacha_metadata.side = self.direction

        player_state.check_state()
        teleporter.teleport_not_default(gacha_metadata)
        gacha.collection(gacha_metadata)
        teleporter.teleport_not_default(self.depo_tp)
        deposit.dedi_deposit(settings.height_ele)

    def get_priority_level(self):
        return 4

    def get_requeue_delay(self):
        return 13200


class pause(base_task):
    def __init__(self, time_seconds):
        super().__init__()
        self.name = "pause"
        self.time = time_seconds

    def execute(self):
        player_state.check_state()
        teleporter.teleport_not_default(settings.bed_spawn)
        bot.render.enter_tekpod()
        time.sleep(self.time)
        bot.render.leave_tekpod()

    def get_priority_level(self):
        return 1

    def get_requeue_delay(self):
        return 0
