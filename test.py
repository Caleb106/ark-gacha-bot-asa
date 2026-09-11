from logger.logger import logger
import source.crafting.items as i
import source.utility.template as t 
import time 

while True:
    time.sleep(1)
    r = t.item_save()
    a = i.get_amount_of_item(r, "element_dust", 0.9)
    logger.debug(a)