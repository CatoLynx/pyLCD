#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to display a countdown on a GLCD
"""

import datetime
import pylcd
import sys
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
	target = datetime.datetime.strptime(sys.argv[1], "%d.%m.%Y %H:%M:%S")
	
	while True:
		now = datetime.datetime.now()
		delta = target - now
		seconds = delta.total_seconds()
		microseconds = seconds - int(seconds)
		seconds = int(seconds)
		minutes, seconds = divmod(seconds, 60.0)
		hours, minutes = divmod(minutes, 60.0)
		days, hours = divmod(hours, 24.0)
		years, days = divmod(days, 365.0)
		years, days, hours, minutes, seconds = [int(number) for number in (years, days, hours, minutes, seconds)]
		
		total_days = days + years * 365
		total_hours = hours + total_days * 24
		total_minutes = minutes + total_hours * 60
		total_seconds = seconds + total_minutes * 60
		
		if now.hour >= 20 and now.hour < 22:
			display.set_brightness(100)
		elif now.hour >= 22:
			display.set_brightness(10)
		elif 0 <= now.hour < 7:
			display.set_brightness(1)
		else:
			display.set_brightness(1023)
		
		display.clear()
		
		#draw.analog_clock(30, 47, 16, hours, minutes, has_lines = False, fill = False, clear = False)
		#draw.text("Es ist", ('center', 0, 56), 40, 9, "/home/pi/.fonts/truetype/arial.ttf")
		draw.text(now.strftime("%H:%M"), ('center', 0, 56), 34, 20, "/home/pi/.fonts/truetype/timesbd.ttf")
		draw.text(now.strftime("%d.%m.%y"), ('center', 0, 56), 52, 14, "/home/pi/.fonts/truetype/timesbd.ttf")
		
		draw.image("/home/pi/projects/pyLCD/ef20.png", 'left', 'top')
		draw.text("%i Tage" % days, ('center', 58, 127), 1, 16, "/home/pi/.fonts/truetype/timesbd.ttf")
		draw.text("%02i:%02i" % (hours, minutes), ('center', 58, 127), 19, 25, "/home/pi/.fonts/truetype/timesbd.ttf")
		draw.text("das sind", ('center', 58, 127), 41, 9, "/home/pi/.fonts/truetype/arial.ttf")
		draw.text("%i min" % (total_minutes), ('center', 58, 127), 51, 16, "/home/pi/.fonts/truetype/timesbd.ttf")
		
		draw.line(56, 0, 56, 64)
		draw.line(57, 0, 57, 64)
		draw.line(0, 31, 57, 31)
		draw.line(0, 32, 57, 32)
		
		display.commit()
		time_needed = (datetime.datetime.now() - now).total_seconds()
		print "%.2f seconds needed to redraw" % time_needed
		time.sleep(60.0 - time_needed)

if __name__ == "__main__":
	main()
