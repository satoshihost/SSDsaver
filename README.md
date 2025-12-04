# SSD Saver - Log2Ram GUI Configurator

A modern GTK4/Libadwaita desktop application for configuring and managing log2ram on Debian-based Linux systems.

## Features

- 🎨 Modern GTK4/Libadwaita interface
- ⚙️ Configure log2ram settings (RAM size, sync method, ZRAM support)
- 🔄 Start, stop, and restart log2ram service
- 📊 View service status in real-time
- 🔐 Secure privilege elevation using pkexec

## Installation

### From .deb package

```bash
sudo apt install ./ssdsaver_1.0.0_all.deb
```

This will automatically install all dependencies including GTK4 and Libadwaita.

### Dependencies

The package automatically installs:
- Python 3.8+
- python3-gi (Python GObject bindings)
- gir1.2-gtk-4.0 (GTK4)
- gir1.2-adw-1 (Libadwaita)
- log2ram

## Usage

Launch from your application menu by searching for "SSD Saver" or run from terminal:

```bash
ssdsaver
```

## Building from Source

```bash
# Build the .deb package
dpkg-deb --build debian-package/ssdsaver

# Install
sudo apt install ./debian-package/ssdsaver.deb
```

## License

GNU General Public License v3.0 - see LICENSE file for details.

## Author

Andy Savage
