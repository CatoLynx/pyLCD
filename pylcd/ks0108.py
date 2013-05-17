# -*- coding: utf-8 -*-
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
Library for KS0108 compatible graphical LCDs
"""

import math
import os
import re
import time
import warnings

from copy import deepcopy
try:
	from PIL import Image, ImageDraw, ImageFont
except ImportError:
	IMAGE = False
else:
	IMAGE = True

from .backends import *
from .inputs import *
from .utils import *

class Display:
	def __init__(self, backend, pinmap, auto_commit = False, backend_args = (), backend_kwargs = {}, skip_init = False, enable_backlight = True, debug = False):
		self.backend = backend(self, pinmap, *backend_args, **backend_kwargs)
		self.auto_commit = auto_commit
		self.brightness = 0
		self.debug = debug
		self.rows = 64
		self.columns = 128
		self.pages = self.rows / 8
		self.content = [[[0 for z in range(8)] for x in range(self.pages)] for y in range(self.columns)]
		self.old_content = deepcopy(self.content)
		self.cursor_pos = [0, 0]
		self.current_chip = 1
		self.set_brightness = self.backend.set_brightness
		self.write_byte = self.backend.write_byte
		self.backend.all_low()
		if enable_backlight:
			self.set_brightness(1023)
		if not skip_init:
			self.initialize()
			self.set_cursor_position(0, 0)
	
	def shutdown(self):
		self.clear()
		self.backend.all_low()
		self.set_brightness(0)
	
	def commit(self, full = False):
		for x in range(self.columns):
			for y in range(self.pages):
				if full or (not full and self.content[x][y] != self.old_content[x][y]):
					# print "Writing page %ix%i: %s" % (x, y, bin(byte_to_value(self.content[x][y])))
					self.write_page(byte_to_value(self.content[x][y]), x, y, commit = True)
		self.old_content = deepcopy(self.content)
		self.set_cursor_position(0, 0)
	
	def write_value(self, value, chip = None, data = True):
		if chip is None:
			chip = self.current_chip
		byte = value_to_byte(value)
		self.backend.high(getattr(self.backend, "PIN_CS%i" % chip))
		self.write_byte(byte, data = data)
		self.backend.pulse(self.backend.PIN_E)
		self.backend.low(getattr(self.backend, "PIN_CS%i" % chip))
	
	def initialize(self):
		self.reset()
		self.set_start_line(0)
		self.set_display_enable(True)
	
	def reset(self):
		self.backend.low(self.backend.PIN_RST)
		self.backend.high(self.backend.PIN_RST)
	
	def clear(self):
		self.content = [[[0 for z in range(8)] for x in range(self.pages)] for y in range(self.columns)]
		if self.auto_commit:
			self.commit()
	
	def set_cursor_position(self, x = 0, y = 0, internal = False):
		if not internal:
			cur_x, cur_y = self.cursor_pos
			cur_page = divmod(cur_y, 8)[0]
			page = divmod(y, 8)[0]
			if page != cur_page:
				self.set_page(page)
			if x != cur_x:
				self.set_column(x)
		self.cursor_pos = [x, y]
	
	def set_display_enable(self, on = True):
		self.backend.high(self.backend.PIN_CS2)
		self.write_value(0b01111100 + (int(on) << 7), chip = 1, data = False)
		self.backend.low(self.backend.PIN_CS2)
	
	def set_column(self, column = 0):
		if column > 63:
			column -= 64
			self.current_chip = 2
		else:
			self.current_chip = 1
		self.write_value(0b00000010 + (column << 2), data = False)
	
	def set_page(self, page = 0):
		self.backend.high(self.backend.PIN_CS2)
		self.write_value(0b00011101 + (page << 5), data = False)
		self.backend.low(self.backend.PIN_CS2)
	
	def set_start_line(self, line = 0):
		self.backend.high(self.backend.PIN_CS2)
		self.write_value(0b00000011 + (line << 2), chip = 1, data = False)
		self.backend.low(self.backend.PIN_CS2)
	
	def write_page(self, value, column = None, page = None, commit = False):
		cur_x, cur_y = self.cursor_pos
		if page is None:
			page = divmod(cur_y, 8)[0]
		if column is None:
			column = cur_x
		
		if commit:
			self.set_cursor_position(column, page * 8)
			self.write_value(value)
			self.set_cursor_position(column + 1, page * 8, internal = True)
		else:
			self.content[column][page] = [int(item) for item in value_to_byte(value)]
			if self.auto_commit:
				self.commit()
	
	def draw_pixel(self, x, y, clear = False):
		if x >= self.columns or x < 0:
			return
		if y >= self.rows or y < 0:
			return
		page, pos = divmod(y, 8)
		self.content[x][page][pos] = int(not clear)
		if self.auto_commit:
			self.commit()
	
	def draw_line(self, start_x, start_y, stop_x, stop_y, clear = False):
		if start_x == stop_x:
			y_range = range(start_y, stop_y + 1) if stop_y >= start_y else range(stop_y, start_y + 1)
			for y in y_range:
				self.draw_pixel(start_x, y, clear = clear)
			return
		elif start_x > stop_x:
			start_x, stop_x = stop_x, start_x
			start_y, stop_y = stop_y, start_y
		
		m = float(stop_y - start_y) / float(stop_x - start_x)
		old_y = start_y
		for x in range(start_x, stop_x + 1):
			y = int(round(m * (x - start_x) + start_y))
			if y >= old_y:
				diff_range = range(old_y, y + 1)
			else:
				diff_range = range(y, old_y + 1)
			for i in diff_range:
				self.draw_pixel(x, i, clear = clear)
			self.draw_pixel(x, y, clear = clear)
			old_y = y
	
	def draw_rectangle(self, start_x, start_y, stop_x, stop_y, fill = False, clear = False):
		x_range = range(start_x, stop_x + 1) if stop_x >= start_x else range(stop_x, start_x + 1)
		y_range = range(start_y + 1, stop_y) if stop_y >= start_y else range(stop_y + 1, start_y)
		for x in x_range:
			if fill:
				for y in y_range:
					self.draw_pixel(x, y, clear = clear)
			else:
				self.draw_pixel(x, start_y, clear = clear)
				self.draw_pixel(x, stop_y, clear = clear)
		
		if not fill:
			for y in y_range:
				self.draw_pixel(start_x, y, clear = clear)
				self.draw_pixel(stop_x, y, clear = clear)
	
	def draw_circle(self, center_x, center_y, radiuses, start = 0, stop = 360, fill = False, clear = False):
		RESOLUTION = 360
		if type(radiuses) not in [list, tuple]:
			radiuses = [radiuses]
		interpolation_step_size = RESOLUTION / len(radiuses)
		complete_radiuses = [0.0] * RESOLUTION
		lambdas = []
		for i, item in enumerate(radiuses):
			next = radiuses[i + 1] if i < len(radiuses) - 1 else radiuses[0]
			# m = (float(next) - float(item)) / float(interpolation_step_size)
			# exec("_tmp = lambda x: %f * x + %i" % (m, item))
			b = math.log(float(next) / float(item)) / float(interpolation_step_size)
			# print "_tmp = lambda x: %f * math.e ** (%.10f * x)" % (item, b)
			exec("_tmp = lambda x: %f * math.e ** (%.10f * x)" % (item, b))
			lambdas.append(_tmp)
		
		for n, radius in enumerate(radiuses):
			for s in range(interpolation_step_size):
				complete_radiuses[n * interpolation_step_size + s] = lambdas[n](s)
		
		# print "\n".join([str(item) for item in complete_radiuses])
		
		for a, radius in enumerate(complete_radiuses):
			if a < start or a > stop:
				continue
			mod_x = int(round(math.sin(math.radians(a)) * radius))
			mod_y = int(round(math.cos(math.radians(a)) * radius))
			x, y = center_x + mod_x, center_y - mod_y
			
			if fill:
				self.draw_line(center_x, center_y, x, y, clear = clear)
			else:
				self.draw_pixel(x, y, clear = clear)
	
	def draw_image(self, image, x, y, width = None, height = None, condition = 'alpha > 127', clear = False):
		if not IMAGE:
			raise RuntimeError("PIL is required to display images, but it is not installed on your system.")
		if isinstance(image, Image.Image):
			im = image
		else:
			im = Image.open(image)
		im = im.convert("RGBA")
		pixels = im.load()
		im_width, im_height = im.size
		if width or height:
			width = width if width is not None else im_width
			height = height if height is not None else im_height
			im = im.resize((width, height), Image.ANTIALIAS)
			im_width, im_height = im.size
			pixels = im.load()
		
		if x == 'left':
			x = 0
		elif x == 'center':
			x = (self.columns - im_width) / 2
		elif x == 'right':
			x = self.columns - im_width
		
		if y == 'top':
			y = 0
		elif y == 'middle':
			y = (self.rows - im_height) / 2
		elif y == 'bottom':
			y = self.rows - im_height
		
		for im_x in range(im_width):
			for im_y in range(im_height):
				red, green, blue, alpha = pixels[im_x, im_y]
				exec("draw = %s" % condition.replace(";", ""))
				if draw:
					self.draw_pixel(x + im_x, y + im_y, clear = clear)
	
	def draw_text(self, text, x, y, size = 10, font = "/usr/share/fonts/truetype/freefont/FreeSans.ttf", clear = False):
		if not IMAGE:
			raise RuntimeError("PIL is required to display images, but it is not installed on your system.")
		font = ImageFont.truetype(font, size)
		size = font.getsize(text)
		image = Image.new('RGBA', size, (0, 0, 0, 0))
		draw = ImageDraw.Draw(image)
		draw.text((0, 0), text, (0, 0, 0), font = font)
		self.draw_image(image, x, y, clear = clear)

class SimulatedDisplay(Display):
	def __init__(self, *args, **kwargs):
		if not IMAGE:
			raise RuntimeError("PIL is required to display images, but it is not installed on your system.")
		Display.__init__(self, *args, **kwargs)
		self.outfile = "display.png"
		self.bg = (0, 0, 255)
		self.fg = (255, 255, 255)
		if False and os.path.exists(self.outfile):
			self.image = Image.open(self.outfile)
		else:
			self.image = Image.new("RGB", (self.columns, self.rows), self.bg)
			self.image.save(self.outfile, "PNG")
		self.pixels = self.image.load()
	
	def commit(self, *args, **kwargs):
		Display.commit(self, *args, **kwargs)
		self.image.save(self.outfile, "PNG")
	
	def write_page(self, value, column = None, page = None, commit = False):
		cur_x, cur_y = self.cursor_pos
		if page is None:
			page = divmod(cur_y, 8)[0]
		if column is None:
			column = cur_x
		
		if commit:
			byte = value_to_byte(value)
			self.set_cursor_position(column, page * 8)
			for i in range(len(byte)):
				self.pixels[column, (page * 8) + i] = self.fg if byte[i] else self.bg
			self.set_cursor_position(column + 1, page * 8, internal = True)
		else:
			self.content[column][page] = [int(item) for item in value_to_byte(value)]
			if self.auto_commit:
				self.commit()