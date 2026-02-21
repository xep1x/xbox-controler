import threading
import time
from pynput.mouse import Controller as MouseController, Button as MouseButton
from pynput.keyboard import Controller as KeyboardController, Key

class SystemSimulator:
    def __init__(self, config_manager):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.config = config_manager

        # Mouse state
        self.mouse_left_down = False
        self.mouse_right_down = False
        self.mouse_middle_down = False

    def move_mouse(self, x, y):
        if x == 0 and y == 0:
            return

        sensitivity = self.config.get_mouse_sensitivity()
        
        # Определение направления
        sign_x = 1 if x > 0 else -1 if x < 0 else 0
        sign_y = 1 if y > 0 else -1 if y < 0 else 0
        
        # Статичное перемещение (скорость не зависит от силы наклона, главное - выход из мертвой зоны)
        move_x = sign_x * sensitivity if x != 0 else 0
        
        # Инвертируем Y, так как у стика Y направлен вверх, а на экране Y направлен вниз
        move_y = sign_y * sensitivity * -1 if y != 0 else 0
        
        if move_x != 0 or move_y != 0:
            self.mouse.move(move_x, move_y)

    def scroll(self, dx, dy):
        if dx == 0 and dy == 0:
            return
            
        curve = self.config.config['scroll'].get('acceleration_curve', 1.5)
        speed = self.config.config['scroll'].get('speed', 1.0)

        sign_dx = 1 if dx > 0 else -1
        sign_dy = 1 if dy > 0 else -1
        
        scroll_x = sign_dx * (abs(dx) ** curve) * speed
        scroll_y = sign_dy * (abs(dy) ** curve) * speed
        
        # self.mouse.scroll(dx, dy) where dx is horizontal, dy is vertical
        self.mouse.scroll(scroll_x, scroll_y)

    def set_mouse_button(self, button, is_pressed):
        mb = None
        if button == 'left':
            mb = MouseButton.left
            state_prop = 'mouse_left_down'
        elif button == 'right':
            mb = MouseButton.right
            state_prop = 'mouse_right_down'
        elif button == 'middle':
            mb = MouseButton.middle
            state_prop = 'mouse_middle_down'
        else:
            return

        current_state = getattr(self, state_prop)
        
        if is_pressed and not current_state:
            self.mouse.press(mb)
            setattr(self, state_prop, True)
        elif not is_pressed and current_state:
            self.mouse.release(mb)
            setattr(self, state_prop, False)

    def trigger_action(self, action_name, is_pressed):
        """Handle actions like osk, enter, media control based on binding name."""
        # Most of these actions are fire-and-forget on press. Some might need hold.
        if not is_pressed:
            return  # Only trigger on press for these single actions unless it's a modifier

        if action_name == 'osk':
            import subprocess
            try:
                # subprocess.Popen не блокирует выполнение, в отличие от os.system
                # При запуске напрямую может возникнуть "Could not start On-Screen Keyboard", поэтому используем cmd /c
                subprocess.Popen('cmd /c osk', creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                print(f"Failed to launch OSK: {e}")
        elif action_name == 'enter':
            self.keyboard.tap(Key.enter)
        elif action_name == 'browser_back':
            # Alt+Left Arrow or dedicated back button (often mouse button x1)
            # pynput keyboard.tap might not have it, let's use alt+left
            with self.keyboard.pressed(Key.alt):
                self.keyboard.tap(Key.left)
        elif action_name == 'browser_forward':
            with self.keyboard.pressed(Key.alt):
                self.keyboard.tap(Key.right)
        elif action_name == 'zoom_in':
            with self.keyboard.pressed(Key.ctrl):
                self.mouse.scroll(0, 1)
        elif action_name == 'zoom_out':
            with self.keyboard.pressed(Key.ctrl):
                self.mouse.scroll(0, -1)
        elif action_name == 'volume_up':
            self.keyboard.tap(Key.media_volume_up)
        elif action_name == 'volume_down':
            self.keyboard.tap(Key.media_volume_down)
        elif action_name == 'media_prev':
            self.keyboard.tap(Key.media_previous)
        elif action_name == 'media_next':
            self.keyboard.tap(Key.media_next)
        elif action_name == 'media_play_pause':
            self.keyboard.tap(Key.media_play_pause)
        elif action_name == 'win_d':
            with self.keyboard.pressed(Key.cmd):
                self.keyboard.tap('d')
        elif action_name == 'close_tab':
            with self.keyboard.pressed(Key.ctrl):
                self.keyboard.tap('w')
        # Additional actions can be added here
