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
        # --- Settings Tab (First/Default) ---
        self.settings_page = self._build_settings_tab()
        self.tab_view.append(self.settings_page)
        self.tab_view.get_page(self.settings_page).set_title("Settings")
        self.tab_view.get_page(self.settings_page).set_icon(Gio.ThemedIcon.new("preferences-system-symbolic"))
        
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

    def _build_settings_tab(self):
        """Build the Settings tab for global RAM budget"""
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
        
        # --- System Info Section ---
        system_group = Adw.PreferencesGroup(title="System Information")
        content_box.append(system_group)
        
        # Total system RAM
        system_ram_mb = self.folder_manager.get_system_ram()
        system_ram_row = Adw.ActionRow(title="Total System RAM")
        system_ram_label = Gtk.Label(label=f"{system_ram_mb} MB")
        system_ram_label.add_css_class("title-3")
        system_ram_row.add_suffix(system_ram_label)
        system_group.add(system_ram_row)
        
        # --- RAM Budget Section ---
        budget_group = Adw.PreferencesGroup(
            title="RAM Budget",
            description="Set the total amount of RAM to allocate for caching. Don't exceed 50% of system RAM."
        )
        content_box.append(budget_group)
        
        # Get current budget
        current_budget = self.folder_manager.get_global_budget()
        max_budget = min(system_ram_mb // 2, 4096)  # Max 50% or 4GB
        
        # Slider for RAM allocation
        slider_row = Adw.ActionRow(title="RAM Allocation")
        self.budget_slider = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            128,  # Min 128MB
            max_budget,
            64  # Step by 64MB
        )
        self.budget_slider.set_value(current_budget)
        self.budget_slider.set_draw_value(False)
        self.budget_slider.set_hexpand(True)
        self.budget_slider.connect("value-changed", self.on_budget_changed)
        slider_row.add_suffix(self.budget_slider)
        budget_group.add(slider_row)
        
        # Manual input for precise control
        input_row = Adw.ActionRow(title="Exact Amount (MB)", subtitle="Type to set precise value")
        self.budget_spinbutton = Gtk.SpinButton()
        self.budget_spinbutton.set_range(128, max_budget)
        self.budget_spinbutton.set_increments(64, 256)
        self.budget_spinbutton.set_value(current_budget)
        self.budget_spinbutton.set_valign(Gtk.Align.CENTER)
        self.budget_spinbutton.connect("value-changed", self.on_budget_input_changed)
        input_row.add_suffix(self.budget_spinbutton)
        budget_group.add(input_row)
        
        # --- Usage Section ---
        usage_group = Adw.PreferencesGroup(title="Current Usage")
        content_box.append(usage_group)
        
        # Allocated
        allocated_row = Adw.ActionRow(title="Allocated Budget")
        self.allocated_label = Gtk.Label(label=f"{current_budget} MB")
        self.allocated_label.add_css_class("title-2")
        allocated_row.add_suffix(self.allocated_label)
        usage_group.add(allocated_row)
        
        # Used by apps
        used_mb = self.folder_manager.get_total_ram_usage()
        used_row = Adw.ActionRow(title="Used by Enabled Apps")
        self.used_label = Gtk.Label(label=f"{used_mb} MB")
        self.used_label.add_css_class("title-2")
        used_row.add_suffix(self.used_label)
        usage_group.add(used_row)
        
        # Available
        available_row = Adw.ActionRow(title="Available")
        self.available_label = Gtk.Label(label=f"{current_budget - used_mb} MB")
        self.available_label.add_css_class("title-2")
        available_row.add_suffix(self.available_label)
        usage_group.add(available_row)
        
        # Progress bar
        self.usage_progress = Gtk.ProgressBar()
        self.usage_progress.set_margin_top(12)
        if current_budget > 0:
            self.usage_progress.set_fraction(used_mb / current_budget)
        usage_group.add(self.usage_progress)
        
        # Apply button
        self.apply_budget_btn = Gtk.Button(label="Apply Budget")
        self.apply_budget_btn.add_css_class("suggested-action")
        self.apply_budget_btn.set_margin_top(20)
        self.apply_budget_btn.set_sensitive(False)
        self.apply_budget_btn.connect("clicked", self.on_apply_budget_clicked)
        content_box.append(self.apply_budget_btn)
        
        return scrolled


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
        row.add_action(switch)  # ExpanderRow uses add_action, not add_suffix
        
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
        if state:  # Enabling the app
            # Get the row and size
            row = self.app_rows.get(app_name)
            if row:
                size_str = row.size_entry.get_text()
                
                # Check if this would exceed budget
                if self.folder_manager.would_exceed_budget(app_name, size_str):
                    budget_mb = self.folder_manager.get_global_budget()
                    used_mb = self.folder_manager.get_total_ram_usage()
                    size_mb = self.folder_manager._parse_size_to_mb(size_str)
                    new_total = used_mb + size_mb
                    
                    # Show warning dialog
                    dialog = Adw.MessageDialog.new(self)
                    dialog.set_heading("Exceeds RAM Budget")
                    dialog.set_body(
                        f"Enabling this app would use {new_total} MB, exceeding your "
                        f"budget of {budget_mb} MB.\n\n"
                        f"Options:\n"
                        f"• Increase your budget in the Settings tab\n"
                        f"• Disable other apps to free up space\n"
                        f"• Reduce the RAM allocation for this app"
                    )
                    dialog.add_response("cancel", "Cancel")
                    dialog.add_response("increase", "Go to Settings")
                    dialog.set_response_appearance("increase", Adw.ResponseAppearance.SUGGESTED)
                    dialog.set_default_response("cancel")
                    dialog.set_close_response("cancel")
                    
                    def on_response(dialog, response):
                        if response == "increase":
                            # Switch to Settings tab
                            self.tab_view.set_selected_page(self.settings_page)
                        else:
                            # Uncheck the switch
                            row.enable_switch.set_active(False)
                    
                    dialog.connect("response", on_response)
                    dialog.present()
                    return True  # Block the toggle
        
        self.apply_apps_btn.set_sensitive(True)
        self._update_ram_usage()
        self._update_settings_usage()  # Update Settings tab too
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
    
    def _update_settings_usage(self):
        """Update Settings tab usage display"""
        budget_mb = self.folder_manager.get_global_budget()
        used_mb = self.folder_manager.get_total_ram_usage()
        available_mb = max(0, budget_mb - used_mb)
        
        self.used_label.set_label(f"{used_mb} MB")
        self.available_label.set_label(f"{available_mb} MB")
        
        # Update progress bar
        if budget_mb > 0:
            fraction = min(1.0, used_mb / budget_mb)
            self.usage_progress.set_fraction(fraction)
            
            # Change color if over budget
            if used_mb > budget_mb:
                self.usage_progress.add_css_class("error")
            else:
                self.usage_progress.remove_css_class("error")
    
    
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
    
    def on_budget_changed(self, slider):
        """Handle budget slider changes"""
        value = int(slider.get_value())
        # Update spin button to match (avoid recursion with handler block)
        self.budget_spinbutton.handler_block_by_func(self.on_budget_input_changed)
        self.budget_spinbutton.set_value(value)
        self.budget_spinbutton.handler_unblock_by_func(self.on_budget_input_changed)
        
        # Update labels
        self._update_budget_display(value)
        self.apply_budget_btn.set_sensitive(True)
    
    def on_budget_input_changed(self, spinbutton):
        """Handle manual budget input changes"""
        value = int(spinbutton.get_value())
        # Update slider to match (avoid recursion with handler block)
        self.budget_slider.handler_block_by_func(self.on_budget_changed)
        self.budget_slider.set_value(value)
        self.budget_slider.handler_unblock_by_func(self.on_budget_changed)
        
        # Update labels
        self._update_budget_display(value)
        self.apply_budget_btn.set_sensitive(True)
    
    def _update_budget_display(self, budget_mb):
        """Update budget display labels"""
        used_mb = self.folder_manager.get_total_ram_usage()
        available_mb = max(0, budget_mb - used_mb)
        
        self.allocated_label.set_label(f"{budget_mb} MB")
        self.available_label.set_label(f"{available_mb} MB")
        
        # Update progress bar
        if budget_mb > 0:
            fraction = min(1.0, used_mb / budget_mb)
            self.usage_progress.set_fraction(fraction)
            
            # Change color if over budget
            if used_mb > budget_mb:
                self.usage_progress.add_css_class("error")
            else:
                self.usage_progress.remove_css_class("error")
    
    def on_apply_budget_clicked(self, btn):
        """Apply the new RAM budget"""
        new_budget = int(self.budget_spinbutton.get_value())
        used_mb = self.folder_manager.get_total_ram_usage()
        
        # Warn if budget is less than current usage
        if new_budget < used_mb:
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Budget Below Current Usage")
            dialog.set_body(
                f"You are trying to set a budget of {new_budget} MB, but enabled apps "
                f"are currently using {used_mb} MB. Please disable some apps first or "
                f"increase the budget."
            )
            dialog.add_response("ok", "OK")
            dialog.set_default_response("ok")
            dialog.present()
            return
        
        # Save budget
        self.folder_manager.set_global_budget(new_budget)
        
        # Save config and update log2ram
        app_configs = self.folder_manager._config_to_dict()
        # Remove GLOBAL section as it's handled separately
        app_configs.pop('GLOBAL', None)
        
        if self.folder_manager.save_config(app_configs):
            if self.folder_manager.update_log2ram_config():
                self.toast_overlay.add_toast(Adw.Toast.new(f"Budget set to {new_budget} MB. Restart service to apply."))
                self.apply_budget_btn.set_sensitive(False)
            else:
                self.toast_overlay.add_toast(Adw.Toast.new("Failed to update log2ram configuration"))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new("Failed to save configuration"))
    
    
    def show_about_dialog(self):
        """Show About dialog with credits"""
        # Check if Adw.AboutWindow is available (Libadwaita 1.2+)
        if hasattr(Adw, 'AboutWindow'):
            about = Adw.AboutWindow(
                transient_for=self,
                application_name="SSDsaver",
                application_icon="drive-harddisk-symbolic",
                developer_name="Andy Savage",
                version="0.3.1",
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
        else:
            # Fallback to Gtk.AboutDialog for older Libadwaita
            about = Gtk.AboutDialog(
                transient_for=self,
                modal=True,
                program_name="SSDsaver",
                logo_icon_name="drive-harddisk-symbolic",
                version="0.3.1",
                website="https://github.com/andysavage/ssdsaver",
                copyright="© 2024 Andy Savage",
                license_type=Gtk.License.GPL_3_0,
                authors=["Andy Savage"],
            )
            
            # Add credits in comments or description since Gtk.AboutDialog is simpler
            about.set_comments(
                "A modern GTK4/Libadwaita desktop application for configuring log2ram.\n\n"
                "Includes log2ram by Azlux (MIT License)."
            )
            
            about.present()
