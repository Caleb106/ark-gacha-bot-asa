from source.join_sim.source.utility import windows, recon_utils , utils
import time
from source.join_sim.source.logs import logger as logs
 
def bed_spawn():
    return recon_utils.check_template_no_bounds("beds_title",0.7)

def logs():
    return recon_utils.check_template_no_bounds("tribelog_check",0.8)

def download():
    return recon_utils.check_template_no_bounds("download",0.7)

def joined_server()-> bool:
    if bed_spawn() or download():
        return True
    
    utils.press_key("ShowTribeManager")
    time.sleep(0.5)
    if logs():
        return True
    return False
