from gi.repository import Gtk, Gdk
import combobox

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

builder = Gtk.Builder()
builder.add_from_file('settings.glade')
w=builder.get_object('settings')

class Handler:
    def on_hotkey(ev, widget, key):
        widget.set_text(Gdk.keyval_name(key.keyval))
    def on_save(*args):
        pass
    def on_close(*args):
        pass
builder.connect_signals(Handler())



position_x = combobox.ComboBox(['left', 'center', 'right'])
pos_x = builder.get_object('pos_x')
pos_x.add(position_x.widget)
position_y = combobox.ComboBox(['left', 'center', 'bottom'])
pos_y = builder.get_object('pos_y')
pos_y.add(position_y.widget)
m=position_y.widget.get_model()
position_y.widget.set_active(2)
print(position_y.value)
position_y.set_value('left')

w.show()
Gtk.main()
