import template
import logs.gachalogs as logs
import utils
import windows
import variables
import time 
import settings
import ASA.config 

class inventory():
    '''
    THIS CLASS HAS NO OPPERATBILITY IF YOU CHANGE ANYTHING NOTHING WILL HAPPEN -> GO TO PLAYER OR STRUCTURE // INVENTORY FOR THE RESPECTED SIDE OF UI THAT THE CHAR IS USING TO CHANGE THINGS
    '''
    def __init__(self):
        ...
        
    def is_open(self):
        return template.check_template("inventory",0.7)
    
    def open(self): 
        attempts = 0 
        while not self.is_open():
            attempts += 1
            logs.logger.debug(f"trying to open strucuture inventory {attempts} / {ASA.config.inventory_open_attempts}")
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
            if attempts >= ASA.config.inventory_open_attempts:
                logs.logger.error(f"unable to open up the objects inventory")
                break
        
    def close(self):
        attempts = 0
        while self.is_open():
            attempts += 1
            logs.logger.debug(f"trying to close objects inventory {attempts} / {ASA.config.inventory_close_attempts}")
            windows.click(variables.get_pixel_loc("close_inv_x"), variables.get_pixel_loc("close_inv_y"))
            template.template_await_false(template.check_template,2,"inventory",0.7)
                

            if attempts >= ASA.config.inventory_close_attempts:
                logs.logger.error(f"unable to close the objects inventory after {attempts} attempts") 
                #check state of the char the reason we can do it now is that the latter should spam click close inv 
                break

    #these functions assume that the inventory is already open
    def search_in_inventory(self,item:str):
        logs.logger.debug(f"searching in inventory for {item}")
        time.sleep(0.2*settings.lag_offset)
        windows.click(variables.get_pixel_loc("search_inventory_x"),variables.get_pixel_loc("transfer_all_y")) 
        utils.ctrl_a()  
        time.sleep(0.2*settings.lag_offset)
        utils.write(item)
        time.sleep(0.1*settings.lag_offset)
    
    def drop_all_inv(self):  
        logs.logger.debug(f"dropping all items from our inventory ")
        time.sleep(0.2*settings.lag_offset)
        windows.click(variables.get_pixel_loc("drop_all_x"),variables.get_pixel_loc("transfer_all_y")) 
        time.sleep(0.1*settings.lag_offset)

    def transfer_all_inventory(self): 
        logs.logger.debug(f"transfering all from our inventory into strucutre")
        time.sleep(0.2*settings.lag_offset)
        windows.click(variables.get_pixel_loc("transfer_all_inventory_x"),variables.get_pixel_loc("transfer_all_y"))
        time.sleep(0.1*settings.lag_offset)

    #these are for structure inventories
    def search_in_object(self,item:str): 
        logs.logger.debug(f"searching in structure/dino for {item}")
        time.sleep(0.2*settings.lag_offset)
        windows.click(variables.get_pixel_loc("search_object_x"),variables.get_pixel_loc("transfer_all_y"))
        utils.ctrl_a() 
        time.sleep(0.2*settings.lag_offset)
        utils.write(item)
        time.sleep(0.1*settings.lag_offset)
        
    def drop_all_obj(self):
        logs.logger.debug(f"dropping all items from object")
        time.sleep(0.2*settings.lag_offset)
        windows.click(variables.get_pixel_loc("drop_all_obj_x"),variables.get_pixel_loc("transfer_all_y")) 
        time.sleep(0.1*settings.lag_offset)

    def transfer_all_from(self): 
        logs.logger.debug(f"transfering all from object")
        time.sleep(0.2*settings.lag_offset)
        windows.click(variables.get_pixel_loc("transfer_all_from_x"), variables.get_pixel_loc("transfer_all_y"))
        time.sleep(0.1*settings.lag_offset)