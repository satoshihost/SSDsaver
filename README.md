# SSDsaver - Comprehensive SSD Wear Reduction Tool

A modern GTK4/Libadwaita desktop application for managing RAM-based caching to reduce SSD wear on Debian-based Linux systems.

## Features

- 🎨 Modern GTK4/Libadwaita interface with tabbed layout
- 💾 **Global RAM Budget Management** - Hard limit prevents over-provisioning
- 🌐 **Browser Cache Management** - Move Chrome, Firefox, Brave, Edge, Opera, Vivaldi caches to RAM
- 📱 **Application Cache Support** - Discord, Slack, Steam, APT, thumbnails, and more
- ⚙️ **System Logs** - Configure log2ram settings (RAM size, sync method, ZRAM support)
- 🔄 Service control - Start, stop, and restart services
- 📊 **Advanced Monitoring** - Real-time per-app RAM usage and session peak tracking
- 🧹 **Auto-Clear Cache** - Automatically clears old large caches when enabling apps
- 🔐 Secure privilege elevation using pkexec
- ⚠️ Smart warnings when apps exceed RAM budget


## Installation

### From .deb package

```bash
sudo apt install ./ssdsaver*.deb
```

This will automatically install all dependencies including GTK4, Libadwaita, and log2ram.

### Dependencies

The package automatically installs:
- Python 3.8+
- python3-gi (Python GObject bindings)
- gir1.2-gtk-4.0 (GTK4)
- gir1.2-adw-1 (Libadwaita)
- log2ram (bundled)

## Usage

Launch from your application menu by searching for "SSDsaver" or run from terminal:

```bash
ssdsaver
```

### Interface Overview

**Settings Tab** (Default):
- View total system RAM
- Set global RAM budget with slider or manual input
- Monitor current RAM usage vs budget
- Visual progress bar showing allocation

**System Logs Tab**:
- Configure log2ram for system logs
- Set sync method (rsync/cp)
- Enable ZRAM support
- Control service (start/stop/restart)

**Applications Tab**:
- Auto-detect installed browsers and apps
- Enable/disable RAM caching per app
- **Auto-Clear**: Automatically deletes old cache when enabling an app
- **Monitoring**: View real-time usage and session peak for each app
- Configure RAM size per app
- Choose Safe (synced) or Lossy (RAM-only) mode

### RAM Allocation Best Practices

**Recommended Budget**:
- Light usage (1-2 browsers): 512MB - 1GB
- Medium usage (multiple browsers + apps): 1GB - 2GB  
- Heavy usage (many apps): 2GB - 4GB

**Important Guidelines**:
- Don't allocate more than 50% of system RAM
- Leave headroom for system and applications
- Start conservative and increase if needed
- Monitor actual usage in Settings tab

**Safe vs Lossy Mode**:
- **Safe Mode** (recommended): Syncs to disk hourly and on shutdown, survives crashes
- **Lossy Mode**: RAM-only, maximum SSD savings, data lost on crash/power loss

### Supported Applications

**Browsers**: Chrome, Chromium, Firefox, Brave, Edge, Opera, Vivaldi  
**Communication**: Discord, Slack  
**Gaming**: Steam  
**System**: APT package cache, Thumbnail cache

> **Note**: The Applications tab only shows apps that are actually installed on your system. The app auto-detects which browsers and applications you have, so you'll only see relevant options.

## Building from Source

```bash
# Copy source files to package directory
cp *.py debian-package/ssdsaver/usr/share/ssdsaver/

# Build the .deb package
# Note: It is standard practice to include the version in the filename
dpkg-deb --build debian-package/ssdsaver ssdsaver_0.3.1_all.deb

# Install
sudo apt install ./ssdsaver_0.3.1_all.deb
```

## Troubleshooting

**App doesn't show new features after update**:
1. Kill running instances: `pkill -f ssdsaver`
2. Reinstall: `sudo apt install ./ssdsaver*.deb`
3. Launch fresh: `ssdsaver`

**Warning: "Insufficient RAM Budget"**:
- You cannot enable an app if it exceeds your remaining Global Budget.
- Go to Settings tab and increase budget, OR
- Disable other apps to free up space.

**Service won't start**:
- Check log2ram status: `systemctl status log2ram`
- View logs: `journalctl -u log2ram`

## Credits

SSDsaver includes [log2ram](https://github.com/azlux/log2ram) by [Azlux](https://github.com/azlux), licensed under the MIT License.

log2ram is an excellent tool for reducing SSD wear by moving system logs to RAM. We've bundled it to provide a seamless user experience. All credit for the log2ram functionality goes to the original author.

See [THIRD-PARTY-LICENSES](THIRD-PARTY-LICENSES) for full license information.

## License

GNU General Public License v3.0 - see LICENSE file for details.

## Author

Andy Savage

## Version
 
Current Version: **0.3.3**
