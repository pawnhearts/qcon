from gi.repository import Gtk
builder = Gtk.Builder()
builder.add_from_file('glade.glade')
w=builder.get_object('settings')

class Handler:
    def on_hotkey(ev, widget, key):
        print(key.keyval)
    def on_save(*args):
        pass
    def on_close(*args):
        pass
builder.connect_signals(Handler())

position_x_store = Gtk.ListStore(str)
for _ in ['left', 'center', 'right']:
    position_x_store.append([_])
renderer_text = Gtk.CellRendererText()
builder.get_object('position_x').pack_start(renderer_text, True)
builder.get_object('position_x').add_attribute(renderer_text, "text", 0)
builder.get_object('position_x').set_model(position_x_store)




w.show()
Gtk.main()
