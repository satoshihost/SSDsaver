import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

from config_manager import ConfigManager
from service_manager import ServiceManager
from app_detector import AppDetector
from folder_manager import FolderManager

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(700, 800)
        self.set_title("SSDsaver")
        
        self.config_manager = ConfigManager()
        self.service_manager = ServiceManager()
        self.app_detector = AppDetector()
        self.folder_manager = FolderManager()
        
        # Track original config values for change detection
        self.original_config = {}
        
        # Store detected apps
        self.detected_apps = []

        # Main Layout
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.box)

        # Header Bar
        self.header = Adw.HeaderBar()
        
        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        menu.append("About SSDsaver", "app.about")
        menu_button.set_menu_model(menu)
        self.header.pack_end(menu_button)
        
        self.box.append(self.header)

        # Toast Overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        self.box.append(self.toast_overlay)

        # Tab View
        self.tab_view = Adw.TabView()
        self.tab_view.set_vexpand(True)
        self.toast_overlay.set_child(self.tab_view)
        
        # Tab Bar
        self.tab_bar = Adw.TabBar()
        self.tab_bar.set_view(self.tab_view)
        self.tab_bar.set_autohide(False)
        self.box.insert_child_after(self.tab_bar, self.header)

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # --- System Logs Tab ---
        self.logs_page = self._build_logs_tab()
        self.tab_view.append(self.logs_page)
        self.tab_view.get_page(self.logs_page).set_title("System Logs")
        self.tab_view.get_page(self.logs_page).set_icon(Gio.ThemedIcon.new("folder-documents-symbolic"))
        
        # --- Applications Tab ---
        self.apps_page = self._build_apps_tab()
        self.tab_view.append(self.apps_page)
        self.tab_view.get_page(self.apps_page).set_title("Applications")
        self.tab_view.get_page(self.apps_page).set_icon(Gio.ThemedIcon.new("applications-system-symbolic"))

    def _build_logs_tab(self):
        """Build the System Logs configuration tab"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)
        scrolled.set_child(clamp)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(content_box)
        
        # --- Service Status Section ---
        self.status_group = Adw.PreferencesGroup(title="Service Status")
        content_box.append(self.status_group)

        self.status_row = Adw.ActionRow(title="Current Status")
        self.status_label = Gtk.Label(label="Checking...")
        self.status_row.add_suffix(self.status_label)
        self.status_group.add(self.status_row)

        # Control Buttons
        self.controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.controls_box.set_halign(Gtk.Align.CENTER)
        self.controls_box.set_margin_top(10)
        
        self.btn_start = Gtk.Button(label="Start")
        self.btn_start.connect("clicked", self.on_start_clicked)
        self.controls_box.append(self.btn_start)

        self.btn_stop = Gtk.Button(label="Stop")
        self.btn_stop.connect("clicked", self.on_stop_clicked)
        self.controls_box.append(self.btn_stop)

        self.btn_restart = Gtk.Button(label="Restart")
        self.btn_restart.connect("clicked", self.on_restart_clicked)
        self.controls_box.append(self.btn_restart)

        self.status_group.add(self.controls_box)

        # --- Configuration Section ---
        self.config_group = Adw.PreferencesGroup(title="System Logs Configuration")
        content_box.append(self.config_group)

        # RAM Size
        self.row_size = Adw.ActionRow(title="RAM Size", subtitle="Amount of RAM to allocate (e.g. 40M, 1G)")
        self.entry_size = Gtk.Entry()
        self.entry_size.set_valign(Gtk.Align.CENTER)
        self.entry_size.connect("changed", self.on_config_changed)
        self.row_size.add_suffix(self.entry_size)
        self.config_group.add(self.row_size)

        # Use Rsync
        self.row_rsync = Adw.ActionRow(title="Use Rsync", subtitle="Use rsync instead of cp for syncing")
        self.switch_rsync = Gtk.Switch()
        self.switch_rsync.set_valign(Gtk.Align.CENTER)
        self.switch_rsync.connect("state-set", self.on_config_changed)
        self.row_rsync.add_suffix(self.switch_rsync)
        self.config_group.add(self.row_rsync)

        # Mail
        self.row_mail = Adw.ActionRow(title="Error Emails", subtitle="Send system mails on error")
        self.switch_mail = Gtk.Switch()
        self.switch_mail.set_valign(Gtk.Align.CENTER)
        self.switch_mail.connect("state-set", self.on_config_changed)
        self.row_mail.add_suffix(self.switch_mail)
        self.config_group.add(self.row_mail)

        # ZL2R (ZRAM)
        self.row_zl2r = Adw.ActionRow(title="ZRAM Support (ZL2R)", subtitle="Enable ZRAM compatibility")
        self.switch_zl2r = Gtk.Switch()
        self.switch_zl2r.set_valign(Gtk.Align.CENTER)
        self.switch_zl2r.connect("state-set", self.on_config_changed)
        self.row_zl2r.add_suffix(self.switch_zl2r)
        self.config_group.add(self.row_zl2r)

        # --- Actions ---
        self.save_btn = Gtk.Button(label="Save Configuration")
        self.save_btn.add_css_class("suggested-action")
        self.save_btn.set_margin_top(20)
        self.save_btn.set_sensitive(False)  # Disabled by default
        self.save_btn.connect("clicked", self.on_save_clicked)
        content_box.append(self.save_btn)
        
        return scrolled

    def _build_apps_tab(self):
        """Build the Applications tab"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        clamp = Adw.Clamp()
        clamp.set_maximum_size(700)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)
        scrolled.set_child(clamp)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(content_box)
        
        # Header with detect button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_margin_bottom(12)
        
        header_label = Gtk.Label(label="Move application caches to RAM to reduce SSD wear")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_hexpand(True)
        header_label.add_css_class("dim-label")
        header_box.append(header_label)
        
        detect_btn = Gtk.Button(label="Detect Apps")
        detect_btn.set_icon_name("view-refresh-symbolic")
        detect_btn.connect("clicked", self.on_detect_apps_clicked)
        header_box.append(detect_btn)
        
        content_box.append(header_box)
        
        # Applications list
        self.apps_group = Adw.PreferencesGroup(title="Detected Applications")
        content_box.append(self.apps_group)
        
        # This will be populated by detect_apps()
        self.app_rows = {}
        
        # RAM Usage Summary
        self.ram_summary_group = Adw.PreferencesGroup(title="RAM Usage")
        content_box.append(self.ram_summary_group)
        
        self.ram_usage_row = Adw.ActionRow(title="Total Allocated")
        self.ram_usage_label = Gtk.Label(label="0 MB")
        self.ram_usage_label.add_css_class("title-2")
        self.ram_usage_row.add_suffix(self.ram_usage_label)
        self.ram_summary_group.add(self.ram_usage_row)
        
        # Apply button
        self.apply_apps_btn = Gtk.Button(label="Apply Changes")
        self.apply_apps_btn.add_css_class("suggested-action")
        self.apply_apps_btn.set_margin_top(20)
        self.apply_apps_btn.set_sensitive(False)
        self.apply_apps_btn.connect("clicked", self.on_apply_apps_clicked)
        content_box.append(self.apply_apps_btn)
        
        return scrolled

    def _load_data(self):
        # Load Config
        config = self.config_manager.read_config()
        self.original_config = config.copy()  # Store original values
        
        self.entry_size.set_text(config.get("SIZE", "40M"))
        self.switch_rsync.set_active(config.get("USE_RSYNC", "false").lower() == "true")
        self.switch_mail.set_active(config.get("MAIL", "true").lower() == "true")
        self.switch_zl2r.set_active(config.get("ZL2R", "false").lower() == "true")

        # Load Status
        self._update_status()
        
        # Detect apps
        self.detect_apps()

    def _update_status(self):
        status = self.service_manager.get_status()
        self.status_label.set_label(status)
        
        # Update button visibility based on service state
        is_active = status == "active"
        self.btn_start.set_visible(not is_active)
        self.btn_stop.set_visible(is_active)
        self.btn_restart.set_visible(is_active)
        
        if is_active:
            self.status_label.add_css_class("success")
            self.status_label.remove_css_class("error")
        else:
            self.status_label.add_css_class("error")
            self.status_label.remove_css_class("success")
    
    def detect_apps(self):
        """Detect installed applications"""
        self.detected_apps = self.app_detector.detect_all_apps()
        
        # Clear existing rows
        for row in list(self.app_rows.values()):
            self.apps_group.remove(row)
        self.app_rows.clear()
        
        # Add rows for detected apps
        for app in self.detected_apps:
            row = self._create_app_row(app)
            self.apps_group.add(row)
            self.app_rows[app.name] = row
        
        # Update RAM usage
        self._update_ram_usage()
    
    def _create_app_row(self, app_info):
        """Create a row for an application"""
        row = Adw.ExpanderRow(title=app_info.display_name)
        row.set_subtitle(f"Default: {app_info.default_size}")
        row.set_icon_name(app_info.icon_name)
        
        # Enable switch
        switch = Gtk.Switch()
        switch.set_valign(Gtk.Align.CENTER)
        
        # Check if app is enabled in config
        is_enabled = self.folder_manager.is_app_enabled(app_info.name)
        switch.set_active(is_enabled)
        switch.connect("state-set", lambda w, s: self.on_app_toggled(app_info.name, s))
        row.add_suffix(switch)
        
        # Size configuration
        size_row = Adw.ActionRow(title="RAM Size")
        size_entry = Gtk.Entry()
        size_entry.set_text(app_info.default_size)
        size_entry.set_valign(Gtk.Align.CENTER)
        size_entry.set_width_chars(8)
        size_row.add_suffix(size_entry)
        row.add_row(size_row)
        
        # Mode selection
        mode_row = Adw.ActionRow(title="Mode", subtitle="Safe: syncs to disk | Lossy: RAM only")
        mode_combo = Gtk.DropDown.new_from_strings(["Safe", "Lossy"])
        mode_combo.set_valign(Gtk.Align.CENTER)
        mode_row.add_suffix(mode_combo)
        row.add_row(mode_row)
        
        # Store widgets for later access
        row.app_name = app_info.name
        row.size_entry = size_entry
        row.mode_combo = mode_combo
        row.enable_switch = switch
        
        return row
    
    def on_app_toggled(self, app_name, state):
        """Handle app enable/disable toggle"""
        self.apply_apps_btn.set_sensitive(True)
        self._update_ram_usage()
        return False
    
    def on_detect_apps_clicked(self, btn):
        """Refresh app detection"""
        self.detect_apps()
        self.toast_overlay.add_toast(Adw.Toast.new(f"Found {len(self.detected_apps)} applications"))
    
    def on_apply_apps_clicked(self, btn):
        """Apply application cache settings"""
        # Build configuration
        app_configs = {}
        
        for app_name, row in self.app_rows.items():
            if row.enable_switch.get_active():
                # Get app info
                app_info = next((a for a in self.detected_apps if a.name == app_name), None)
                if not app_info:
                    continue
                
                size = row.size_entry.get_text()
                mode = "safe" if row.mode_combo.get_selected() == 0 else "lossy"
                
                app_configs[app_name] = {
                    "enabled": "true",
                    "size": size,
                    "mode": mode,
                    "paths": ";".join(app_info.cache_paths)
                }
        
        # Save configuration
        if self.folder_manager.save_config(app_configs):
            # Update log2ram config
            if self.folder_manager.update_log2ram_config():
                self.toast_overlay.add_toast(Adw.Toast.new("Configuration saved! Restart service to apply."))
                self.apply_apps_btn.set_sensitive(False)
            else:
                self.toast_overlay.add_toast(Adw.Toast.new("Failed to update log2ram configuration"))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new("Failed to save configuration"))
    
    def _update_ram_usage(self):
        """Update RAM usage display"""
        total_mb = 0
        
        for app_name, row in self.app_rows.items():
            if row.enable_switch.get_active():
                size_str = row.size_entry.get_text()
                total_mb += self.folder_manager._parse_size_to_mb(size_str)
        
        self.ram_usage_label.set_label(f"{total_mb} MB")
    
    def on_config_changed(self, widget, *args):
        """Called when any configuration value changes"""
        # Check if current values differ from original
        current_size = self.entry_size.get_text()
        current_rsync = "true" if self.switch_rsync.get_active() else "false"
        current_mail = "true" if self.switch_mail.get_active() else "false"
        current_zl2r = "true" if self.switch_zl2r.get_active() else "false"
        
        has_changes = (
            current_size != self.original_config.get("SIZE", "40M") or
            current_rsync != self.original_config.get("USE_RSYNC", "false") or
            current_mail != self.original_config.get("MAIL", "true") or
            current_zl2r != self.original_config.get("ZL2R", "false")
        )
        
        self.save_btn.set_sensitive(has_changes)
        return False  # For switch state-set signal

    def on_save_clicked(self, btn):
        new_config = {
            "SIZE": self.entry_size.get_text(),
            "USE_RSYNC": "true" if self.switch_rsync.get_active() else "false",
            "MAIL": "true" if self.switch_mail.get_active() else "false",
            "ZL2R": "true" if self.switch_zl2r.get_active() else "false"
        }
        
        success = self.config_manager.save_config(new_config)
        if success:
            self.original_config = new_config.copy()  # Update original values
            self.save_btn.set_sensitive(False)  # Disable save button
            self.toast_overlay.add_toast(Adw.Toast.new("Configuration saved!"))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new("Failed to save configuration."))

    def on_start_clicked(self, btn):
        if self.service_manager.start_service():
            self.toast_overlay.add_toast(Adw.Toast.new("Service started"))
            self._update_status()
        else:
            self.toast_overlay.add_toast(Adw.Toast.new("Failed to start service"))

    def on_stop_clicked(self, btn):
        if self.service_manager.stop_service():
            self.toast_overlay.add_toast(Adw.Toast.new("Service stopped"))
            self._update_status()
        else:
            self.toast_overlay.add_toast(Adw.Toast.new("Failed to stop service"))

    def on_restart_clicked(self, btn):
        if self.service_manager.restart_service():
            self.toast_overlay.add_toast(Adw.Toast.new("Service restarted"))
            self._update_status()
        else:
            self.toast_overlay.add_toast(Adw.Toast.new("Failed to restart service"))
    
    def show_about_dialog(self):
        """Show About dialog with credits"""
        about = Adw.AboutWindow(
            transient_for=self,
            application_name="SSDsaver",
            application_icon="drive-harddisk-symbolic",
            developer_name="Andy Savage",
            version="2.0.0",
            website="https://github.com/andysavage/ssdsaver",
            issue_url="https://github.com/andysavage/ssdsaver/issues",
            copyright="© 2024 Andy Savage",
            license_type=Gtk.License.GPL_3_0,
            developers=["Andy Savage"],
        )
        
        # Add credits for log2ram
        about.add_credit_section(
            "Includes",
            [
                "log2ram by Azlux https://github.com/azlux/log2ram"
            ]
        )
        
        about.add_legal_section(
            "log2ram",
            "© 2016-2023 Azlux",
            Gtk.License.MIT_X11,
            None
        )
        
        about.present()
