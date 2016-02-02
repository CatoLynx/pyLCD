#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013-2016 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to display an image on a GLCD
"""

import argparse
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
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--image', type = str, required = True)
	parser.add_argument('-x', '--x-pos', type = int, default = 0)
	parser.add_argument('-y', '--y-pos', type = int, default = 0)
	parser.add_argument('-t', '--threshold', type = int, default = 127)
	parser.add_argument('-a', '--angle', type = int, default = 0)
	args = parser.parse_args()
	
	display = pylcd.ks0108.Display(backend = pylcd.GPIOBackend, pinmap = PINMAP, debug = False)
	draw = pylcd.ks0108.DisplayDraw(display)
	display.commit(full = True)
	display.clear()
	draw.image(args.image, args.x_pos, args.y_pos, threshold = args.threshold, angle = args.angle)
	display.commit()

if __name__ == "__main__":
	main()
