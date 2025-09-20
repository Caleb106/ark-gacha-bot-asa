import source.logs.gachalogs as logs 
from source.utility import utils ,template , windows ,variables ,screen ,local_player
import time
import settings
import source.ASA.config

class inventory():
    '''
    Super class for every inventory in ark 
    Class is based on the inventory of the player when pressing the ShowMyInventory button in ASA
    '''
    def __init__(self):
        ...

    def is_open(self)-> bool:
        '''checks if the inventory is on the screen in the top left of the screen'''
        return template.check_template("inventory",0.7)
    
    def open(self):
        attempts = 0 
        while not self.is_open():
            attempts += 1
            logs.logger.debug(f"trying to open player inventory {attempts} / {source.ASA.config.inventory_open_attempts}")
            utils.press_key("ShowMyInventory")
            if template.template_await_true(template.check_template,2,"inventory",0.7):
                logs.logger.debug("inventory opened")
                break
            
            #check state of the char before redoing
            if attempts >= source.ASA.config.inventory_open_attempts:
                logs.logger.error(f"unable to open up the players inventory")
                break
        time.sleep(0.3*settings.lag_offset)
        
    def close(self):
        attempts = 0
        while self.is_open():
            attempts += 1
            logs.logger.debug(f"trying to close objects inventory {attempts} / {source.ASA.config.inventory_close_attempts}")
            windows.click(variables.get_pixel_loc("close_inv_x"), variables.get_pixel_loc("close_inv_y"))
            template.template_await_false(template.check_template,2,"inventory",0.7)
                

            if attempts >= source.ASA.config.inventory_close_attempts:
                logs.logger.error(f"unable to close the objects inventory after {attempts} attempts") 
                #check state of the char the reason we can do it now is that the latter should spam click close inv 
                break 

    #these functions assume that the inventory is already open
    def search_in_inventory(self,item:str):
        if self.is_open():
            logs.logger.debug(f"searching in inventory for {item}")
            time.sleep(0.2*settings.lag_offset)
            windows.click(variables.get_pixel_loc("search_inventory_x"),variables.get_pixel_loc("transfer_all_y")) 
            utils.ctrl_a()  
            time.sleep(0.2*settings.lag_offset)
            utils.write(item)
            time.sleep(0.1*settings.lag_offset)

    def drop_all_inv(self):  
        if self.is_open():
            logs.logger.debug(f"dropping all items from our inventory ")
            time.sleep(0.2*settings.lag_offset)
            windows.click(variables.get_pixel_loc("drop_all_x"),variables.get_pixel_loc("transfer_all_y")) 
            time.sleep(0.1*settings.lag_offset)

    def transfer_all_inventory(self): 
        if self.is_open():
            logs.logger.debug(f"transfering all from our inventory into strucutre")
            time.sleep(0.2*settings.lag_offset)
            windows.click(variables.get_pixel_loc("transfer_all_inventory_x"),variables.get_pixel_loc("transfer_all_y"))
            time.sleep(0.1*settings.lag_offset)
        