import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from config_manager import ConfigManager
from service_manager import ServiceManager

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(600, 700)
        self.set_title("Log2Ram Configurator")
        
        self.config_manager = ConfigManager()
        self.service_manager = ServiceManager()

        # Main Layout
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.box)

        # Header Bar
        self.header = Adw.HeaderBar()
        self.box.append(self.header)

        # Toast Overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        self.box.append(self.toast_overlay)

        # Scrollable Content
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.toast_overlay.set_child(self.scrolled_window)

        # Clamp to center content
        self.clamp = Adw.Clamp()
        self.clamp.set_maximum_size(600)
        self.clamp.set_margin_top(24)
        self.clamp.set_margin_bottom(24)
        self.clamp.set_margin_start(12)
        self.clamp.set_margin_end(12)
        self.scrolled_window.set_child(self.clamp)

        # Main Content Box
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.clamp.set_child(self.content_box)

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # --- Service Status Section ---
        self.status_group = Adw.PreferencesGroup(title="Service Status")
        self.content_box.append(self.status_group)

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
        self.config_group = Adw.PreferencesGroup(title="Configuration")
        self.content_box.append(self.config_group)

        # RAM Size
        self.row_size = Adw.ActionRow(title="RAM Size", subtitle="Amount of RAM to allocate (e.g. 40M, 1G)")
        self.entry_size = Gtk.Entry()
        self.entry_size.set_valign(Gtk.Align.CENTER)
        self.row_size.add_suffix(self.entry_size)
        self.config_group.add(self.row_size)

        # Use Rsync
        self.row_rsync = Adw.ActionRow(title="Use Rsync", subtitle="Use rsync instead of cp for syncing")
        self.switch_rsync = Gtk.Switch()
        self.switch_rsync.set_valign(Gtk.Align.CENTER)
        self.row_rsync.add_suffix(self.switch_rsync)
        self.config_group.add(self.row_rsync)

        # Mail
        self.row_mail = Adw.ActionRow(title="Error Emails", subtitle="Send system mails on error")
        self.switch_mail = Gtk.Switch()
        self.switch_mail.set_valign(Gtk.Align.CENTER)
        self.row_mail.add_suffix(self.switch_mail)
        self.config_group.add(self.row_mail)

        # ZL2R (ZRAM)
        self.row_zl2r = Adw.ActionRow(title="ZRAM Support (ZL2R)", subtitle="Enable ZRAM compatibility")
        self.switch_zl2r = Gtk.Switch()
        self.switch_zl2r.set_valign(Gtk.Align.CENTER)
        self.row_zl2r.add_suffix(self.switch_zl2r)
        self.config_group.add(self.row_zl2r)

        # --- Actions ---
        self.save_btn = Gtk.Button(label="Save Configuration")
        self.save_btn.add_css_class("suggested-action")
        self.save_btn.set_margin_top(20)
        self.save_btn.connect("clicked", self.on_save_clicked)
        self.content_box.append(self.save_btn)

    def _load_data(self):
        # Load Config
        config = self.config_manager.read_config()
        self.entry_size.set_text(config.get("SIZE", "40M"))
        self.switch_rsync.set_active(config.get("USE_RSYNC", "false").lower() == "true")
        self.switch_mail.set_active(config.get("MAIL", "true").lower() == "true")
        self.switch_zl2r.set_active(config.get("ZL2R", "false").lower() == "true")

        # Load Status
        self._update_status()

    def _update_status(self):
        status = self.service_manager.get_status()
        self.status_label.set_label(status)
        if status == "active":
            self.status_label.add_css_class("success")
            self.status_label.remove_css_class("error")
        else:
            self.status_label.add_css_class("error")
            self.status_label.remove_css_class("success")

    def on_save_clicked(self, btn):
        new_config = {
            "SIZE": self.entry_size.get_text(),
            "USE_RSYNC": "true" if self.switch_rsync.get_active() else "false",
            "MAIL": "true" if self.switch_mail.get_active() else "false",
            "ZL2R": "true" if self.switch_zl2r.get_active() else "false"
        }
        
        success = self.config_manager.save_config(new_config)
        if success:
            self.toast_overlay.add_toast(Adw.Toast.new("Configuration saved!"))
            # Optionally ask to restart service?
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
