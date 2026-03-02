import ctypes
import time
from source.join_sim.source.utility import local_player ,windows

"""
FUNCTIONS FOR KEYBOARD 
"""
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102

keymap = {
    "tab":0x09,"escape" :0x1B,"return":0x0D, "enter":0x0D, "leftcontrol":0xA2, "zero": 0x30,
    "one":0x31, "two":0x32, "three":0x33 , "four":0x34 , "five":0x35 , "six":0x36 , "seven":0x37,
    "eight":0x38, "nine":0x39, "thumbmousebutton": 0x05, "thumbmousebutton2": 0x06, "spacebar": 0x20,"hyphen":0xBD,
    "leftshift":0xA0 , "tilde":0xC0
}

default_keymap = { 
    "use": "e", "consolekeys": "tilde", "showtribemanager": "l", "showmyinventory": "i", "accessinventory": "f", "dropitem":"o",
    "pausemenu": "escape","reload":"r","run":"leftshift","crouch":"c","useitem1": "one","useitem2": "two","useitem3": "three","useitem4": "four",
    "useitem5": "five","useitem6": "six","useitem7": "seven","useitem8": "eight","useitem9": "nine","useitem10": "zero"
}

hwnd = windows.hwnd
ctypes.windll.user32.VkKeyScanA.argtypes = [ctypes.c_char]
ctypes.windll.user32.VkKeyScanA.restype = ctypes.c_short  

def keymap_return(key_input):
    key = key_input.lower()

    if key in default_keymap: # this would only be triggered if the input.ini file is empty || base key mpa

        key = default_keymap[key]
        if key in keymap:
            return keymap[key]

    if key in keymap:
        return keymap[key]
 
    if len(key) == 1:
        result = ctypes.windll.user32.VkKeyScanA(ord(key))
   
        vk_code = result & 0xFF
        
        return vk_code

def press_key(input_action):
    vk_code = keymap_return(local_player.get_input_settings(input_action))

    ctypes.windll.user32.PostMessageW(hwnd, WM_KEYDOWN , vk_code, 0)
    time.sleep(0.05)
    ctypes.windll.user32.PostMessageW(hwnd, WM_KEYUP , vk_code, 0)

def post_charecter(char):
    ctypes.windll.user32.PostMessageW(hwnd, WM_CHAR, ord(char), 0)

def write(text):
    for c in text:
        post_charecter(c)
        
def ctrl_a(): # hotkey for sending ctrl a 
    ctypes.windll.user32.SendMessageW(windows.hwnd, WM_KEYDOWN, 0x11, 0)
    time.sleep(0.1)
    ctypes.windll.user32.SendMessageW(windows.hwnd, WM_KEYDOWN, 0x41, 0)
    time.sleep(0.1)  
    
    ctypes.windll.user32.SendMessageW(windows.hwnd, WM_KEYUP, 0x41, 0)
    time.sleep(0.1)
    ctypes.windll.user32.SendMessageW(windows.hwnd, WM_KEYUP, 0x11, 0)