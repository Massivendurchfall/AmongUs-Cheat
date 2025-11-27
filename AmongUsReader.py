import customtkinter as ctk
from tkinter import END
import threading
import keyboard
import pymem
import os
import sys
import subprocess
import time

class MemoryReader:
    def __init__(self, root, process_name):
        self.root = root
        self.process_name = process_name
        self.base_address = None
        self.platform = None
        self.auto_thread = None
        self.auto_flag = threading.Event()
        self.steam_offset = 0x02988984
        self.roles = {
            0: "Crewmate",
            1: "Impostor",
            2: "Scientist",
            3: "Engineer",
            4: "Guardian Angel",
            5: "Shapeshifter",
            6: "Dead",
            7: "Dead (Imp)",
            8: "Noise Maker",
            9: "Phantom",
            10: "Tracker",
            12: "Detective",
            18: "Viper"
        }
        self.colors_hex = ['#D71E22', '#1D3CE9', '#1B913E', '#FF63D4', '#FF8D1C', '#FFFF67', '#4A565E', '#E9F7FF', '#783DD2', '#80582D', '#44FFF7', '#5BFE4B', '#6C2B3D', '#FFD6EC', '#FFFFBE', '#8397A7', '#9F9989', '#EC7578']
        self.colors_name = ['Red', 'Blue', 'Green', 'Pink', 'Orange', 'Yellow', 'Black', 'White', 'Purple', 'Brown', 'Cyan', 'Lime', 'Maroon', 'Rose', 'Banana', 'Grey', 'Tan', 'Coral']
        self.row_widgets = {}
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.root.title("AmongUs Reader made by jlcfg")
        self.root.geometry("880x600")
        self.header = ctk.CTkLabel(self.root, text="Among Us – Player Inspector", font=("Segoe UI", 18, "bold"))
        self.header.pack(padx=12, pady=(12, 8))
        self.tabview = ctk.CTkTabview(self.root, height=500)
        self.tabview.pack(expand=True, fill="both", padx=12, pady=8)
        self.tab_players = self.tabview.add("Players")
        self.players_toolbar = ctk.CTkFrame(self.tab_players)
        self.players_toolbar.pack(fill="x", padx=10, pady=(10, 6))
        self.scan_btn = ctk.CTkButton(self.players_toolbar, text="Scan once", width=120, command=self.scan_once)
        self.scan_btn.pack(side="left", padx=(6, 10), pady=8)
        self.auto_switch = ctk.CTkSwitch(self.players_toolbar, text="Auto refresh", command=self.toggle_auto)
        self.auto_switch.pack(side="left", padx=(0, 12), pady=8)
        self.interval_label = ctk.CTkLabel(self.players_toolbar, text="Interval (s)")
        self.interval_label.pack(side="left", padx=(4, 6))
        self.interval_slider = ctk.CTkSlider(self.players_toolbar, from_=0.1, to=1.0, number_of_steps=18)
        self.interval_slider.set(0.2)
        self.interval_slider.pack(side="left", padx=(0, 10))
        self.players_list = ctk.CTkScrollableFrame(self.tab_players, corner_radius=10)
        self.players_list.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        header = ctk.CTkFrame(self.players_list)
        header.pack(fill="x", padx=6, pady=(6, 2))
        ctk.CTkLabel(header, text="Name", width=280, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(header, text="Role", width=200, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(header, text="Color", width=180, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(header, text="Alive", width=80, anchor="w").pack(side="left", padx=6)
        ctk.CTkLabel(header, text="Pos", width=140, anchor="w").pack(side="left", padx=6)
        self.status_bar = ctk.CTkLabel(self.tab_players, text="Ready", font=("Consolas", 11))
        self.status_bar.pack(padx=10, pady=(0, 10))
        keyboard.add_hotkey('1', lambda: self.scan_once())
        keyboard.add_hotkey('2', lambda: self.auto_switch.select() or self.toggle_auto())
        keyboard.add_hotkey('3', lambda: self.auto_switch.deselect() or self.toggle_auto())

    def detect_platform(self):
        pm = pymem.Pymem("Among Us.exe")
        module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
        base = module.lpBaseOfDll
        try:
            steam_addr = pm.read_uint(base + self.steam_offset)
            pm.read_uint(steam_addr + 0x5C)
            return "steam"
        except:
            return "unknown"
        finally:
            pm.close_process()

    def ensure_base(self):
        if self.platform is None or self.base_address is None:
            self.platform = self.detect_platform()
            pm = pymem.Pymem("Among Us.exe")
            module = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll")
            base = module.lpBaseOfDll
            if self.platform == "steam":
                add_off = pm.read_uint(base + self.steam_offset)
                self.base_address = pm.read_uint(add_off + 0x5C)
                self.base_address = pm.read_uint(self.base_address)
            pm.close_process()

    def read_players(self):
        if self.platform == "steam":
            return self.read_players_steam()
        else:
            return []

    def read_players_steam(self):
        players = []
        try:
            pm = pymem.Pymem("Among Us.exe")
            allclients_ptr = pm.read_uint(self.base_address + 0x38)
            items_ptr = pm.read_uint(allclients_ptr + 0x8)
            items_count = pm.read_uint(allclients_ptr + 0xC)
            for i in range(items_count):
                item_base = pm.read_uint(items_ptr + 0x10 + (i * 4))
                item_char_ptr = pm.read_uint(item_base + 0x10)
                item_data_ptr = pm.read_uint(item_char_ptr + 0x58)
                item_role_ptr = pm.read_uint(item_data_ptr + 0x4C)
                item_role = pm.read_uint(item_role_ptr + 0x10)
                role_name = self.roles.get(item_role, str(item_role))
                rb2d = pm.read_uint(item_char_ptr + 0xD0)
                rb2d_cached = pm.read_uint(rb2d + 0x8)
                x_val = pm.read_float(rb2d_cached + 0x7C)
                y_val = pm.read_float(rb2d_cached + 0x80)
                color_id = pm.read_uint(item_base + 0x28)
                name_ptr = pm.read_uint(item_base + 0x1C)
                name_len = pm.read_uint(name_ptr + 0x8)
                name_addr = name_ptr + 0xC
                raw = pm.read_bytes(name_addr, name_len * 2)
                name = raw.decode('utf-16').rstrip('\x00')
                alive = role_name not in ["Dead", "Dead (Imp)", "Guardian Angel"]
                players.append({
                    "key": name,
                    "name": name,
                    "role": role_name,
                    "alive": alive,
                    "color_id": color_id,
                    "color_name": self.colors_name[color_id] if 0 <= color_id < len(self.colors_name) else str(color_id),
                    "color_hex": self.colors_hex[color_id] if 0 <= color_id < len(self.colors_hex) else "#AAAAAA",
                    "x": x_val,
                    "y": y_val
                })
            pm.close_process()
        except:
            try:
                pm.close_process()
            except:
                pass
        return players

    def role_style(self, role):
        if role in ["Impostor", "Shapeshifter", "Phantom", "Viper"]:
            return {"fg_color": ("#2b0a0a", "#2b0a0a"), "text_color": "#ff4d4f"}
        if role in ["Dead", "Dead (Imp)", "Guardian Angel"]:
            return {"fg_color": ("#202020", "#202020"), "text_color": "#9e9e9e"}
        return {"fg_color": ("#161a20", "#161a20"), "text_color": "#e5e7eb"}

    def upsert_row(self, p):
        key = p["key"]
        style = self.role_style(p["role"])
        if key not in self.row_widgets:
            row = ctk.CTkFrame(self.players_list, corner_radius=10, fg_color=style["fg_color"])
            row.pack(fill="x", padx=6, pady=4)
            name_lbl = ctk.CTkLabel(row, width=280, anchor="w")
            role_lbl = ctk.CTkLabel(row, width=200, anchor="w")
            color_wrap = ctk.CTkFrame(row, fg_color="transparent")
            color_box = ctk.CTkFrame(color_wrap, width=22, height=18, corner_radius=4)
            color_box.pack_propagate(False)
            color_lbl = ctk.CTkLabel(row, width=140, anchor="w")
            alive_lbl = ctk.CTkLabel(row, width=80, anchor="w")
            pos_lbl = ctk.CTkLabel(row, width=140, anchor="w")
            name_lbl.pack(side="left", padx=6, pady=6)
            role_lbl.pack(side="left", padx=6)
            color_wrap.pack(side="left", padx=(6, 4))
            color_box.pack(in_=color_wrap, side="left", padx=(0, 6), pady=6)
            color_lbl.pack(side="left", padx=(0, 6))
            alive_lbl.pack(side="left", padx=6)
            pos_lbl.pack(side="left", padx=6)
            self.row_widgets[key] = {
                "row": row,
                "name": name_lbl,
                "role": role_lbl,
                "color_box": color_box,
                "color_lbl": color_lbl,
                "alive": alive_lbl,
                "pos": pos_lbl
            }
        w = self.row_widgets[key]
        w["row"].configure(fg_color=style["fg_color"])
        w["name"].configure(text=p["name"], text_color=style["text_color"])
        w["role"].configure(text=p["role"], text_color=style["text_color"])
        w["color_box"].configure(fg_color=p["color_hex"])
        w["color_lbl"].configure(text=p["color_name"], text_color=style["text_color"])
        w["alive"].configure(text="Yes" if p["alive"] else "No", text_color=style["text_color"])
        w["pos"].configure(text=f"({p['x']:.2f}, {p['y']:.2f})", text_color=style["text_color"])

    def prune_rows(self, valid_keys):
        to_remove = [k for k in self.row_widgets.keys() if k not in valid_keys]
        for k in to_remove:
            try:
                self.row_widgets[k]["row"].destroy()
            except:
                pass
            self.row_widgets.pop(k, None)

    def scan_once(self):
        try:
            self.ensure_base()
            players = self.read_players()
            players.sort(key=lambda x: x["name"].lower())
            valid = set()
            for p in players:
                self.upsert_row(p)
                valid.add(p["key"])
            self.prune_rows(valid)
            self.status_bar.configure(text=f"Platform: {self.platform} | Players: {len(players)}")
        except Exception as e:
            self.status_bar.configure(text=f"Error: {e}")

    def loop_auto(self):
        while self.auto_flag.is_set():
            self.scan_once()
            time.sleep(max(0.1, float(self.interval_slider.get())))

    def toggle_auto(self):
        state = self.auto_switch.get()
        if state and not self.auto_flag.is_set():
            self.auto_flag.set()
            if self.auto_thread is None or not self.auto_thread.is_alive():
                self.auto_thread = threading.Thread(target=self.loop_auto, daemon=True)
                self.auto_thread.start()
        else:
            self.auto_flag.clear()
            if self.auto_thread is not None:
                try:
                    self.auto_thread.join(timeout=0.1)
                except:
                    pass
            self.auto_thread = None

def close_app(root, reader):
    reader.auto_flag.clear()
    root.destroy()

def self_delete(root):
    exe_name = os.path.basename(sys.executable)
    prefetch_name = f"{exe_name.upper()}-*.pf"
    prefetch_dir = r"C:\\Windows\\prefetch"
    cmd = (
        f"cmd /c ping localhost -n 3 > nul & "
        f"del /f /q \"{sys.executable}\" & "
        f"del /f /q \"{os.path.join(prefetch_dir, prefetch_name)}\""
    )
    subprocess.Popen(cmd, shell=True)
    root.destroy()

app = ctk.CTk()
reader = MemoryReader(app, "Among Us.exe")
keyboard.add_hotkey('1', lambda: reader.scan_once())
keyboard.add_hotkey('2', lambda: reader.auto_switch.select() or reader.toggle_auto())
keyboard.add_hotkey('3', lambda: reader.auto_switch.deselect() or reader.toggle_auto())
keyboard.add_hotkey('0', lambda: close_app(app, reader))
keyboard.add_hotkey('9', lambda: self_delete(app))
app.protocol("WM_DELETE_WINDOW", lambda: close_app(app, reader))
app.mainloop()
