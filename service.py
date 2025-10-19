"""
Windows Theme Monitor - Background service wrapper
Provides a service interface for the theme monitoring functionality
"""

import logging
import threading
import winreg
from pathlib import Path
from theme_monitor import ThemeMonitor

class ThemeService:
    """Background service wrapper for theme monitoring"""

    def __init__(self):
        """Initialize the theme service"""
        self.logger = logging.getLogger(__name__)
        self.theme_monitor = ThemeMonitor()
        self.is_running = False
        self.service_thread = None

    def start(self):
        """Start the background service"""
        if self.is_running:
            return

        self.is_running = True
        self.theme_monitor.start_monitoring()
        self.logger.info("Theme service started")

    def stop(self):
        """Stop the background service"""
        if not self.is_running:
            return

        self.is_running = False
        self.theme_monitor.cleanup()
        self.logger.info("Theme service stopped")

    def get_theme_monitor(self) -> ThemeMonitor:
        """Get the underlying theme monitor instance"""
        return self.theme_monitor

    def enable_persistence(self, theme_value: int):
        """Enable theme persistence"""
        self.theme_monitor.enable_persistence(theme_value)

    def disable_persistence(self):
        """Disable theme persistence"""
        self.theme_monitor.disable_persistence()

    def get_current_theme(self):
        """Get current theme state"""
        return self.theme_monitor.get_current_theme()

    def set_theme(self, theme_value: int):
        """Set theme"""
        return self.theme_monitor.set_theme(theme_value)

    def get_logs(self, limit: int = 100):
        """Get theme logs"""
        return self.theme_monitor.get_logs(limit)

    def clear_logs(self):
        """Clear theme logs"""
        return self.theme_monitor.clear_logs()

class StartupManager:
    """Manages Windows startup configuration"""

    STARTUP_REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "WindowsThemeMonitor"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def is_startup_enabled(self) -> bool:
        """Check if application is set to run at startup"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.STARTUP_REGISTRY_PATH) as key:
                winreg.QueryValueEx(key, self.APP_NAME)
                return True
        except FileNotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Error checking startup status: {e}")
            return False

    def enable_startup(self, executable_path: str) -> bool:
        """Enable application to run at Windows startup"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.STARTUP_REGISTRY_PATH,
                               0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, executable_path)

            self.logger.info("Startup enabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable startup: {e}")
            return False

    def disable_startup(self) -> bool:
        """Disable application from running at Windows startup"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.STARTUP_REGISTRY_PATH,
                               0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, self.APP_NAME)

            self.logger.info("Startup disabled")
            return True
        except FileNotFoundError:
            # Already not in startup
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable startup: {e}")
            return False
