import customtkinter as ctk
import threading
from gamepad_reader import GamepadReader
from mouse_keyboard_sim import SystemSimulator

# Настройки темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

class GamepadApp(ctk.CTk):
    def __init__(self, config_manager):
        super().__init__()

        self.config_manager = config_manager
        
        # Инструменты управления системой
        self.simulator = SystemSimulator(self.config_manager)
        self.reader = GamepadReader(self.config_manager, self.simulator)

        self.title("Xbox Gamepad Utility")
        self.geometry("600x700")

        # Настраиваем сетку
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Верхний фрейм с кнопкой Start/Stop
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.status_label = ctk.CTkLabel(self.top_frame, text="Status: Stopped", font=ctk.CTkFont(size=18, weight="bold"), text_color="grey")
        self.status_label.pack(side="left", padx=10)

        self.toggle_btn = ctk.CTkButton(self.top_frame, text="START", font=ctk.CTkFont(size=16, weight="bold"), width=150, height=40, fg_color="#2FA572", hover_color="#106A43", command=self.toggle_reader)
        self.toggle_btn.pack(side="right", padx=10)

        # 2. Фрейм с настройками (со скроллом)
        self.settings_frame = ScrollableFrame(self)
        self.settings_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        self._build_settings_ui()

    def _build_settings_ui(self):
        # Настройки мыши (Sensitivity)
        ctk.CTkLabel(self.settings_frame, text="Mouse Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(10, 5), padx=10)
        
        self._create_slider("Sensitivity", "mouse", "sensitivity", 1, 50)
        self._create_slider("Update Rate (Hz)", "mouse", "update_rate_hz", 30, 240)

        # Мертвые зоны
        ctk.CTkLabel(self.settings_frame, text="Deadzones", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 5), padx=10)
        self._create_slider("Left Stick", "deadzones", "left_stick", 0.01, 0.5, resolution=0.01)
        self._create_slider("Right Stick", "deadzones", "right_stick", 0.01, 0.5, resolution=0.01)
        self._create_slider("Triggers", "deadzones", "triggers", 0.01, 0.5, resolution=0.01)

        # Раскладка кнопок (Bindings)
        ctk.CTkLabel(self.settings_frame, text="Button Bindings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 5), padx=10)
        
        # Доступные действия (actions)
        actions = ["mouse_left", "mouse_right", "mouse_middle", "osk", "enter", 
                   "browser_back", "browser_forward", "zoom_in", "zoom_out", 
                   "volume_up", "volume_down", "media_prev", "media_next", 
                   "media_play_pause", "win_d", "close_tab"]

        for btn in self.config_manager.config['bindings']:
            frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(frame, text=btn, width=100, anchor="w").pack(side="left")
            
            current_action = self.config_manager.config['bindings'][btn]
            combobox = ctk.CTkComboBox(frame, values=actions, width=200)
            combobox.set(current_action)
            combobox.pack(side="right")
            
            # Привязываем изменение
            combobox.configure(command=lambda val, b=btn: self.config_manager.update_binding(b, val))

    def _create_slider(self, text, category, key, min_val, max_val, resolution=1):
        frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        
        current_val = self.config_manager.config[category][key]
        
        label = ctk.CTkLabel(frame, text=f"{text}: {current_val}", width=150, anchor="w")
        label.pack(side="left")
        
        slider = ctk.CTkSlider(frame, from_=min_val, to=max_val, number_of_steps=int((max_val-min_val)/resolution))
        slider.set(current_val)
        slider.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        def on_change(value):
            val = round(value, 2) if resolution < 1 else int(value)
            label.configure(text=f"{text}: {val}")
            self.config_manager.update_setting(category, key, val)
            
        slider.configure(command=on_change)

    def toggle_reader(self):
        if not self.reader.running:
            # Start
            self.reader.start()
            self.status_label.configure(text="Status: Running", text_color="#2FA572")
            self.toggle_btn.configure(text="STOP", fg_color="#C23B22", hover_color="#8F2C1A")
        else:
            # Stop
            self.reader.stop()
            self.status_label.configure(text="Status: Stopped", text_color="grey")
            self.toggle_btn.configure(text="START", fg_color="#2FA572", hover_color="#106A43")

    def stop_all(self):
        if self.reader.running:
            self.reader.stop()
        self.destroy()
