#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to monitor the pyIBIS display state
"""

import datetime
import ibis
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

def main():
	display = pylcd.ks0108.Display(backend = pylcd.GPIOBackend, pinmap = PINMAP, debug = False)
	draw = pylcd.ks0108.DisplayDraw(display)
	display.commit(full = True)
	fb2 = ibis.simulation.DisplayFont("/home/pi/projects/pyIBIS/simulation-font/bold/.fontmap", spacing = 2)
	fb1 = ibis.simulation.DisplayFont("/home/pi/projects/pyIBIS/simulation-font/bold/.fontmap", spacing = 1)
	fn2 = ibis.simulation.DisplayFont("/home/pi/projects/pyIBIS/simulation-font/narrow/.fontmap", spacing = 2)
	fn1 = ibis.simulation.DisplayFont("/home/pi/projects/pyIBIS/simulation-font/narrow/.fontmap", spacing = 1)
	simulator = ibis.simulation.DisplaySimulator((fb2, fb1, fn2, fn1))
	client = ibis.Client('localhost', 4242)
	
	old_active = True
	old_text = ""
	while True:
		now = datetime.datetime.now()
		texts = client.get_current_text()
		indicators = client.get_stop_indicators()
		
		active = False
		for idx in range(4):
			if texts[idx] or indicators[idx]:
				active = True
				break
		
		display.clear()
		redraw = False
		
		if active:
			old_text = ""
			draw.text("IBIS Monitor", 2, ('middle', 0, 13), 12, "/home/pi/.fonts/truetype/arialbd.ttf")
			draw.text(now.strftime("%H:%M:%S"), ('right', 0, 125), ('middle', 0, 13), 12, "/home/pi/.fonts/truetype/arialbd.ttf")
			
			for idx in range(4):
				bg_color = inactive_color = (255, 255, 255) if indicators[idx] else (0, 0, 0)
				active_color = (0, 0, 0) if indicators[idx] else (255, 255, 255)
				simulator.generate_image(texts[idx] if texts[idx] else " ", "/home/pi/projects/pyLCD/display%i.png" % idx, dotsize = 1, dotspacing = 0, inactive_color = inactive_color, active_color = active_color, bg_color = bg_color)
				draw.rectangle(2, 13 + idx * 13, 125, 24 + idx * 13)
				draw.image("/home/pi/projects/pyLCD/display%i.png" % idx, 4, 15 + idx * 13, condition = 'red > 0')
				redraw = True
		else:
			text = now.strftime("%H:%M")
			if text != old_text:
				draw.text(text, 'center', 'middle', 50, "/home/pi/.fonts/truetype/arialbd.ttf")
				old_text = text
				redraw = True
			else:
				time.sleep(3)
				redraw = False
		
		if not old_active and active:
			display.set_brightness(1023)
		
		if redraw:
			display.commit()
			time_needed = (datetime.datetime.now() - now).total_seconds()
			print "%.2f seconds needed to redraw" % time_needed
		
		if old_active and not active:
			display.set_brightness(10)
		
		old_active = active

if __name__ == "__main__":
	main()
