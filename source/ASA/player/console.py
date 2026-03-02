from source.ASA.player import player_inventory , player_state
from source.logs import gachalogs as logs
from source.utility import utils ,template , windows ,variables ,screen ,local_player
import time 
import settings
import source.ASA.config
import pyautogui
import win32clipboard

last_command = ""

def is_open():
    return template.console_strip_check(template.console_strip_bottom()) or template.console_strip_check(template.console_strip_middle())

def enter_data(data:str):
    global last_command
    if source.ASA.config.up_arrow and data == last_command:
        logs.logger.debug(f"using uparrow to put {data} into the console")
        pyautogui.press("up")
    else:
        logs.logger.debug(f"using clipboard to put {data} into the console")
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText( data, win32clipboard.CF_TEXT )
        finally:
            win32clipboard.CloseClipboard()
        pyautogui.hotkey("ctrl","v")
    last_command = data
    
def console_ccc():
    data = None
    attempts = 0
    while data == None:
        attempts += 1
        logs.logger.debug(f"trying to get ccc data {attempts} / {source.ASA.config.console_ccc_attempts}")
        player_state.reset_state() #reset state at the start to make sure we can open up the console window
        count = 0
        while not is_open():
            count += 1
            utils.press_key("ConsoleKeys")
            template.template_await_true(is_open,1)
            if count >= source.ASA.config.console_open_attempts:
                logs.logger.error(f"console didnt open after {count} attempts")
                break
        if is_open():
            middle = template.console_strip_check(template.console_strip_middle())
            if attempts >= source.ASA.config.console_ccc_attempts:
                console_write("ccc")
            else: 
                enter_data("ccc")
                close_console(middle)
            
            time.sleep(0.1*settings.lag_offset) # slow to try and prevent opening clipboard to empty data
            try:
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData()
                win32clipboard.EmptyClipboard()
            finally:
                win32clipboard.CloseClipboard()

        if attempts >= source.ASA.config.console_ccc_attempts:
            logs.logger.error(f"CCC is still returning NONE after {attempts} attempts")
            break        
    if data != None:    
        ccc_data = data.split()
        return ccc_data
    return data

def console_write(text:str):
    global last_command
    attempts = 0
    while not is_open():
        attempts += 1
        utils.press_key("ConsoleKeys")
        template.template_await_true(is_open,1)
        if attempts >= source.ASA.config.console_open_attempts:
            logs.logger.error(f"console didnt open after {attempts} attempts unable to input {text}")
            break

    if is_open():
        middle = template.console_strip_check(template.console_strip_middle())
        enter_data(text)
        close_console(middle)
        last_command = text
        time.sleep(0.1*settings.lag_offset) # slow to try and prevent opening clipboard to empty data

def close_console(middle):
    '''
    middle bar console has to have been entered in 2 times 
    before typing we check again for the console location just to make sure 
    '''
    time.sleep(0.1*settings.lag_offset)
    utils.press_key("Enter")

    if middle == True:
        logs.logger.warning(f"middle console open if this is happening alot something should be changed")
        time.sleep(0.1*settings.lag_offset)
        utils.press_key("Enter")