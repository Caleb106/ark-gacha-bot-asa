import pygetwindow as gw
import psutil
import win32process
import subprocess
import os
import local_player
import logs.discordbot as discordbot
import time 
import windows
from reconnect import recon_utils
import logs.gachalogs as logs


class crash():
    def __init__(self,hwnd):
        self.appid = "2399830" 
        self.hwnd = hwnd

    def detect_crash(self):

        titles = set(gw.getAllTitles())
        for title in titles:
            if title == "The UE-ShooterGame Game has crashed and will close" or title == "Crash!":
                logs.logger.critical("GAME HAS CRASHED")
                return True

    def close_game(self):
        try:
            _, pid = win32process.GetWindowThreadProcessId(self.hwnd) 
            process = psutil.Process(pid)

            process.terminate()
            logs.logger.critical(f"game with pid {pid} terminated")
        except psutil.NoSuchProcess:
            logs.logger.critical("process not found")
        except psutil.AccessDenied:
            logs.logger.critical("no permissions to terminate")
        except Exception as e:
            logs.logger.critical(f"error: {e}")


    def launch_game_with_steam(self):
        steam_path = local_player.path("steam.exe")
        print(steam_path)
        if os.path.exists(steam_path):
        
            subprocess.run([steam_path, f"steam://run/{self.appid}"])
            logs.logger.critical(f"launching game with appid {self.appid} via steam")
        else:
            logs.logger.critical("steam exe not found at the expected location cannot relaunch game")
            
    def re_open_game(self):
        self.close_game()
        time.sleep(10)
        self.launch_game_with_steam()
        recon_utils.template_sleep_no_bounds("join_last_session",0.7,60)
        windows.hwnd = windows.find_window_by_title("ArkAscended") # new process ID as game as relaunced
        
    def crash_rejoin(self):
        if self.detect_crash():
            self.close_game()
            time.sleep(10)
            self.launch_game_with_steam()
            recon_utils.template_sleep_no_bounds("join_last_session",0.7,60)
            windows.hwnd = windows.find_window_by_title("ArkAscended") # new process ID as game as relaunced




