#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
WORK IN PROGRESS
Script to display an UI for displaying stuff on a graphical display
"""

import gobject
import gtk
import pylcd
import time

PINMAP = {
	'RS': 7,
	'E': 8,
	'D0': 25,
	'D1': 24,
	'D2': 11,
	'D3': 9,
	'D4': 10,
	'D5': 22,
	'D6': 27,
	'D7': 17,
	'CS1': 4,
	'CS2': 3,
	'RST': 2,
	'LED': 18,
}

class NumberEntry(gtk.Entry):
	def __init__(self):
		super(NumberEntry, self).__init__()
		self.connect('changed', self.on_changed)
	
	def on_changed(self, *args):
		text = self.get_text().strip()
		self.set_text("".join([i for i in text if i in "-0123456789"]))

class GUI:
	def __init__(self):
		self.spacing = 5
		
		self.display = pylcd.ks0108.Display(backend = pylcd.DummyBackend, pinmap = PINMAP, debug = False)
		self.drawer = pylcd.ks0108.DisplayDraw(self.display)
		self.window = gtk.Window()
		self.window.connect('destroy', self.quit)
		self.window.set_title("GLCD control panel")
		self.window.set_border_width(10)
		self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
		self.icon = self.window.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_MENU)
		self.window.set_icon(self.icon)
		self.update()
	
	def _build_page(self, content, v_padding = 10, h_padding = 10):
		page = gtk.HBox()
		padding = gtk.VBox()
		padding.pack_start(content, padding = v_padding)
		page.pack_start(padding, padding = h_padding)
		return page
	
	def quit(self, widget, data = None):
		gtk.main_quit()
	
	def update(self):
		# Create the pixel draw page
		self.entry_pixel_x = NumberEntry()
		self.entry_pixel_x.set_size_request(10, -1)
		self.label_pixel_x = gtk.Label("X:")
		self.box_pixel_x = gtk.HBox(spacing = self.spacing)
		self.box_pixel_x.pack_start(self.label_pixel_x)
		self.box_pixel_x.pack_start(self.entry_pixel_x)
		
		self.entry_pixel_y = NumberEntry()
		self.entry_pixel_y.set_size_request(10, -1)
		self.label_pixel_y = gtk.Label("Y:")
		self.box_pixel_y = gtk.HBox(spacing = self.spacing)
		self.box_pixel_y.pack_start(self.label_pixel_y)
		self.box_pixel_y.pack_start(self.entry_pixel_y)
		
		self.box_pixel = gtk.VBox(spacing = self.spacing)
		self.box_pixel.pack_start(self.box_pixel_x)
		self.box_pixel.pack_start(self.box_pixel_y)
		self.page_pixel = self._build_page(self.box_pixel)
		
		# Create the line draw page
		self.box_line = gtk.VBox(spacing = self.spacing)
		self.box_line.pack_start(gtk.Button("okay was zum fick ððð"))
		self.box_line.pack_start(gtk.Button("wtf"))
		self.page_line = self._build_page(self.box_line)
		
		# Create the main notebook
		self.notebook_main = gtk.Notebook()
		self.notebook_main.set_tab_pos(gtk.POS_TOP)
		self.notebook_main.append_page(self.page_pixel, gtk.Label("Pixel"))
		self.notebook_main.append_page(self.page_line, gtk.Label("Line"))
		
		# Create the drawing controls
		self.checkbox_clear = gtk.CheckButton("Clear instead of drawing")
		self.checkbox_autocommit = gtk.CheckButton("Auto Commit")
		self.button_commit = gtk.Button("Commit")
		
		# Create the drawing control box
		self.box_controls = gtk.HBox(spacing = self.spacing)
		self.box_controls.pack_start(self.checkbox_clear)
		self.box_controls.pack_start(self.checkbox_autocommit)
		self.box_controls.pack_end(self.button_commit)
		
		# Create the main box
		self.box_main = gtk.VBox(spacing = self.spacing)
		self.box_main.pack_start(self.notebook_main)
		self.box_main.pack_start(self.box_controls)
		
		# Add the main box to the window
		self.window.add(self.box_main)
		self.window.show_all()

def main():
	gui = GUI()
	gtk.main()

if __name__ == "__main__":
	main()