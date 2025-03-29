import ctypes
import time
from datetime import datetime

class DesktopNotifier:
    def __init__(self, config):
        self.config = config
        self.last_notification_time = 0
        
    def show_notification(self, title, message):
        current_time = time.time()
        if current_time - self.last_notification_time >= self.config['notification_cooldown']:
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1)
            self.last_notification_time = current_time
            return True
        return False
    
    def log_event(self, event_type, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {event_type}: {message}\n"
        with open(self.config['log_file'], 'a') as f:
            f.write(log_entry)