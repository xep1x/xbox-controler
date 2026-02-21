import json
import os
import sys

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "mouse": {
        "sensitivity": 20.0,
        "acceleration_curve": 2.5,  # Exponent for non-linear acceleration. 1 is linear.
        "update_rate_hz": 120
    },
    "deadzones": {
        "left_stick": 0.15,
        "right_stick": 0.15,
        "triggers": 0.1
    },
    "scroll": {
        "speed": 1.0,
        "acceleration_curve": 1.5
    },
    "bindings": {
        "A": "mouse_left",
        "B": "mouse_right",
        "X": "osk",
        "Y": "enter",
        "LB": "browser_back",
        "RB": "browser_forward",
        "LT": "zoom_out",
        "RT": "zoom_in",
        "DPAD_UP": "volume_up",
        "DPAD_DOWN": "volume_down",
        "DPAD_LEFT": "media_prev",
        "DPAD_RIGHT": "media_next",
        "START": "media_play_pause",
        "BACK": "win_d",
        "L3": "mouse_middle",
        "R3": "close_tab"
    }
}

class ConfigManager:
    def __init__(self, filepath=CONFIG_FILE):
        self.filepath = self._get_absolute_path(filepath)
        self.config = self.load()

    def _get_absolute_path(self, filepath):
        if not os.path.isabs(filepath):
            # Resolve relative to the executable or script
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_dir, filepath)
        return filepath

    def load(self):
        if not os.path.exists(self.filepath):
            self.save(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # Recursive update to ensure all default keys exist
                updated = False
                for section, values in DEFAULT_CONFIG.items():
                    if section not in config:
                        config[section] = values
                        updated = True
                    elif isinstance(values, dict):
                        for k, v in values.items():
                            if k not in config[section]:
                                config[section][k] = v
                                updated = True
                if updated:
                    self.save(config)
                    
                return config
        except Exception as e:
            print(f"Error loading {self.filepath}: {e}")
            return DEFAULT_CONFIG.copy()

    def save(self, config_data):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"Error saving {self.filepath}: {e}")

    def get_mouse_sensitivity(self):
        return self.config['mouse']['sensitivity']

    def get_mouse_acceleration_curve(self):
        return self.config['mouse']['acceleration_curve']
        
    def get_update_rate(self):
        return self.config['mouse']['update_rate_hz']

    def get_deadzone(self, stick_or_trigger):
        return self.config['deadzones'].get(stick_or_trigger, 0.15)
        
    def get_binding(self, button_name):
        return self.config['bindings'].get(button_name)

    def update_setting(self, category, key, value):
        if category in self.config and key in self.config[category]:
            self.config[category][key] = value
            self.save(self.config)
            
    def update_binding(self, button, action):
        if button in self.config['bindings']:
            self.config['bindings'][button] = action
            self.save(self.config)
