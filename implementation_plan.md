# Log2Ram Desktop Configurator Implementation Plan

## Goal Description
Create a desktop application for Linux Mint (and other Debian-based distros) to configure and manage `log2ram`. The app will allow users to modify settings (RAM size, sync method), manage the service, and view status, without needing the command line.

## User Review Required
> [!IMPORTANT]
> **Root Privileges**: Modifying `/etc/log2ram.conf` and managing systemd services requires root privileges. The application will need to use `pkexec` or similar to run privileged operations.

> [!NOTE]
> **Tech Stack**: Proposing **Python** with **GTK4 (PyGObject)**. This is native to Linux Mint (Cinnamon/Mate) and ensures a lightweight, integrated feel.

## Proposed Changes

### Project Structure
We will create a Python project structure.

#### [NEW] [main.py](file:///home/andy/work/new%20things/ssdsaver/main.py)
Entry point for the application.

#### [NEW] [ui.py](file:///home/andy/work/new%20things/ssdsaver/ui.py)
GTK4 user interface definitions.

#### [NEW] [config_manager.py](file:///home/andy/work/new%20things/ssdsaver/config_manager.py)
Logic to parse and write `/etc/log2ram.conf`.

#### [NEW] [service_manager.py](file:///home/andy/work/new%20things/ssdsaver/service_manager.py)
Logic to interact with `systemctl` (start, stop, status).

#### [NEW] [requirements.txt](file:///home/andy/work/new%20things/ssdsaver/requirements.txt)
Python dependencies (likely just system packages, but we'll list `PyGObject`).

### Features (Stage 1)
1.  **Configuration Form**:
    - `SIZE`: Input field (e.g., "40M").
    - `USE_RSYNC`: Checkbox.
    - `MAIL`: Checkbox.
        - *Context*: Enables sending system emails if Log2Ram encounters errors (e.g., RAM full).
    - `ZL2R`: Checkbox (ZRAM support).
        - *Context*: Enables compatibility with ZRAM (compressed RAM), which saves physical memory but uses a bit more CPU.
2.  **Service Control**:
    - Buttons to Start, Stop, Restart `log2ram`.
    - Status indicator (Running/Stopped).
3.  **Save & Apply**:
    - Button to save config and restart service (prompts for password).

### Future Extensibility (Stage 2)
- **Browser Cache Support**: The `ConfigManager` will be designed to support arbitrary directory mounts, not just `/var/log`. This will allow us to easily add a "Browser Cache" tab later where users can select their browser profiles (Firefox, Chrome, etc.) to move their caches to RAM.

## Verification Plan

### Automated Tests
- Unit tests for `config_manager.py` to ensure it correctly parses and regenerates the config file format.

### Manual Verification
1.  **Launch App**: Verify UI loads.
2.  **Read Config**: Verify it reads existing `/etc/log2ram.conf` (or defaults if missing).
3.  **Change Settings**: Modify a setting (e.g., change size to 50M) and Save.
4.  **Verify File**: Check `/etc/log2ram.conf` content.
5.  **Service Interaction**: Click Restart and check `systemctl status log2ram`.
