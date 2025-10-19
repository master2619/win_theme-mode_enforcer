"""
Windows Theme Monitor - Main UI Window
PySide6-based modern UI with tabbed interface
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QPushButton, QRadioButton,
                              QCheckBox, QTableWidget, QTableWidgetItem, 
                              QGroupBox, QButtonGroup, QMessageBox, QHeaderView,
                              QApplication, QSystemTrayIcon, QMenu, QSplitter)
from PySide6.QtCore import QTimer, Signal, QThread, Qt
from PySide6.QtGui import QIcon, QFont, QPixmap, QAction

from service import ThemeService, StartupManager
from theme_monitor import ThemeMonitor

class LogUpdateThread(QThread):
    """Thread for updating logs without blocking UI"""
    logs_updated = Signal(list)

    def __init__(self, theme_service):
        super().__init__()
        self.theme_service = theme_service
        self.running = True

    def run(self):
        while self.running:
            try:
                logs = self.theme_service.get_logs(100)
                self.logs_updated.emit(logs)
                self.msleep(2000)  # Update every 2 seconds
            except Exception as e:
                logging.getLogger(__name__).error(f"Error updating logs: {e}")
                self.msleep(5000)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class ThemeMonitorWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Initialize services
        self.theme_service = ThemeService()
        self.startup_manager = StartupManager()

        # UI state
        self.persistence_enabled = False
        self.current_theme_mode = "Dark"

        # Background thread for log updates
        self.log_thread = None

        # Setup UI
        self.setup_ui()
        self.setup_tray_menu()
        self.setup_timers()
        self.update_theme_status()

        # Start background log updates
        self.start_log_updates()

    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("Windows Theme Monitor")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        # Central widget with tabs
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        # Create tabs
        self.create_dashboard_tab()
        self.create_logs_tab()
        self.create_settings_tab()

        # Apply modern styling
        self.apply_modern_style()

    def create_dashboard_tab(self):
        """Create the dashboard tab"""
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Theme Monitor Dashboard")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Current theme status
        self.theme_status_group = QGroupBox("Current Theme Status")
        theme_layout = QVBoxLayout(self.theme_status_group)

        self.current_theme_label = QLabel("🌙 Dark Mode")
        self.current_theme_label.setFont(QFont("Arial", 14))
        self.current_theme_label.setAlignment(Qt.AlignCenter)
        theme_layout.addWidget(self.current_theme_label)

        layout.addWidget(self.theme_status_group)

        # Persistence control
        self.persistence_group = QGroupBox("Theme Persistence")
        persistence_layout = QVBoxLayout(self.persistence_group)

        self.persistence_checkbox = QCheckBox("Enable Theme Persistence")
        self.persistence_checkbox.toggled.connect(self.toggle_persistence)
        persistence_layout.addWidget(self.persistence_checkbox)

        # Theme selection for persistence
        theme_selection_layout = QHBoxLayout()
        self.light_theme_radio = QRadioButton("☀️ Light Theme")
        self.dark_theme_radio = QRadioButton("🌙 Dark Theme")
        self.dark_theme_radio.setChecked(True)  # Default to dark

        self.theme_group = QButtonGroup()
        self.theme_group.addButton(self.light_theme_radio, 1)
        self.theme_group.addButton(self.dark_theme_radio, 0)

        theme_selection_layout.addWidget(self.light_theme_radio)
        theme_selection_layout.addWidget(self.dark_theme_radio)
        persistence_layout.addLayout(theme_selection_layout)

        # Initially disable theme selection
        self.light_theme_radio.setEnabled(False)
        self.dark_theme_radio.setEnabled(False)

        layout.addWidget(self.persistence_group)

        # Manual theme control
        manual_group = QGroupBox("Manual Theme Control")
        manual_layout = QHBoxLayout(manual_group)

        self.set_light_btn = QPushButton("Set Light Theme")
        self.set_dark_btn = QPushButton("Set Dark Theme")

        self.set_light_btn.clicked.connect(lambda: self.set_theme_manually(1))
        self.set_dark_btn.clicked.connect(lambda: self.set_theme_manually(0))

        manual_layout.addWidget(self.set_light_btn)
        manual_layout.addWidget(self.set_dark_btn)
        layout.addWidget(manual_group)

        # Status information
        self.status_label = QLabel("Monitoring active")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.central_widget.addTab(dashboard, "Dashboard")

    def create_logs_tab(self):
        """Create the logs tab"""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Theme Change Logs")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title)

        # Refresh and export buttons
        header_layout.addStretch()
        self.refresh_logs_btn = QPushButton("Refresh")
        self.export_logs_btn = QPushButton("Export Logs")

        self.refresh_logs_btn.clicked.connect(self.refresh_logs)
        self.export_logs_btn.clicked.connect(self.export_logs)

        header_layout.addWidget(self.refresh_logs_btn)
        header_layout.addWidget(self.export_logs_btn)
        layout.addLayout(header_layout)

        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(4)
        self.logs_table.setHorizontalHeaderLabels(["Timestamp", "Theme Mode", "Source Process", "Details"])

        # Configure table
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSortingEnabled(True)

        layout.addWidget(self.logs_table)

        self.central_widget.addTab(logs_widget, "Logs")

    def create_settings_tab(self):
        """Create the settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # Startup settings
        startup_group = QGroupBox("Startup Settings")
        startup_layout = QVBoxLayout(startup_group)

        self.startup_checkbox = QCheckBox("Run at Windows startup")
        self.startup_checkbox.toggled.connect(self.toggle_startup)
        startup_layout.addWidget(self.startup_checkbox)

        # Check current startup status
        if self.startup_manager.is_startup_enabled():
            self.startup_checkbox.setChecked(True)

        layout.addWidget(startup_group)

        # Monitoring settings
        monitoring_group = QGroupBox("Monitoring Settings")
        monitoring_layout = QVBoxLayout(monitoring_group)

        self.monitoring_status_label = QLabel("Status: Active")
        monitoring_layout.addWidget(self.monitoring_status_label)

        layout.addWidget(monitoring_group)

        # Log management
        logs_group = QGroupBox("Log Management")
        logs_layout = QVBoxLayout(logs_group)

        log_info = QLabel("Logs are stored in your user AppData folder")
        log_info.setWordWrap(True)
        logs_layout.addWidget(log_info)

        self.clear_logs_btn = QPushButton("Clear All Logs")
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        logs_layout.addWidget(self.clear_logs_btn)

        layout.addWidget(logs_group)

        # About section
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout(about_group)

        about_text = QLabel("Windows Theme Monitor v1.0\nMonitors and controls Windows Light/Dark theme changes")
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)

        layout.addWidget(about_group)

        layout.addStretch()

        self.central_widget.addTab(settings_widget, "Settings")

    def setup_tray_menu(self):
        """Setup system tray menu"""
        # This will be handled by the main app class
        pass

    def setup_timers(self):
        """Setup update timers"""
        # Timer for updating theme status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_theme_status)
        self.status_timer.start(2000)  # Update every 2 seconds

    def apply_modern_style(self):
        """Apply modern styling to the application"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }

        QTabWidget::pane {
            border: 1px solid #d0d0d0;
            background-color: white;
        }

        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }

        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 1px solid white;
        }

        QGroupBox {
            font-weight: bold;
            border: 2px solid #d0d0d0;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }

        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #106ebe;
        }

        QPushButton:pressed {
            background-color: #005a9e;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }

        QRadioButton::indicator {
            width: 18px;
            height: 18px;
        }

        QTableWidget {
            gridline-color: #d0d0d0;
            background-color: white;
            alternate-background-color: #f9f9f9;
        }

        QTableWidget::item {
            padding: 4px;
        }
        """

        self.setStyleSheet(style)

    def toggle_persistence(self, enabled):
        """Toggle theme persistence mode"""
        self.persistence_enabled = enabled

        # Enable/disable theme selection
        self.light_theme_radio.setEnabled(enabled)
        self.dark_theme_radio.setEnabled(enabled)

        if enabled:
            # Get selected theme
            theme_value = self.theme_group.checkedId()
            if theme_value == -1:  # No selection
                theme_value = 0  # Default to dark

            self.theme_service.enable_persistence(theme_value)
            self.status_label.setText("Persistence enabled - Theme will be enforced")
        else:
            self.theme_service.disable_persistence()
            self.status_label.setText("Monitoring active")

    def set_theme_manually(self, theme_value):
        """Set theme manually"""
        success = self.theme_service.set_theme(theme_value)
        if success:
            theme_name = "Light" if theme_value else "Dark"
            QMessageBox.information(self, "Theme Changed", f"Theme set to {theme_name}")
        else:
            QMessageBox.warning(self, "Error", "Failed to change theme")

    def update_theme_status(self):
        """Update the current theme status display"""
        try:
            current_theme = self.theme_service.get_current_theme()
            if current_theme['apps'] == 1:
                self.current_theme_label.setText("☀️ Light Mode")
                self.current_theme_mode = "Light"
            else:
                self.current_theme_label.setText("🌙 Dark Mode")
                self.current_theme_mode = "Dark"
        except Exception as e:
            self.logger.error(f"Error updating theme status: {e}")

    def start_log_updates(self):
        """Start background log updates"""
        if self.log_thread is None or not self.log_thread.isRunning():
            self.log_thread = LogUpdateThread(self.theme_service)
            self.log_thread.logs_updated.connect(self.update_logs_table)
            self.log_thread.start()

    def update_logs_table(self, logs):
        """Update the logs table with new data"""
        try:
            self.logs_table.setRowCount(len(logs))

            for row, log_entry in enumerate(logs):
                timestamp, theme_mode, source_process, details = log_entry

                self.logs_table.setItem(row, 0, QTableWidgetItem(timestamp))
                self.logs_table.setItem(row, 1, QTableWidgetItem(theme_mode))
                self.logs_table.setItem(row, 2, QTableWidgetItem(source_process))
                self.logs_table.setItem(row, 3, QTableWidgetItem(details))

        except Exception as e:
            self.logger.error(f"Error updating logs table: {e}")

    def refresh_logs(self):
        """Manually refresh logs"""
        try:
            logs = self.theme_service.get_logs(100)
            self.update_logs_table(logs)
        except Exception as e:
            self.logger.error(f"Error refreshing logs: {e}")
            QMessageBox.warning(self, "Error", "Failed to refresh logs")

    def export_logs(self):
        """Export logs to CSV file"""
        try:
            logs = self.theme_service.get_logs(1000)  # Get more logs for export

            if not logs:
                QMessageBox.information(self, "Export", "No logs to export")
                return

            # Create CSV content
            csv_content = "Timestamp,Theme Mode,Source Process,Details\n"
            for log in logs:
                csv_content += f"{log[0]},{log[1]},{log[2]},\"{log[3]}\"\n"

            # Save to desktop
            desktop = Path.home() / "Desktop"
            filename = desktop / f"theme_monitor_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(csv_content)

            QMessageBox.information(self, "Export Complete", f"Logs exported to:\n{filename}")

        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            QMessageBox.warning(self, "Export Error", "Failed to export logs")

    def toggle_startup(self, enabled):
        """Toggle Windows startup"""
        try:
            if enabled:
                # Get current executable path
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = sys.executable + ' "' + __file__ + '"'

                success = self.startup_manager.enable_startup(exe_path)
            else:
                success = self.startup_manager.disable_startup()

            if not success:
                # Reset checkbox if operation failed
                self.startup_checkbox.setChecked(not enabled)
                QMessageBox.warning(self, "Startup Error", 
                                  "Failed to change startup settings")

        except Exception as e:
            self.logger.error(f"Error toggling startup: {e}")
            self.startup_checkbox.setChecked(not enabled)
            QMessageBox.warning(self, "Startup Error", 
                              "Failed to change startup settings")

    def clear_logs(self):
        """Clear all logs"""
        reply = QMessageBox.question(self, "Clear Logs", 
                                   "Are you sure you want to clear all logs?",
                                   QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            success = self.theme_service.clear_logs()
            if success:
                self.refresh_logs()
                QMessageBox.information(self, "Logs Cleared", "All logs have been cleared")
            else:
                QMessageBox.warning(self, "Error", "Failed to clear logs")

    def closeEvent(self, event):
        """Handle window close event"""
        # Hide to tray instead of closing
        event.ignore()
        self.hide()

        # Show tray message
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage(
                "Theme Monitor",
                "Application is still running in the system tray",
                QSystemTrayIcon.Information,
                2000
            )

    def cleanup(self):
        """Cleanup resources"""
        if self.log_thread:
            self.log_thread.stop()

        if self.theme_service:
            self.theme_service.stop()
