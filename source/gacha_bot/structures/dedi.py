import time 
import settings
import json
from source.utility import utils ,template , windows ,variables ,screen ,local_player
from source.logs import gachalogs as logs
from source.ASA.strucutres import teleporter , inventory
from source.ASA.stations import custom_stations
from source.ASA.player import player_inventory , player_state
import source.gacha_bot.config 

def load_dedi_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def dedi_deposit_deafult(height):
    '''
    default dedi deposit will be used when no locations are provided in the dedis.json file IE set to 0 or whatever will suggest that files have not been edited
    '''
    if height == 3:
        utils.turn_up(15)
        utils.turn_left(10)
        time.sleep(0.3*settings.lag_offset)
        utils.press_key("Use")
        time.sleep(0.3*settings.lag_offset)
        utils.turn_right(40)
        time.sleep(0.3*settings.lag_offset)
        utils.press_key("Use")
        time.sleep(0.3*settings.lag_offset)
        utils.turn_left(30)
        utils.turn_down(15)
        time.sleep(0.3*settings.lag_offset)

    utils.turn_left(10)
    utils.press_key("Crouch")
    time.sleep(0.3*settings.lag_offset)
    utils.press_key("Use")
    time.sleep(0.3*settings.lag_offset)
    utils.turn_right(40)
    time.sleep(0.3*settings.lag_offset)
    utils.press_key("Use")
    time.sleep(0.3*settings.lag_offset)
    utils.turn_down(30)
    time.sleep(0.3*settings.lag_offset)
    utils.press_key("Use")
    time.sleep(0.3*settings.lag_offset)
    utils.turn_left(40)
    time.sleep(0.3*settings.lag_offset)
    utils.press_key("Use")
    time.sleep(0.3*settings.lag_offset)
    utils.press_key("Run")
    utils.turn_up(30)
    utils.turn_right(10)
    time.sleep(0.1*settings.lag_offset)

def resource_finder(resource,dedi_stack):
    found_id = [] # we return this array instead of just the first value we find to ensure that we dont miss any dedis 
    for x in range(len(dedi_stack["dediBoxes"])):
        if dedi_stack["dediBoxes"][x]["resource"] == resource:
            found_id.append(x)
    if len(found_id) > 0:
        return [dedi_stack["dediID"],found_id]    

def find_dedis_with_resource(resource):
    dedi_data = load_dedi_data("json_files\dedis.json")
    locations = []
    for x in range(len(dedi_data)):
        data = resource_finder(resource,dedi_data[x])
        if data != None:
            locations.append(data)
    return locations
    
def get_info_on_dedi(dedi_id,position):
    full_file = load_dedi_data("json_files\dedis.json")
    for x in range(len(full_file)):
        if dedi_id == full_file[x]["dediID"]:
            print(full_file[x]["dediBoxes"][position])
            dedi_info = full_file[x]["dediBoxes"][position]
            yaw = dedi_info["location"]["yaw"]
            pitch = dedi_info["location"]["pitch"]
            crouched = dedi_info["crouched"]
            return yaw , pitch, crouched

def get_resource_from_dedis(resource):
    capped = False
    resource_positions = find_dedis_with_resource(resource)
    for x in range(len(resource_positions)):
        #teleport to the tp with the dedi
        #teleporter.teleport_not_default(resource_positions[x][0])
        utils.pitch_zero()
        utils.set_yaw(settings.station_yaw) # its done this in the tp part to the dedis
        for y in range(len(resource_positions[x][1])):
            yaw, pitch, crouched =get_info_on_dedi(resource_positions[x][0],resource_positions[x][1][y])
            utils.turn_to(pitch,yaw)
            if crouched:
                player_state.human.crouch()
            #open dedi
            #transfer all from
            #exit
            #check if capped if capped go on else go to the next 
            #
    #if overcapped we dont tp again 
    

def dedi_deposit(dedi_type):
    '''
    i guess with this you could put more dedis than the default numbers of 6 or 4 depending on if the bot can reach them 
    '''
    full_file = load_dedi_data("json_files\dedis.json")
    utils.pitch_zero()
    utils.set_yaw(settings.station_yaw)
    for x in range(len(full_file)):
        if dedi_type == full_file[x]["dediID"]:
            for y in range(len(full_file[x]["dediBoxes"])):
                yaw, pitch, crouched = get_info_on_dedi(dedi_type,y)
                utils.turn_to(pitch,yaw)
                time.sleep(0.2*settings.lag_offset)
                if crouched:
                    player_state.human.crouch()
                utils.press_key("Use")
                time.sleep(0.2*settings.lag_offset)

    player_state.human.reset_crouch()
                