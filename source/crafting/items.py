import threading

import cv2
from logger.logger import logger
from source.utility import template, ocr , screen
import time

# what we need is a function that starts at the start of the opening crystals 
# then continues till the end 
# while its happening taking screenshots maybe every 0.5 seconds or smth 
# as soon as the item is found we tally
# if it disapears we stop the tally where it is 
# if it reapears we start tallying again from the last location till the end
# at the end we can return the total amount of items found and then reset 

# use worker thread 
#start at the beginning of opening the crystals
# stop at the end
# we also need to take a screenshot while depositing in the dedis can use this to check our values are correct 
#also needed for the grinding station 
  
items = {
    #stores the amount collected  the temporary highest amount and if it is active 
    "gacha_crystal": {"amount": 0,"temp":0, "active": False},
    "element_dust": {"amount": 0,"temp":0, "active": False},
    "org_poly": {"amount": 0,"temp":0, "active": False},
    "black_pearl": {"amount": 0,"temp":0, "active": False},
    "metal_ingot": {"amount": 0,"temp":0, "active": False},
    "flint": {"amount": 0,"temp":0, "active": False},
    "electronics": {"amount": 0,"temp":0, "active": False},
    "crystal": {"amount": 0,"temp":0, "active": False}
}

def is_active():
    roi = template.check_items()

    for item in list(items.keys()) + ["minus", "plus"]:
        found, _ = template.item_counter(roi, item, 0.9)

        if found:
            return True, roi

    return False, roi


def get_amount_of_item(roi, item, threshold):
    b, location = template.item_counter(roi, item, threshold)
    
    if not b:
        return item, None
    scale = screen.screen_resolution / 1440
    logger.debug(scale)
    #roi which is the same as the region with the item 
    amount = ocr.int_only_roi(
    roi,
    int(85 * scale),
    int((location - (12 * scale))),
    int(100 * scale),
    int(24 * scale)
)

    return item, amount

class DepositCounter:
    def __init__(self, interval: float = 0.2, save_fn=None):
        self.items = {item: data.copy() for item, data in items.items()}
        self.interval = interval
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self.save_fn = save_fn 

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, join: bool = True, timeout: float | None = None, save: bool = True):
        self._stop_event.set()
        if join and self._thread:
            self._thread.join(timeout=timeout)

        if save:
            self._flush_and_save()

    def _flush_and_save(self):
        with self.lock:
            for item in self.items:
                self.items[item]["amount"] += self.items[item]["temp"]
                self.items[item]["temp"] = 0
                self.items[item]["active"] = False

            snapshot = {k: v["amount"] for k, v in self.items.items()}

        if self.save_fn:
            self.save_fn(snapshot)

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._deposit_count()
            except Exception as e:
                logger.error(f"deposit_count error: {e}")
            self._stop_event.wait(self.interval)

    def _deposit_count(self):
        active = is_active()
        with self.lock:
            if not active[0]:
                for item in self.items:
                    self.items[item]["amount"] += self.items[item]["temp"]
                    self.items[item]["temp"] = 0
                    self.items[item]["active"] = False
                return

            roi = active[1]
            for item in self.items:
                _, amount = get_amount_of_item(roi, item, 0.9)
                if amount is not None:
                    self.items[item]["active"] = True
                    if amount > self.items[item]["temp"]:
                        self.items[item]["temp"] = amount
                else:
                    if self.items[item]["active"]:
                        self.items[item]["amount"] += self.items[item]["temp"]
                        self.items[item]["temp"] = 0
                        self.items[item]["active"] = False

