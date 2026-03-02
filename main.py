import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess
import sys
import threading
from source.utility.colour_checks import console_output,output_oranage_tp_pixel
SETTINGS_FILE = "json_files/settings.json"

default_settings = {
    "screeen_resolution":"VALUE DOES NOT MATTER",
    "base_path":"VALUE DOES NOT MATTER",
    "lag_offset": 1.0,
    "iguanadon": "GACHAIGUANADON",
    "drop_off": "GACHADEDI",
    "bed_spawn": "GACHARENDER",
    "berry_station": "GACHABERRYSTATION",
    "grindables": "GACHAGRINDABLES",
    "berry_type": "mejoberry",
    "station_yaw": 0,
    "render_pushout": 0,
    "height_ele": 3,
    "height_grind": 3,
    "command_prefix": "%",
    "server_number": "0",
    "singleplayer": False,
    "external_berry": False,
    "crafting": False,
    "seeds_230": False,
    "side_crop_plot":False,
    "y_trap_bot":False,
    "log_channel_gacha": "",
    "log_active_queue": "",
    "log_wait_queue": "",
    "discord_api_key": ""
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(default_settings)
        return default_settings.copy()

    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)


def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)


class SettingsGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Settings Launcher")
        self.root.geometry("1400x800")

        self.process = None
        self.vars = {}

        style = ttk.Style()
        style.theme_use("clam")

        self.root.configure(bg="#2b2b2b")

        style.configure(".", background="#2b2b2b", foreground="white")
        style.configure("TLabel", background="#2b2b2b", foreground="white")
        style.configure("TFrame", background="#2b2b2b")
        style.configure("TButton", background="#3c3f41", foreground="white")
        style.configure("TCheckbutton", background="#2b2b2b", foreground="white")
        style.configure("TEntry",
                        fieldbackground="#3c3f41",
                        foreground="white")

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="ns")

        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

        self.settings = load_settings()

        row = 0
        for key, default_value in default_settings.items():
            ttk.Label(left_frame, text=key).grid(row=row, column=0, sticky="w", pady=2)

            value = self.settings.get(key, default_value)

            if isinstance(default_value, bool):
                var = tk.BooleanVar(value=value)
                ttk.Checkbutton(left_frame, variable=var).grid(row=row, column=1, sticky="w")
            else:
                var = tk.StringVar(value=str(value))
                show = "*" if key == "discord_api_key" else ""
                ttk.Entry(left_frame, textvariable=var, show=show, width=25).grid(row=row, column=1)

            self.vars[key] = var
            row += 1

        ttk.Button(left_frame, text="Save Settings",
                   command=self.save).grid(row=row, column=0, columnspan=2, pady=10)

        row += 1

        ttk.Button(left_frame, text="Start Program",
                   command=self.start_program).grid(row=row, column=0, columnspan=2, pady=5)

        row += 1

        ttk.Button(left_frame, text="Stop Program",
                   command=self.stop_program).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        ttk.Button(left_frame, text="Test console Colours",
                   command=self.check_colours).grid(row=row, column=0, columnspan=2, pady=5)

        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            right_frame,
            bg="#1e1e1e",
            fg="white",
            insertbackground="white",
            wrap="word"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(right_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.log_text.config(yscrollcommand=scrollbar.set)

  
    def save(self):
        new_data = {}

        try:
            for key, var in self.vars.items():
                value = var.get()
                default_value = default_settings[key]

                if isinstance(default_value, bool):
                    new_data[key] = var.get()
                elif isinstance(default_value, int):
                    new_data[key] = int(value)
                elif isinstance(default_value, float):
                    new_data[key] = float(value)
                else:
                    new_data[key] = value

            save_settings(new_data)
            messagebox.showinfo("Success", "Settings saved successfully!")

        except ValueError:
            messagebox.showerror("Error", "Invalid number format.")

    
    def start_program(self):
        if self.process and self.process.poll() is None:
            messagebox.showinfo("Info", "Program already running.")
            return

        try:
            self.process = subprocess.Popen(
                [sys.executable, "-u", "main_program.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            threading.Thread(target=self.read_output, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", str(e))

 
    def stop_program(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None
            messagebox.showinfo("Stopped","Program Terminated")
        else:
            messagebox.showinfo("Info","no running program ")

    def read_output(self):
        for line in self.process.stdout:
            self.log_text.after(0, self.append_log, line)

    def append_log(self, text):
        self.log_text.insert("end", text)
        self.log_text.see("end")

    def check_colours(self):
        self.append_log(f"the average console colour was :{console_output.output_mean_colour()} go to console.json and set +and - 5 from this in the respected section IE upperbound = average+5\n")
        #self.append_log(f"{output_oranage_tp_pixel.get_orange_pixel()} -> these colours should be put into xxxxxx location in xxxx file ")

if __name__ == "__main__":
    root = tk.Tk()
    app = SettingsGUI(root)
    root.mainloop()