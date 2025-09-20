import json
import settings

class station_metadata():
    def __init__(self):
        super().__init__()
        self.name = None
        self.xpos = None
        self.ypos = None
        self.zpos = None
        self.yaw = None
        self.pitch = 0
        self.side = None
        self.resource = None

def get_custom_stations():
    file_path = "json_files/stations.json"
    try:
        with open(file_path, 'r') as file:
            data = file.read().strip()
            if not data:
                return []
            return json.loads(data)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return []


def get_station_metadata(teleporter_name:str):
    global custom_stations
    custom_stations = False
    stationdata = station_metadata()
    foundstation = False

    all_stations = get_custom_stations()

    if len(all_stations) > 0:
        custom_stations = True
        for entry_station in all_stations:
            if entry_station["name"] == teleporter_name:
                stationdata.name = entry_station["name"]
                stationdata.xpos = entry_station["xpos"]
                stationdata.ypos = entry_station["ypos"]
                stationdata.zpos = entry_station["zpos"]
                stationdata.yaw  = entry_station["yaw"]
                #stationdata.pitch = entry_station["pitch"]
                foundstation = True
                break

    if not foundstation:   #setting up default station metadata
        stationdata.name = teleporter_name
        stationdata.xpos = 0
        stationdata.ypos = 0
        stationdata.zpos = 0
        stationdata.yaw = settings.station_yaw
        stationdata.pitch = 0

    return stationdata