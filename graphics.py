#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to display graphics on a GLCD
"""

import argparse
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
	"""parser = argparse.ArgumentParser()
	parser.add_argument('-t', '--time', help = "The time to count down to.")
	parser.add_argument('-tf', '--timeformat', default = "%d.%m.%Y %H:%M:%S", help = "The format string to parse the target time, e.g. '%%d.%%m.%%Y %%H:%%M:%%S'")
	parser.add_argument('-f', '--format', help = "The format string for the countdown, e.g. '%%Y years %%D days %%H hours %%M minutes %%S seconds %%U microseconds %%TD total days %%TH total hours %%TM total minutes %%TS total seconds until %%E'")
	parser.add_argument('-a', '--align', choices = ['left', 'center', 'right'], default = 'center')
	parser.add_argument('-e', '--event', help = "The name of the event to count down to.")
	args = parser.parse_args()"""
	display = pylcd.ks0108.SimulatedDisplay(backend = pylcd.DummyBackend, pinmap = PINMAP, debug = False)
	draw = pylcd.ks0108.GraphicsFactory(display)
	
	"""display.commit(full = True, live = False)
	display.draw_rectangle(0, 0, 63, 63, fill = True, clear = False)
	display.draw_rectangle(5, 5, 58, 58, fill = True, clear = True)
	display.draw_rectangle(10, 10, 53, 53, fill = True, clear = False)
	display.draw_rectangle(15, 15, 48, 48, fill = True, clear = True)
	display.draw_rectangle(20, 20, 43, 43, fill = True, clear = False)
	display.draw_rectangle(25, 25, 38, 38, fill = True, clear = True)
	display.draw_rectangle(30, 30, 33, 33, fill = True, clear = False)"""
	
	"""display.draw_circle(95, 31, 32, fill = True, clear = False)
	display.draw_circle(95, 31, 27, fill = True, clear = True)
	display.draw_circle(95, 31, 22, fill = True, clear = False)
	display.draw_circle(95, 31, 17, fill = True, clear = True)
	display.draw_circle(95, 31, 12, fill = True, clear = False)
	display.draw_circle(95, 31, 7, fill = True, clear = True)
	
	display.draw_line(95, 0, 95, 63)
	display.draw_line(64, 31, 127, 31)"""
	
	# draw.fill_screen(drawer.PATTERN_SOLID)
	draw.draw_analog_clock(32, 32, 31, 23, 23, 40, has_lines = True, fill = False, clear = False)
	display.commit()

if __name__ == "__main__":
	main()