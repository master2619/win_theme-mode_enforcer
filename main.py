#!/usr/bin/env python3
"""
Windows Theme Monitor - Main Application Entry Point
Monitors Windows Light/Dark theme changes and provides persistence mode
"""

import sys
import os
import traceback
from pathlib import Path

# Add the project root to Python path for imports
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    application_path = sys._MEIPASS
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QIcon, QPixmap
import logging

from ui.main_window import ThemeMonitorWindow
from theme_monitor import ThemeMonitor
from service import ThemeService

class ThemeMonitorApp:
    """Main application class handling UI and background service coordination"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running when window is closed

        # Set application properties
        self.app.setApplicationName("Windows Theme Monitor")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("ThemeMonitor")

        # Initialize logging
        self.setup_logging()

        # Initialize components
        self.main_window = None
        self.theme_service = None
        self.tray_icon = None

        # Setup application
        self.setup_tray_icon()
        self.setup_main_window()
        self.setup_theme_service()

    def setup_logging(self):
        """Setup application logging"""
        log_dir = Path.home() / "AppData" / "Roaming" / "ThemeMonitor"
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "app.log"),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("Application starting...")

    def setup_tray_icon(self):
        """Setup system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "Theme Monitor", 
                               "System tray is not available on this system.")
            sys.exit(1)

        # Create tray icon (using a simple icon for now)
        self.tray_icon = QSystemTrayIcon()

        # Set icon (create a simple one if asset doesn't exist)
        try:
            icon_path = Path(application_path) / "assets" / "icon.ico"
            if icon_path.exists():
                self.tray_icon.setIcon(QIcon(str(icon_path)))
            else:
                # Create a simple pixmap icon
                pixmap = QPixmap(16, 16)
                pixmap.fill(Qt.darkGray)
                self.tray_icon.setIcon(QIcon(pixmap))
        except Exception as e:
            self.logger.warning(f"Could not load tray icon: {e}")
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.darkGray)
            self.tray_icon.setIcon(QIcon(pixmap))

        self.tray_icon.setToolTip("Windows Theme Monitor")

        # Connect tray icon signals
        self.tray_icon.activated.connect(self.tray_icon_activated)

        self.tray_icon.show()

    def setup_main_window(self):
        """Setup main application window"""
        try:
            self.main_window = ThemeMonitorWindow()
            self.main_window.show()
        except Exception as e:
            self.logger.error(f"Failed to setup main window: {e}")
            self.logger.error(traceback.format_exc())

    def setup_theme_service(self):
        """Setup background theme monitoring service"""
        try:
            self.theme_service = ThemeService()
            self.theme_service.start()
            self.logger.info("Theme monitoring service started")
        except Exception as e:
            self.logger.error(f"Failed to start theme service: {e}")
            self.logger.error(traceback.format_exc())

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()

    def show_main_window(self):
        """Show the main window"""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def run(self):
        """Run the application"""
        try:
            return self.app.exec()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            self.logger.error(traceback.format_exc())
            return 1
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup application resources"""
        self.logger.info("Cleaning up application...")

        if self.theme_service:
            self.theme_service.stop()

        if self.tray_icon:
            self.tray_icon.hide()

def main():
    """Main entry point"""
    try:
        app = ThemeMonitorApp()
        return app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
