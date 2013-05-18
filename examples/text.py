#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to display simple text on a HD44780 LCD
"""

import pylcd
import sys

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

def main():
	display = pylcd.hd44780.Display(backend = pylcd.GPIOBackend, pinmap = PINMAP, lines = 4, columns = 16, debug = False)
	display.clear()
	display.home()
	ui = pylcd.hd44780.DisplayUI(display, pylcd.NoInput, debug = False)
	
	if sys.stdin.isatty():
		text = " ".join(sys.argv[1:])
	else:
		text = sys.stdin.read()
	
	ui.message(text)

if __name__ == "__main__":
	main()