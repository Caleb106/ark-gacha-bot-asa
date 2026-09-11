from source.ASA.inventories import structures
from source.utility import template , windows
from logger.logger import logger


class forge(structures.structure_inventory):
    def __init__(self):
        super().__init__()

    def turn_on(self):
        if not template.check_template("turn_off",0.8):
            logger.error("indi forge was turnt off we are turning it back on")
            windows.click(1270,1175)
            
    def open_forge(self):
        open()
        self.turn_on()