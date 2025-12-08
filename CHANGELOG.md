# Changelog

All notable changes to SSDsaver will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.3] - 2025-12-08

### Fixed
- **Save Button Sensitivity**: The "Apply Changes" button now correctly activates when you modify RAM size or mode settings for enabled applications. Previously, you had to toggle the app off and on again to save changes.

### Technical Details
- Added signal handlers (`changed` and `notify::selected`) to size entry and mode combo widgets
- Implemented `on_app_param_changed()` method to update UI state when app parameters change

## [0.3.2] - 2025-12-08

### Changed
- **Version Bump**: Updated to 0.3.2 to trigger package upgrade for users on 0.3.1
- **Packaging**: Moved build output to `dist/` folder for cleaner project organization

## [0.3.1] - 2025-12-07

This release introduces major improvements to RAM budget management, cache handling, and monitoring capabilities.

### Added
- **Hard RAM Budget Limit**: The application now enforces a strict limit on total RAM allocation
  - You cannot enable an app if it would exceed your global budget
  - Clear "Insufficient RAM Budget" dialog explains exactly how much space you need vs. have available
  - Prevents system instability from RAM disk overflow
  - Validation runs both when toggling apps and when clicking "Apply Changes"

- **Auto-Clear Cache**: Automatically handles existing large caches when enabling apps
  - When you enable an app, its existing disk cache is automatically deleted
  - Prevents the "startup problem" where old caches are larger than allocated RAM
  - Shows toast notification confirming cache was cleared
  - Static warning label in UI: "Enabling an app will DELETE its existing cache"

- **Advanced RAM Monitoring**: Real-time visibility into actual RAM usage
  - Per-app usage display in Settings tab
  - "Current" vs "Peak" toggle to track session maximum usage
  - Visual progress bars showing usage vs. allocated size
  - Color coding: green (normal), yellow (>90%), red (over budget)
  - Monitoring only runs when Settings tab is active (performance optimization)

- **Smart Path Detection**: Improved browser cache detection
  - Firefox: Updated pattern from `*.default-release` to `*.default*` for broader compatibility
  - Brave: Added fallback path `~/.cache/BraveSoftware/...` in addition to `~/.config/...`
  - Opera: Enhanced path detection
  - Paths are now refreshed from detector on each operation, not cached in config

### Fixed
- **0MB Usage Reporting**: Fixed issue where Firefox, Brave, and Opera showed 0MB usage
  - Root cause: Path patterns were too specific or missing
  - Solution: Broadened wildcard patterns and added fallback paths

- **Path Expansion Bug**: Fixed cache clearing failure for paths starting with `~`
  - Root cause: `clear_app_cache()` wasn't expanding `~` to home directory
  - Solution: Added `os.path.expanduser()` before file operations
  - This was causing the "cache cleared" toast to appear even though files weren't actually deleted

- **Navigation Crash**: Fixed TypeError when clicking "Go to Settings" from warning dialogs
  - Root cause: Passing `Gtk.ScrolledWindow` instead of `Adw.TabPage` to `set_selected_page()`
  - Solution: Store and use the `Adw.TabPage` objects returned by `tab_view.append()`

- **Dialog Compatibility**: Replaced `Adw.MessageDialog` with `Gtk.MessageDialog`
  - Fixes crashes on systems with older Libadwaita versions (< 1.2)
  - Maintains visual consistency while improving compatibility

### Changed
- **Simplified UX**: Removed blocking confirmation dialogs for cache clearing
  - Old behavior: Multiple dialogs asking "Are you sure?" before clearing cache
  - New behavior: Clear warning label + automatic clearing with toast notification
  - Reduces friction while maintaining user awareness

- **Optimized Monitoring**: Usage stats only update when Settings tab is visible
  - Prevents unnecessary CPU/disk usage when user isn't viewing stats
  - Implemented via tab selection check in `_update_usage_stats()`

### Technical Details
- Implemented `get_path_usage_mb()` using `du -sk` command for accurate disk usage
- Implemented `get_app_actual_usage()` to aggregate usage across multiple cache paths
- Implemented `clear_app_cache()` with wildcard support and proper error handling
- Added `would_exceed_budget()` validation method to `FolderManager`
- Tab page objects now properly stored for navigation (`settings_tab_page`, `logs_tab_page`, `apps_tab_page`)

## [0.3.0] - 2025-12-04

### Added
- **Multi-Application Support**: Expanded beyond system logs to manage browser and application caches
  - Chrome, Chromium, Firefox, Brave, Edge, Opera, Vivaldi
  - Discord, Slack, Steam
  - APT package cache, Thumbnail cache

- **Global RAM Budget Management**: New Settings tab for controlling total RAM allocation
  - Slider for quick adjustments (128MB - 50% of system RAM)
  - Manual input for precise values
  - Visual progress bar showing current usage vs. budget
  - Real-time calculation of available RAM

- **Per-Application Configuration**: Granular control over each app
  - Enable/disable RAM caching per application
  - Customize RAM size allocation
  - Choose between Safe (synced) and Lossy (RAM-only) modes
  - Auto-detection of installed applications

- **Tabbed Interface**: Organized UI with three tabs
  - Settings: Global RAM budget management
  - System Logs: Original log2ram configuration
  - Applications: Browser and app cache management

### Changed
- **Rebranded**: From "Log2Ram Config" to "SSDsaver"
  - Reflects expanded scope beyond just system logs
  - New application ID: `com.example.ssdsaver`
  - Updated icons and branding

- **Architecture**: Modular design for scalability
  - `app_detector.py`: Detects installed applications and their cache paths
  - `folder_manager.py`: Manages per-app RAM disk configurations
  - `config_manager.py`: Handles log2ram configuration
  - `service_manager.py`: Controls systemd services

### Technical Details
- Bundled log2ram (MIT License by Azlux) for seamless installation
- Configuration stored in `/etc/ssdsaver/folders.conf`
- Uses `pkexec` for privilege elevation
- GTK4 + Libadwaita for modern UI

## [0.2.0] - 2025-11-20

### Added
- Initial release as "Log2Ram Config"
- Basic log2ram configuration interface
- Service control (start/stop/restart)
- RAM size configuration
- Rsync/cp sync method selection
- ZRAM support toggle

### Technical Details
- GTK4 + Libadwaita UI
- Python 3.8+ with GObject introspection
- Debian package (.deb) distribution

---

## Legend

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
- **Technical Details**: Implementation notes for developers
