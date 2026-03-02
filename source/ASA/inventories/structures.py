import source.logs.gachalogs as logs 
from source.utility import utils ,template , windows ,variables ,screen ,local_player
import time
import settings
import source.ASA.config 
import source.ASA.inventories.inventory

inv_slots = { 
    "x" : 1660,
    "y" : 320,
    "distance" : 125
}

class structure_inventory(source.ASA.inventories.inventory.inventory):
    def __init__(self):
        super().__init__()
    
    def open(self):
        attempts = 0 
        while not self.is_open():
            attempts += 1
            logs.logger.debug(f"trying to open strucuture inventory {attempts} / {source.ASA.config.inventory_open_attempts}")
            utils.press_key("AccessInventory")
            if template.template_await_true(template.check_template,2,"inventory",0.7):
                logs.logger.debug(f"inventory opened")
                if template.template_await_true(template.check_template,1,"waiting_inv",0.8):
                    start = time.time()
                    logs.logger.debug(f"waiting for up too 10 seconds due to the reciving remote inventory is present")
                    template.template_await_false(template.check_template,10,"waiting_inv",0.8)
                    logs.logger.debug(f"{time.time() - start} seconds taken for the reciving remote inventory to go away")
                    break
                
            #check state of the char before redoing
            else:
                source.ASA.player.player_state.check_state()
            if attempts >= source.ASA.config.inventory_open_attempts:
                logs.logger.error(f"unable to open up the objects inventory")
                break
        time.sleep(0.3*settings.lag_offset)

    def search_in_object(self,item:str): 
        if self.is_open():    
            logs.logger.debug(f"searching in structure/dino for {item}")
            time.sleep(0.2*settings.lag_offset)
            windows.click(variables.get_pixel_loc("search_object_x"),variables.get_pixel_loc("transfer_all_y"))
            utils.ctrl_a() 
            time.sleep(0.2*settings.lag_offset)
            utils.write(item)
            time.sleep(0.1*settings.lag_offset)
        
    def drop_all_obj(self):
        if self.is_open():    
            logs.logger.debug(f"dropping all items from object")
            time.sleep(0.2*settings.lag_offset)
            windows.click(variables.get_pixel_loc("drop_all_obj_x"),variables.get_pixel_loc("transfer_all_y")) 
            time.sleep(0.1*settings.lag_offset)

    def transfer_all_from(self): 
        if self.is_open():
            logs.logger.debug(f"transfering all from object")
            time.sleep(0.2*settings.lag_offset)
            windows.click(variables.get_pixel_loc("transfer_all_from_x"), variables.get_pixel_loc("transfer_all_y"))
            time.sleep(0.1*settings.lag_offset)

    def popcorn_top_row(self):
        if self.is_open():
            for count in range(6):
                time.sleep(0.1*settings.lag_offset)
                x = inv_slots["x"] + (count *inv_slots["distance"]) + 30 # x pos = startx + distancebetweenslots * count 
                y = inv_slots["y"] + 30
                if screen.screen_resolution == 1080:
                    windows.move_mouse(x * 0.75,y * 0.75)
                else:
                    windows.move_mouse(x,y)
                time.sleep(0.1*settings.lag_offset)
                utils.press_key("DropItem")
    
