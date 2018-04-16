#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class ComboBox(object):
    def __init__(self, items):
        self.items = items
        liststore = Gtk.ListStore(str)

        for item in items:
            liststore.append([item])

        combobox = Gtk.ComboBox()
        combobox.set_model(liststore)
        combobox.set_active(0)
        combobox.connect("changed", self.on_combobox_changed)

        cellrenderertext = Gtk.CellRendererText()
        combobox.pack_start(cellrenderertext, True)
        combobox.add_attribute(cellrenderertext, "text", 0)
        combobox.show()
        self.widget = combobox

    def on_combobox_changed(self, combobox):
        treeiter = combobox.get_active_iter()
        model = combobox.get_model()
        self.value = model[treeiter][0]
        return self.value

    def set_value(self, value):
        self.widget.set_active(self.items.index(value))



