import settings
import time
import template
import logs.gachalogs as logs
import bot.render
from ASA.strucutres import bed , teleporter , inventory
from ASA.player import buffs , console , player_state , tribelog , player_inventory
from ASA.stations import custom_stations
from bot import config , deposit , gacha , iguanadon , pego 
from abc import ABC ,abstractmethod
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
    def __init__(self,name,teleporter_name,direction):
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

        if (berry_station or time_between > config.time_to_reberry*60*60): # if time is greater than 4 hours since the last time you went to berry station 
            teleporter.teleport_not_default(berry_metadata)                    # or if berry station is true( when you go to tekpod and drop all ) and the time between has been longer than 30 mins since youve last been 
            if settings.external_berry: 
                logs.logger.debug("sleeping for 20 seconds as external")
                time.sleep(20)#letting station spawn in if you have to tp away
            iguanadon.berry_station()
            last_berry = time.time()
            berry_station = False
            temp = True
        
        teleporter.teleport_not_default(iguanadon_metadata) # iguanadon is a centeral tp
        
        if settings.external_berry and temp: # quick fix for level 1 bug
            logs.logger.debug("reconnecting because of level 1 bug - you chose external berry will sleep for 60 seconds as a way to ensure that we are fully loaded in")
            console.console_write("reconnect")
            time.sleep(60) # takes a while for the reonnect to actually go into action

        iguanadon.iguanadon(iguanadon_metadata)
        teleporter.teleport_not_default(gacha_metadata)
        gacha.drop_off(gacha_metadata)

    def get_priority_level(self):
        return 3
    
    def get_requeue_delay(self):
        if settings.seeds_230:
            delay = 10700  # should take about this amount of time to do 230 slots of seeds 
        else:
            delay = 6600    # delay can be constant as it will be the same for all gachas 142 stacks took 110 mins
        return delay 

class pego_station(base_task):
    def __init__(self,name,teleporter_name,delay):
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
        if template.check_template("crystal_in_hotbar",0.7):
            teleporter.teleport_not_default(dropoff_metadata) # everytime you collect you have to drop off makes sense to include it into here 
            deposit.deposit_all(dropoff_metadata)
        else:
            logs.logger.info(f"bot has no crystals in hotbar we are skipping the deposit step")

    def get_priority_level(self):
        return 2 # highest prio level as we cant have these get capped 

    def get_requeue_delay(self):
        return self.delay # delay cannot be constant as stations can cover different amounts of space each |||| 2 stacks of berries to 1 crystal 4 gachas to 1 pego
    
    
class render_station(base_task):
    def __init__(self):
        super().__init__()
        self.name = settings.bed_spawn
        
    def execute(self):
        global berry_station 
        berry_station = True # setting to true as we will be away for mostlikly for a few hours
        if bot.render.render_flag == False:
            logs.logger.debug(f"render flag:{bot.render.render_flag} we are trying to get into the pod now")
            player_state.reset_state()
            teleporter.teleport_not_default(settings.bed_spawn)
            bot.render.enter_tekpod()
            player_inventory.open()
            player_inventory.drop_all_inv()
            player_inventory.close()
            tribelog.open()
    def get_priority_level(self):
        return 8

    def get_requeue_delay(self):
        return 90 # after triggered we will wait for 60 seconds reduces the amount of cpu usage 
    
class snail_pheonix(base_task):
    def __init__(self,name,teleporter_name,direction,depo):
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
    def __init__(self,time):
        super().__init__()
        self.name = "pause"
        self.time = time
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
