import sys
from config_manager import ConfigManager
from gui_app import GamepadApp

def main():
    print("Initializing Gamepad Utility GUI...")
    config = ConfigManager()
    
    app = GamepadApp(config)
    
    # Catch window close event to ensure threads exit cleanly
    app.protocol("WM_DELETE_WINDOW", app.stop_all)
    
    app.mainloop()

if __name__ == "__main__":
    main()
