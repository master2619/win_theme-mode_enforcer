"""
Windows Theme Monitor - Core theme monitoring and persistence functionality
Handles registry monitoring, change detection, and theme persistence
"""

import winreg
import sqlite3
import time
import logging
import psutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import ctypes
from ctypes import wintypes

class ThemeMonitor:
    """Core theme monitoring class handling registry changes and persistence"""

    # Registry paths and keys
    THEME_REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    APPS_USE_LIGHT_THEME = "AppsUseLightTheme"
    SYSTEM_USES_LIGHT_THEME = "SystemUsesLightTheme"

    # Theme values
    LIGHT_THEME = 1
    DARK_THEME = 0

    # Windows constants for broadcasting changes
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A
    SMTO_ABORTIFHUNG = 0x0002

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the theme monitor"""
        self.logger = logging.getLogger(__name__)

        # Setup database
        if db_path is None:
            app_data = Path.home() / "AppData" / "Roaming" / "ThemeMonitor"
            app_data.mkdir(parents=True, exist_ok=True)
            db_path = app_data / "logs.db"

        self.db_path = str(db_path)
        self.setup_database()

        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self.persistence_enabled = False
        self.persistence_theme = self.DARK_THEME
        self.persistence_thread = None
        self.stop_event = threading.Event()

        # Cache current theme state
        self.current_theme = self.get_current_theme()

    def setup_database(self):
        """Setup SQLite database for logging"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS theme_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    theme_mode TEXT NOT NULL,
                    source_process TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            self.logger.error(f"Failed to setup database: {e}")
            raise

    def get_current_theme(self) -> Dict[str, int]:
        """Get current theme state from registry"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.THEME_REGISTRY_PATH) as key:
                apps_theme = winreg.QueryValueEx(key, self.APPS_USE_LIGHT_THEME)[0]
                system_theme = winreg.QueryValueEx(key, self.SYSTEM_USES_LIGHT_THEME)[0]

                return {
                    'apps': apps_theme,
                    'system': system_theme
                }
        except Exception as e:
            self.logger.error(f"Failed to read theme from registry: {e}")
            return {'apps': self.DARK_THEME, 'system': self.DARK_THEME}

    def set_theme(self, theme_value: int, broadcast: bool = True):
        """Set theme in registry and optionally broadcast change"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.THEME_REGISTRY_PATH, 
                               0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, self.APPS_USE_LIGHT_THEME, 0, 
                                winreg.REG_DWORD, theme_value)
                winreg.SetValueEx(key, self.SYSTEM_USES_LIGHT_THEME, 0, 
                                winreg.REG_DWORD, theme_value)

            if broadcast:
                self.broadcast_theme_change()

            self.logger.info(f"Theme set to {'Light' if theme_value else 'Dark'}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to set theme: {e}")
            return False

    def broadcast_theme_change(self):
        """Broadcast theme change to all windows"""
        try:
            user32 = ctypes.windll.user32
            result = user32.SendMessageTimeoutW(
                self.HWND_BROADCAST,
                self.WM_SETTINGCHANGE,
                0,
                "ImmersiveColorSet",
                self.SMTO_ABORTIFHUNG,
                5000,
                None
            )
            self.logger.debug(f"Broadcast result: {result}")
        except Exception as e:
            self.logger.error(f"Failed to broadcast theme change: {e}")

    def detect_source_process(self) -> str:
        """Attempt to detect which process triggered the theme change"""
        try:
            # This is a simplified approach - in reality, detecting the exact
            # process that modified registry is complex and may require ETW
            current_process = psutil.Process()

            # Check for common processes that might change themes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info['name'].lower()
                    if name in ['systemsettings.exe', 'winlogon.exe', 'explorer.exe']:
                        return proc.info['name']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return "unknown"

        except Exception as e:
            self.logger.error(f"Failed to detect source process: {e}")
            return "unknown"

    def log_theme_change(self, old_theme: Dict[str, int], new_theme: Dict[str, int], 
                        source_process: str = "unknown"):
        """Log theme change to database"""
        try:
            theme_mode = "Light" if new_theme['apps'] else "Dark"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            details = f"Apps: {old_theme['apps']} -> {new_theme['apps']}, "
            details += f"System: {old_theme['system']} -> {new_theme['system']}"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO theme_logs (timestamp, theme_mode, source_process, details)
                VALUES (?, ?, ?, ?)
            """, (timestamp, theme_mode, source_process, details))

            conn.commit()
            conn.close()

            self.logger.info(f"Logged theme change: {theme_mode} by {source_process}")

        except Exception as e:
            self.logger.error(f"Failed to log theme change: {e}")

    def start_monitoring(self):
        """Start monitoring theme changes"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Theme monitoring started")

    def stop_monitoring(self):
        """Stop monitoring theme changes"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.stop_event.set()

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self.logger.info("Theme monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring and not self.stop_event.is_set():
            try:
                new_theme = self.get_current_theme()

                # Check if theme changed
                if new_theme != self.current_theme:
                    source_process = self.detect_source_process()
                    self.log_theme_change(self.current_theme, new_theme, source_process)
                    self.current_theme = new_theme

                # Sleep for a short interval
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait longer on error

    def enable_persistence(self, theme_value: int):
        """Enable theme persistence mode"""
        self.persistence_enabled = True
        self.persistence_theme = theme_value

        if self.persistence_thread is None or not self.persistence_thread.is_alive():
            self.persistence_thread = threading.Thread(target=self._persistence_loop, daemon=True)
            self.persistence_thread.start()

        self.logger.info(f"Persistence enabled for {'Light' if theme_value else 'Dark'} theme")

    def disable_persistence(self):
        """Disable theme persistence mode"""
        self.persistence_enabled = False
        self.logger.info("Persistence disabled")

    def _persistence_loop(self):
        """Persistence enforcement loop"""
        while not self.stop_event.is_set():
            if self.persistence_enabled:
                try:
                    current = self.get_current_theme()

                    # Check if theme needs to be reset
                    if (current['apps'] != self.persistence_theme or 
                        current['system'] != self.persistence_theme):

                        self.set_theme(self.persistence_theme, broadcast=True)
                        self.log_theme_change(
                            current,
                            {'apps': self.persistence_theme, 'system': self.persistence_theme},
                            "ThemeMonitor (Persistence)"
                        )

                except Exception as e:
                    self.logger.error(f"Error in persistence loop: {e}")

            time.sleep(0.5)  # Check every 500ms as specified

    def get_logs(self, limit: int = 100) -> list:
        """Get theme change logs from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT timestamp, theme_mode, source_process, details
                FROM theme_logs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            logs = cursor.fetchall()
            conn.close()

            return logs

        except Exception as e:
            self.logger.error(f"Failed to get logs: {e}")
            return []

    def clear_logs(self):
        """Clear all logs from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM theme_logs")
            conn.commit()
            conn.close()
            self.logger.info("Logs cleared")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear logs: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        self.disable_persistence()
        self.stop_event.set()
