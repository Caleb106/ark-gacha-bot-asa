import pygetwindow as gw
import psutil
import win32process
import subprocess
import os
from source.join_sim.source.logs import logger as logs
from source.join_sim.source.utility import local_player,windows,recon_utils
import time

appid = "2399830"

def detect_crash():
    titles = set(gw.getAllTitles())
    for title in titles:
        if title == "The UE-ShooterGame Game has crashed and will close" or title == "Crash!":
            return True
        
def close_game():
    try:
        _, pid = win32process.GetWindowThreadProcessId(windows.hwnd) 
        process = psutil.Process(pid)

        process.terminate()
        logs.logger.critical(f"game with pid {pid} terminated")
    except psutil.NoSuchProcess:
        logs.logger.critical("process not found")
    except psutil.AccessDenied:
        logs.logger.critical("no permissions to terminate")
    except Exception as e:
        logs.logger.critical(f"error: {e}")

def launch_game_with_steam():
    steam_path = local_player.path("steam.exe")
    print(steam_path)
    if os.path.exists(steam_path):
    
        subprocess.run([steam_path, f"steam://run/{appid}"])
        logs.logger.critical(f"launching game with appid {appid} via steam")
    else:
        logs.logger.critical("steam exe not found at the expected location cannot relaunch game")

def re_open_game():
    close_game()
    time.sleep(10)
    launch_game_with_steam()
    recon_utils.template_sleep_no_bounds("join_last_session",0.7,60)
    windows.hwnd = windows.find_window_by_title("ArkAscended") # new process ID as game as relaunced
    
def crash_rejoin():
    if detect_crash():
        close_game()
        time.sleep(10)
        launch_game_with_steam()
        recon_utils.template_sleep_no_bounds("join_last_session",0.7,60)
        windows.hwnd = windows.find_window_by_title("ArkAscended") # new process ID as game as relaunced