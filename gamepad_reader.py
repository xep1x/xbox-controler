import threading
import time
import XInput
from mouse_keyboard_sim import SystemSimulator

class GamepadReader:
    def __init__(self, config_manager, simulator: SystemSimulator):
        self.config = config_manager
        self.simulator = simulator
        self.running = False
        self.paused = False
        self.thread = None
        self.controller_id = 0

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def _apply_deadzone(self, value, deadzone):
        if abs(value) < deadzone:
            return 0.0
        # Normalize to 0.0 - 1.0 outside of deadzone
        sign = 1 if value >= 0 else -1
        normalized = (abs(value) - deadzone) / (1.0 - deadzone)
        return sign * normalized

    def _handle_button_event(self, button_name, is_pressed):
        # We check mapping from config
        binding = self.config.get_binding(button_name)
        if not binding:
            return

        if binding.startswith('mouse_'):
            # It's a mouse click
            btn = binding.split('_')[1] # left, right, middle
            self.simulator.set_mouse_button(btn, is_pressed)
        else:
            # It's a keyboard/system action. Trigger on press.
            self.simulator.trigger_action(binding, is_pressed)

    def _loop(self):
        update_rate = self.config.get_update_rate()
        sleep_time = 1.0 / update_rate if update_rate > 0 else 0.01

        # Keep track of button states to trigger on change
        button_states = {
            'A': False, 'B': False, 'X': False, 'Y': False,
            'LB': False, 'RB': False, 'START': False, 'BACK': False,
            'L3': False, 'R3': False,
            'DPAD_UP': False, 'DPAD_DOWN': False, 'DPAD_LEFT': False, 'DPAD_RIGHT': False,
            'LT': False, 'RT': False
        }

        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            connected = XInput.get_connected()
            if not connected[self.controller_id]:
                # Find first connected controller
                found = False
                for i in range(4):
                    if connected[i]:
                        self.controller_id = i
                        found = True
                        break
                
                if not found:
                    time.sleep(1.0) # Wait for hot-reconnect
                    continue

            try:
                state = XInput.get_state(self.controller_id)
                
                # Get sticks
                lx, ly = XInput.get_thumb_values(state)[0] # Left stick
                rx, ry = XInput.get_thumb_values(state)[1] # Right stick
                
                # Apply deadzones
                ls_deadzone = self.config.get_deadzone('left_stick')
                rs_deadzone = self.config.get_deadzone('right_stick')

                lx = self._apply_deadzone(lx, ls_deadzone)
                ly = self._apply_deadzone(ly, ls_deadzone)
                rx = self._apply_deadzone(rx, rs_deadzone)
                ry = self._apply_deadzone(ry, rs_deadzone)

                # Move mouse and scroll
                self.simulator.move_mouse(lx, ly)
                self.simulator.scroll(rx, ry)

                # Process buttons
                buttons = XInput.get_button_values(state)
                # Map XInput buttons to our config names
                current_states = {
                    'A': buttons.get('A', False),
                    'B': buttons.get('B', False),
                    'X': buttons.get('X', False),
                    'Y': buttons.get('Y', False),
                    'LB': buttons.get('LEFT_SHOULDER', False),
                    'RB': buttons.get('RIGHT_SHOULDER', False),
                    'START': buttons.get('START', False),
                    'BACK': buttons.get('BACK', False),
                    'L3': buttons.get('LEFT_THUMB', False),
                    'R3': buttons.get('RIGHT_THUMB', False),
                    'DPAD_UP': buttons.get('DPAD_UP', False),
                    'DPAD_DOWN': buttons.get('DPAD_DOWN', False),
                    'DPAD_LEFT': buttons.get('DPAD_LEFT', False),
                    'DPAD_RIGHT': buttons.get('DPAD_RIGHT', False),
                }

                # Treat triggers as buttons based on deadzone
                trigger_values = XInput.get_trigger_values(state)
                trigger_dz = self.config.get_deadzone('triggers')
                current_states['LT'] = trigger_values[0] > trigger_dz
                current_states['RT'] = trigger_values[1] > trigger_dz

                # Check for changes and handle events
                for btn, state in current_states.items():
                    if state != button_states[btn]:
                        self._handle_button_event(btn, state)
                        button_states[btn] = state

                time.sleep(sleep_time)
                
            except XInput.XInputError:
                # Controller disconnected mid-poll
                time.sleep(1.0)
            except Exception as e:
                print(f"Error in gamepad reader loop: {e}")
                time.sleep(1.0)
