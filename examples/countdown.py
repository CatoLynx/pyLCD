#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to display a countdown to a specified time
"""

import argparse
import datetime
import pylcd
import re
import time
from string import Template

PINMAP = {
	'RS': 2,
	'RW': 3,
	'E': 4,
	'D4': 22,
	'D5': 10,
	'D6': 9,
	'D7': 11,
	'LED': 18,
}

CHARMAP = {
	0: (
		0b00000,
		0b10000,
		0b01000,
		0b00100,
		0b00010,
		0b00001,
		0b00000,
		0b00000,
	),
	1: (
		0b11111,
		0b00000,
		0b00000,
		0b00000,
		0b00000,
		0b00000,
		0b00000,
		0b00000,
	),
	2: (
		0b00000,
		0b10001,
		0b01110,
		0b00000,
		0b00000,
		0b00000,
		0b00000,
		0b00000,
	),
	3: (
		0b00111,
		0b00100,
		0b10100,
		0b00111,
		0b00100,
		0b10100,
		0b00111,
		0b00000,
	),
}

class DeltaTemplate(Template):
	delimiter = "%"

def build_countdown(delta, event, fmt):
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
	
	t = DeltaTemplate(fmt)
	formatted_delta = t.substitute(E = event, Y = years, D = days, H = "%02i" % hours, M = "%02i" % minutes, S = "%02i" % seconds, U = microseconds, TD = total_days, TH = total_hours, TM = total_minutes, TS = total_seconds)
	if "%U" in fmt:
		interval = 0.1
	elif "%S" in fmt or "%TS" in fmt:
		interval = 1
	elif "%M" in fmt or "%TM" in fmt:
		interval = 60
	elif "%H" in fmt or "%TH" in fmt:
		interval = 60 * 60
	elif "%D" in fmt or "%TD" in fmt:
		interval = 60 * 60 * 24
	elif "%Y" in fmt:
		interval = 60 * 60 * 24 * 365
	else:
		interval = 60
	return formatted_delta, interval

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-t', '--time', help = "The time to count down to.")
	parser.add_argument('-tf', '--timeformat', default = "%d.%m.%Y %H:%M:%S", help = "The format string to parse the target time, e.g. '%%d.%%m.%%Y %%H:%%M:%%S'")
	parser.add_argument('-f', '--format', help = "The format string for the countdown, e.g. '%%Y years %%D days %%H hours %%M minutes %%S seconds %%U microseconds %%TD total days %%TH total hours %%TM total minutes %%TS total seconds until %%E'")
	parser.add_argument('-a', '--align', choices = ['left', 'center', 'right'], default = 'center')
	parser.add_argument('-e', '--event', help = "The name of the event to count down to.")
	args = parser.parse_args()
	args.format = re.sub(r"\\(?P<id>\d+)", lambda match: chr(int(match.groupdict()['id'])), args.format)
	display = pylcd.hd44780.Display(backend = pylcd.GPIOBackend, pinmap = PINMAP, charmap = CHARMAP, lines = 4, columns = 16, debug = False)
	display.clear()
	display.home()
	ui = pylcd.hd44780.DisplayUI(display, pylcd.NoInput, debug = True)
	while True:
		now = datetime.datetime.now()
		target = datetime.datetime.strptime(args.time, args.timeformat)
		delta = target - now
		if delta.total_seconds() <= 0:
			break
		text, interval = build_countdown(delta, args.event, args.format)
		ui.message(text, align = args.align)
		time.sleep(interval)

if __name__ == "__main__":
	main()