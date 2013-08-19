#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to display an information panel with various information.
Bound to the GPIO backend.
Requires some sort of hardware input ("Previous" and "Next" buttons to switch panels).
"""

import datetime
import pylcd
import speedtest
import time
import traceback
import weather

from pprint import pprint

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

BUTTON_PINMAP = {
	'PREV': 31,
	'NEXT': 30,
}

def error_panel(display, draw, button_input):
	display.clear()
	draw.text("Error", 'center', 'middle', 50)
	display.commit()

def weather_panel(display, draw, button_input, loc_id):
	data = weather.get_weather_from_yahoo(loc_id, units = 'metric')
	
	display.clear()
	
	draw.text(data['location']['city'], 'left', 'top', 13)
	draw.text(u"%s°C" % data['condition']['temp'], 'right', 'top', 20)
	draw.text(u"%s%%" % data['atmosphere']['humidity'], 'left', 18, 14)
	draw.text(u"%s hPa" % data['atmosphere']['pressure'], 'right', 18, 14)
	
	draw.text(data['forecasts'][0]['day'], 1, 34, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.text(u"%s-%s°" % (data['forecasts'][0]['low'], data['forecasts'][0]['high']), 1, 44, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.text(data['forecasts'][0]['text'].split()[-1], 1, 54, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.line(0, 32, 127, 32)
	
	draw.text(data['forecasts'][1]['day'], 44, 34, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.text(u"%s-%s°" % (data['forecasts'][1]['low'], data['forecasts'][1]['high']), 44, 44, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.text(data['forecasts'][1]['text'].split()[-1], 44, 54, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.line(42, 32, 42, 63)
	
	draw.text(data['forecasts'][2]['day'], 87, 34, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.text(u"%s-%s°" % (data['forecasts'][2]['low'], data['forecasts'][2]['high']), 87, 44, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.text(data['forecasts'][2]['text'].split()[-1], 87, 54, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.line(85, 32, 85, 63)
	
	display.commit()

def network_panel(display, draw, button_input):
	display.clear()
	draw.image("/home/pi/projects/pyLCD/examples/network.png", 'left', 'top')
	draw.text("Network", 25, 'top', 20)
	draw.text("Download", 0, 25, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.text("Upload", 64, 25, font = "/home/pi/projects/pyLCD/5x7.fnt")
	draw.text("...", 0, 35, 20)
	draw.text("...", 64, 35, 20)
	display.commit()
	
	download_value, download_unit = speedtest.pretty_speed(speedtest.download()).split()
	draw.text("...", 0, 35, 20, clear = True)
	draw.text(download_value, 0, 35, 20)
	draw.text(download_unit, 0, 50, font = "/home/pi/projects/pyLCD/5x7.fnt")
	display.commit()
	
	upload_value, upload_unit = speedtest.pretty_speed(speedtest.upload()).split()
	draw.text("...", 64, 35, 20, clear = True)
	draw.text(upload_value, 64, 35, 20)
	draw.text(upload_unit, 64, 50, font = "/home/pi/projects/pyLCD/5x7.fnt")
	display.commit()

CONFIG = {
	'panels': (
		{
			'func': weather_panel,
			'timeout': 300.0,
			'kwargs': {
				'loc_id': "GMXX0191",
			},
		},
		{
			'func': network_panel,
			'timeout': 300.0,
			'kwargs': {
				
			},
		},
	),
	'error_panel': {
		'func': error_panel,
		'timeout': 300.0,
		'kwargs': {
			
		},
	},
}

def main():
	display = pylcd.ks0108.Display(backend = pylcd.GPIOBackend, pinmap = PINMAP, debug = False)
	draw = pylcd.ks0108.DisplayDraw(display)
	button_input = pylcd.GPIOInput(BUTTON_PINMAP)
	display.commit(full = True)
	num_panels = len(CONFIG['panels'])
	current_panel = 0
	brightness = 1023
	
	while True:
		try:
			panel = CONFIG['panels'][current_panel]
			panel['func'](display, draw, button_input, **panel['kwargs'])
		except:
			traceback.print_exc()
			print ""
			panel = CONFIG['error_panel']
			panel['func'](display, draw, button_input, **panel['kwargs'])
		
		start = datetime.datetime.now()
		while True:
			buttons = button_input.read_pressed_keys()
			if buttons:
				break
			secs = (datetime.datetime.now() - start).total_seconds()
			if secs >= panel['timeout']: # Timeout after the panel's TTL to reload the current panel
				buttons = []
				break
			time.sleep(0.1)
		
		if 'PREV' in buttons and 'NEXT' in buttons:
			if brightness == 1023:
				brightness = 100
			elif brightness == 100:
				brightness = 10
			elif brightness == 10:
				brightness = 0
			else:
				brightness = 1023
			
			display.set_brightness(brightness)
		elif buttons == ['PREV']:
			current_panel = current_panel - 1 if current_panel > 0 else num_panels - 1
		elif buttons == ['NEXT']:
			current_panel = current_panel + 1 if current_panel < num_panels - 1 else 0
		else:
			pass

if __name__ == "__main__":
	main()
