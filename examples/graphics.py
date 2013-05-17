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
	display = pylcd.ks0108.Display(backend = pylcd.GPIOBackend, pinmap = PINMAP, debug = False)
	display.commit(full = True)
	display.set_display_enable(True)
	display.draw_line(0, 0, 127, 63)
	display.draw_line(0, 63, 127, 0)
	display.commit()

if __name__ == "__main__":
	main()