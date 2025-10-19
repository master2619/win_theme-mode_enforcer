# Windows Theme Monitor

A comprehensive Windows desktop application that monitors Light/Dark theme changes and provides theme persistence functionality.

## Features

### Core Functionality
- **Real-time Theme Monitoring**: Detects changes to Windows Light/Dark theme settings
- **Process Detection**: Identifies which process or service triggered theme changes
- **Comprehensive Logging**: SQLite-based logging system with detailed change history
- **Theme Persistence**: Enforces selected theme by continuously resetting registry values
- **System Tray Integration**: Runs in background with system tray icon
- **Auto-startup**: Optional Windows startup integration

### Modern UI
- **PySide6-based Interface**: Modern, responsive GUI with tabbed interface
- **Dashboard Tab**: Current theme status and persistence controls
- **Logs Tab**: Sortable, filterable view of all theme changes
- **Settings Tab**: Startup configuration and log management

### Technical Features
- **Registry Monitoring**: Monitors `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize`
- **Background Service**: Efficient background monitoring without impacting performance
- **Portable Executable**: Single-file executable via PyInstaller
- **No Admin Rights Required**: Runs with standard user privileges

## Installation

### Option 1: Run from Source
1. Ensure Python 3.11+ is installed
2. Run `install.bat` to install dependencies
3. Execute: `python main.py`

### Option 2: Build Executable
1. Install dependencies: `pip install -r requirements.txt`
2. Install PyInstaller: `pip install pyinstaller`
3. Build: `pyinstaller --onefile --noconsole --icon=assets/icon.ico main.py`
4. Run the executable from the `dist/` folder

## Usage

### Dashboard Tab
- View current theme mode (Light/Dark)
- Enable/disable theme persistence
- Select preferred theme for persistence mode
- Manual theme switching buttons

### Logs Tab
- View chronological list of all theme changes
- Sort by timestamp, theme mode, or source process
- Export logs to CSV for analysis
- Real-time updates as changes occur

### Settings Tab
- Configure Windows startup behavior
- Manage log database (clear logs)
- View application information

### System Tray
- Double-click tray icon to show main window
- Application continues running when main window is closed
- Right-click for quick access menu (if implemented)

## Persistence Mode

When enabled, Persistence Mode:
1. Monitors theme settings every 500ms
2. Automatically resets theme if changed externally
3. Logs all enforcement actions
4. Effectively "locks" the theme to your preference

**Use Cases:**
- Prevent applications from changing your theme
- Override Group Policy theme settings
- Maintain consistent theme across all applications
- Block unwanted theme changes from system updates

## Technical Details

### Registry Keys Monitored
- `AppsUseLightTheme`: Controls app-level theme (0=Dark, 1=Light)
- `SystemUsesLightTheme`: Controls system-level theme (0=Dark, 1=Light)

### Database Schema
SQLite database stores:
- Timestamp of change
- New theme mode (Light/Dark)
- Source process name
- Detailed change information

### Performance
- Minimal CPU usage (< 1% on modern systems)
- Small memory footprint (< 50MB RAM)
- Efficient registry monitoring
- Non-blocking UI operations

## Troubleshooting

### Common Issues
1. **Registry Access Denied**: Ensure running as standard user, not restricted account
2. **Theme Not Changing**: Check Windows version compatibility (Windows 10/11)
3. **Persistence Not Working**: Verify no Group Policy restrictions
4. **Build Failures**: Update PyInstaller and dependencies

### Logs Location
Application logs and database stored in:
`C:\Users\<Username>\AppData\Roaming\ThemeMonitor\`

### System Requirements
- Windows 10 version 1903+ or Windows 11
- Python 3.11+ (for source execution)
- 50MB free disk space
- No administrator privileges required

## Development

### Project Structure
```
ThemeMonitor/
├── main.py                 # Application entry point
├── theme_monitor.py        # Core monitoring logic
├── service.py             # Background service wrapper
├── ui/
│   ├── __init__.py
│   └── main_window.py     # PySide6 main window
├── assets/                # Icons and resources
├── requirements.txt       # Python dependencies
├── build_instructions.txt # Build guide
└── install.bat           # Windows installer
```

### Key Classes
- `ThemeMonitor`: Core functionality for registry monitoring and persistence
- `ThemeService`: Service wrapper for background operations
- `ThemeMonitorWindow`: Main PySide6 UI window
- `StartupManager`: Windows startup registry management

## License

This project is provided as-is for educational and personal use.

## Contributing

This is a demonstration project. For production use, consider:
- Enhanced process detection using ETW (Event Tracing for Windows)
- Digital signing for the executable
- MSI installer creation
- Additional theme-related registry keys monitoring
- Group Policy integration
