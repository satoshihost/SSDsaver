import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio

from ui import MainWindow

class Log2RamApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.satoshihost.ssdsaver',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect('activate', self.on_activate)
        
        # Create About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_action)
        self.add_action(about_action)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()
    
    def on_about_action(self, action, param):
        """Show About dialog"""
        self.win.show_about_dialog()

def main():
    app = Log2RamApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    sys.exit(main())
