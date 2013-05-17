# -*- coding: utf-8 -*-
# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

"""
Library for HD44780 compatible character LCDs
"""

import re
import time
import warnings

from .backends import *
from .inputs import *
from .utils import *

class Display:
	CONTROL_CHARACTERS = (0x0D, 0x18, 0x1B, 0x7F)
	
	def __init__(self, backend, pinmap, charmap = None, lines = 2, columns = 16, characters = 80, backend_args = (), backend_kwargs = {}, skip_init = False, enable_backlight = True, debug = False):
		self.backend = backend(self, pinmap, *backend_args, **backend_kwargs)
		self.brightness = 0
		self.debug = debug
		self.line_count = lines
		self.column_count = columns
		self.character_count = characters
		self.max_chars_per_line = self.character_count / lines
		self.lines = ()
		self.cursor_pos = [0, 0]
		self.set_brightness = self.backend.set_brightness
		self.write_nibble = self.backend.write_nibble
		self.backend.all_low()
		if enable_backlight:
			self.set_brightness(1023)
		if not skip_init:
			self.initialize()
			if charmap:
				if 'dir' in charmap:
					files = os.listdir(charmap['dir'])
					for filename in files:
						charmap[int(filename.split(".")[0])] = open(os.path.join(charmap['dir'], filename), 'rb')
					del charmap['dir']
				for pos, char in charmap.iteritems():
					self.load_custom_character(pos, char)
			self.set_cursor_position(0, 0)
	
	def shutdown(self):
		self.clear()
		self.backend.all_low()
		self.set_brightness(0)
	
	def write_value(self, value, data = True):
		if self.debug:
			print "Writing   %i / %s / %s / %s" % (value, hex(value), bin(value), chr(value))
		nibbles = value_to_nibbles(value)
		if data:
			self.backend.high(self.backend.PIN_RS)
			self.cursor_pos[0] += 1
		self.write_nibble(nibbles[0], data = data)
		self.backend.pulse(self.backend.PIN_E)
		self.write_nibble(nibbles[1], data = data)
		self.backend.pulse(self.backend.PIN_E)
		self.write_nibble((False, False, False, False), data = False)
	
	def update_internal_lines(self, lines):
		self.lines = lines
	
	def split_lines(self, string):
		lines = string.splitlines()
		return lines
	
	def _custom_sub(self, match):
		num = int(match.groupdict()['num'])
		return chr(num)
	
	def write_string(self, string, parse_custom = True, update = False, align = 'left'):
		if parse_custom:
			string = re.sub(r"<(?P<num>[0-7])>", self._custom_sub, string)
		
		lines = self.split_lines(string)
		if align == 'left':
			pass
		elif align == 'center':
			lines = [line.center(self.column_count) for line in lines]
		elif align == 'right':
			lines = [line.rjust(self.column_count) for line in lines]
		if update:
			return self.update(lines)
		pos = self.cursor_pos[:]
		for i in range(len(lines)):
			self.set_cursor_position(pos[0], pos[1] + i)
			for char in lines[i]:
				self.write_value(ord(char))
		self.update_internal_lines(lines)
	
	def cycle_strings(self, strings, delay = 5.0, count = -1, *args, **kwargs):
		i = 0
		while count == -1 or i < count:
			i += 1
			for string in strings:
				self.write_string(string, *args, **kwargs)
				time.sleep(delay)
	
	def update(self, string):
		lines = self.split_lines(string)
		old_lines = self.lines[:]
		lens = [len(line) for line in lines]
		old_lens = [len(line) for line in old_lines]
		for i in range(len(lines)):
			for n in range(lens[i]):
				if lines[i][n] != old_lines[i][n:n + 1]:
					self.set_cursor_position(n, i)
					self.write_value(ord(lines[i][n]))
			if lens[i] < old_lens[i]:
				self.set_cursor_position(lens[i], i)
				self.write_string(" " * (old_lens[i] - lens[i]))
		self.update_internal_lines(lines)
	
	def initialize(self):
		self.write_nibble((False, False, True, True), data = False)
		self.backend.pulse(self.backend.PIN_E)
		self.backend.pulse(self.backend.PIN_E)
		self.backend.pulse(self.backend.PIN_E)
		self.write_nibble((False, False, True, False), data = False)
		self.backend.pulse(self.backend.PIN_E)
		self.set_configuration(multiline = True)
		self.set_display_enable(enable = True, cursor = False)
	
	def clear(self):
		self.write_value(0b00000001, data = False)
	
	def home(self):
		self.write_value(0b00000010, data = False)
		self.cursor_pos = [0, 0]
	
	def set_entry_mode(self, rtl = False, scroll = True):
		_rtl = 0b00000010 if rtl else 0b00000000
		_scroll = 0b00000001 if scroll else 0b00000000
		self.write_value(0b00000100 + _rtl + _scroll, data = False)
	
	def set_display_enable(self, enable = True, cursor = False, cursor_blink = False):
		_enable = 0b00000100 if enable else 0b00000000
		_cursor = 0b00000010 if cursor else 0b00000000
		_cursor_blink = 0b00000001 if cursor_blink else 0b00000000
		self.write_value(0b00001000 + _enable + _cursor + _cursor_blink, data = False)
	
	def scroll(self, right = False):
		_right = 0b00000100 if right else 0b00000000
		self.write_value(0b00011000 + _right, data = False)
	
	def move_cursor(self, left = False):
		_left = 0b00000000 if left else 0b00000100
		self.write_value(0b00010000 + _left, data = False)
		if left:
			self.cursor_pos[0] -= 1
		else:
			self.cursor_pos[0] += 1
	
	def set_configuration(self, multiline = True, five_seven_font = True):
		_multiline = 0b00001000 if multiline else 0b00000000
		_five_seven_font = 0b00000100 if five_seven_font else 0b00000000
		self.write_value(0b00100000 + _multiline + _five_seven_font, data = False)
	
	def set_cursor_position(self, column = 0, line = 0):
		if line == 1:
			_line = 0xC0
		elif line == 2:
			_line = 0x90
		elif line == 3:
			_line = 0xD0
		else:
			line = 0
			_line = 0x80
		self.cursor_pos = [column, line]
		self.write_value(_line + column, data = False)
	
	def char_from_file(self, f):
		image = Image.open(f)
		pixels = image.load()
		f.close()
		if image.size != (5, 8):
			return False
		char = [[]] * 8
		for y in range(len(char)):
			char[y] = []
			for x in range(5):
				pix = pixels[4 - x, y]
				char[y].append(sum(pix) / len(pix) <= 127)
			char[y] = bool_list_to_mask(char[y])
		char = tuple(char)
		return char
	
	def load_custom_character(self, pos, char):
		if type(char) is file:
			_char = self.char_from_file(char)
			if not _char:
				return False
		else:
			_char = char
		for i in range(8):
			self.write_value(0b01000000 + (pos << 3) + i, data = False)
			self.write_value(_char[i])
	
	def backspace(self):
		self.move_cursor(left = True)
		self.write_value(0x20)
		self.move_cursor(left = True)
	
	def process_escape_sequence(self, seq):
		data = seq[1:]
		if data == "OH":
			return self.set_cursor_position(0, self.cursor_pos[1])
		elif data == "OF":
			return self.set_cursor_position(self.column_count - 1, self.cursor_pos[1])
		elif data == "[A":
			return self.set_cursor_position(self.cursor_pos[0], self.cursor_pos[1] - 1)
		elif data == "[B":
			return self.set_cursor_position(self.cursor_pos[0], self.cursor_pos[1] + 1)
		elif data == "[C":
			return self.move_cursor()
		elif data == "[D":
			return self.move_cursor(left = True)
		elif data == "[3~":
			return self.write_value(0x20)
		else:
			return False
	
	def process_control_character(self, char):
		code = ord(char)
		if code == 0x0D:
			return self.set_cursor_position(0, self.cursor_pos[1] + 1)
		elif code == 0x18:
			self.clear()
			self.home()
		elif code == 0x1B:
			return False
		elif code == 0x7F:
			return self.backspace()
		else:
			return False
	
	def write(self, data, *args, **kwargs):
		if data is None:
			return False
		t = type(data)
		if t is int:
			return self.write_value(data)
		elif t in [str, unicode]:
			if data.startswith(chr(27)):
				return self.process_escape_sequence(data)
			else:
				if len(data) == 1 and ord(data) in self.CONTROL_CHARACTERS:
					return self.process_control_character(data)
				else:
					return self.write_string(data, *args, **kwargs)
		elif t in [list, tuple]:
			return self.cycle_strings(data, *args, **kwargs)
		elif t is file:
			return self.write_string(data.read(), *args, **kwargs)
		else:
			return self.write_string(str(data), *args, **kwargs)

class DisplayUI:
	KEY_LEFT = "\x1b[D"
	KEY_RIGHT = "\x1b[C"
	KEY_UP = "\x1b[A"
	KEY_DOWN = "\x1b[B"
	KEY_ENTER = chr(13)
	
	class ProgressBar:
		def __init__(self, ui, title, fraction, char, align):
			self.ui = ui
			self.title = title
			self.fraction = fraction
			self.char = char
			self.align = align
		
		def update(self, title = None, fraction = None, char = None, align = None):
			self.title = title or self.title
			self.fraction = fraction or self.fraction
			self.char = char or self.char
			self.align = align or self.align
			self = self.ui.progress_bar(title = self.title, fraction = self.fraction, char = self.char, align = self.align)
	
	def __init__(self, display, input_module, input_args = (), input_kwargs = {}, debug = False):
		self.debug = debug
		self.current_lines = ()
		self.display = display
		self.displayed_lines = ()
		self.h_scroll_pos = 0
		self.input = input_module(self, *input_args, **input_kwargs)
		self.line_buffer = []
		self.viewport = ()
		self.v_scroll_pos = 0
		self.input.set_error(False)
		self.input.set_ready(True)
	
	def _chunks(self, seq, size):
		for i in range(0, len(seq), size):
			yield seq[i:i + size]
	
	def _shift(self, seq, amount):
		amount = divmod(amount, len(seq))[1]
		shifted = seq[-amount:] + seq[:-amount]
		return shifted
	
	def _align(self, line, align, width = None):
		width = width or self.display.column_count
		aligned_line = line
		if "\t" in line:
			parts = line.split("\t")
			parts = [parts[0], " ".join(parts[1:])]
			len2 = len(parts[1])
			len1 = width - (len2 + 1)
			parts[0] = parts[0][:len1].ljust(len1)
			aligned_line = " ".join(parts)
		else:
			if align == 'left':
				aligned_line = line.ljust(width)
			elif align == 'center':
				aligned_line = line.center(width)
			elif align == 'right':
				aligned_line = line.rjust(width)
		return aligned_line
	
	def shutdown(self):
		self.input.set_ready(False)
		self.input.set_error(False)
	
	def update(self, lines = None, home = True):
		if home:
			self.h_scroll_pos = 0
		if lines is not None:
			self.line_buffer = list(lines[:])
			if home:
				self.v_scroll_pos = 0
		self.line_buffer += [""] * (self.display.line_count - len(self.line_buffer))
		self.v_scroll_pos = min(len(self.line_buffer) - self.display.line_count, self.v_scroll_pos)
		lines = self.line_buffer[self.v_scroll_pos:self.v_scroll_pos + self.display.line_count]
		self.stored_lines = tuple([line[:self.display.column_count].ljust(self.display.column_count) if i < 2 and self.display.line_count > 2 else line[:self.display.max_chars_per_line].ljust(self.display.max_chars_per_line) for i, line in enumerate(lines)])
		self.displayed_lines = tuple([line[:self.display.column_count].ljust(self.display.column_count) if i < 2 and self.display.line_count > 2 else line[:self.display.max_chars_per_line].ljust(self.display.max_chars_per_line) for i, line in enumerate(lines)])
		self.viewport = tuple([self._shift(line, -self.h_scroll_pos)[:self.display.column_count] for line in self.displayed_lines])
	
	def redraw(self):
		if self.debug:
			header = "╔%s╗" % ("═" * self.display.column_count)
			footer = "╚%s╝" % ("═" * self.display.column_count)
			print header + "\n%s\n" % "\n".join(["║%s║" % line.ljust(self.display.column_count) for line in self.viewport]) + footer
		self.display.set_cursor_position(0, 0)
		self.display.write("\n".join(self.stored_lines))
	
	def clear(self):
		self.line_buffer = []
		self.update()
		self.display.clear()
		self.display.home()
	
	def format_buttons(self, buttons, active = 0):
		btn_width = self.display.column_count / len(buttons) - 2
		row = ("%s" * len(buttons)) % tuple([("<%s>" if active == buttons.index(button) else " %s ") % button[0][:btn_width].center(btn_width) for button in buttons])
		return row
	
	def format_list_entries(self, entries, align = 'center', active = 0):
		entry_width = self.display.column_count - 2
		rows = tuple([("<%s>" if active == entries.index(entry) else " %s ") % self._align(entry[0][:entry_width], align, entry_width) for entry in entries])
		return rows
	
	def format_lines(self, lines, align = 'left', wrap = True):
		_lines = []
		if wrap:
			for line in lines:
				_lines += self._chunks(line, self.display.column_count)
		else:
			_lines = lines
		formatted_lines = tuple([self._align(line, align) for line in _lines])
		return formatted_lines
	
	def format_slider(self, minimum, maximum, value, align = 'left', char = "*", fill_char = "-", style = 'slider'):
		val_width = max(len(str(minimum)), len(str(maximum))) + 1
		max_slider_width = self.display.column_count - val_width
		slider_width = int(max_slider_width * float(value) / (maximum - minimum))
		if style == 'bar':
			_row = char * slider_width
		else:
			_row = [fill_char] * max_slider_width
			index = int(slider_width * ((max_slider_width - 1) / float(max_slider_width)))
			_row[index] = char
			_row = "".join(_row)
		row = str(value).ljust(val_width) + _row
		return row
	
	def format_multiple_choice_entries(self, entries, align = 'center', active = 0, selected = [], char = "*"):
		entry_width = self.display.column_count - 4
		rows = []
		for entry in entries:
			if entries.index(entry) == active:
				row = ("[%s] %%s" % char if entries.index(entry) in selected else "[ ] %s") % self._align(entry[:entry_width], align, entry_width)
			else:
				row = (" %s  %%s" % char if entries.index(entry) in selected else "    %s") % self._align(entry[:entry_width], align, entry_width)
			rows.append(row)
		rows = tuple(rows)
		return rows
	
	def dialog(self, title, buttons = ("OK", ), align = 'left', active = 0, onchange = None, onchange_args = (), onchange_kwargs = {}):
		done = False
		while not done:
			title = self._align(title, align)
			buttons = tuple([(button, None) if type(button) in [str, unicode] else button for button in buttons])
			button_row = self.format_buttons(buttons, active = active)
			self.update((title, button_row))
			self.redraw()
			key = None
			while key is None:
				key = self.input.read_key()
			if key == self.KEY_LEFT:
				active = max(0, active - 1)
			elif key == self.KEY_RIGHT:
				active = min(active + 1, len(buttons) - 1)
			elif key == self.KEY_UP:
				self.v_scroll(-1)
			elif key == self.KEY_DOWN:
				self.v_scroll(1)
			elif key == self.KEY_ENTER:
				done = True
			if onchange:
				try:
					onchange(active, *onchange_args, **onchange_kwargs)
				except:
					warnings.warn("On-Change function of dialog element failed", RuntimeWarning)
		selected = buttons[active]
		if selected[1]:
			try:
				selected[1][0](*selected[1][1], **selected[1][2])
			except:
				pass
		return active, selected[0]
	
	def progress_bar(self, title, fraction = 0.0, char = "#", align = 'left'):
		assert type(char) in [str, unicode]
		title = self._align(title, align)
		char = char[0]
		count = int(self.display.column_count * fraction)
		bar = char * count
		self.update((title, bar))
		self.redraw()
		return self.ProgressBar(self, title, fraction, char, align)
	
	def list_dialog(self, title, entries, align = 'left', active = 0, onchange = None, onchange_args = (), onchange_kwargs = {}):
		done = False
		first_loop = True
		while not done:
			title = self._align(title, align)
			entries = tuple([(entry, None) if type(entry) in [str, unicode] else entry for entry in entries])
			entry_rows = self.format_list_entries(entries, align = align, active = active)
			self.update([title] + list(entry_rows), home = first_loop)
			self.redraw()
			first_loop = False
			key = None
			while key is None:
				key = self.input.read_key()
			if key == self.KEY_UP:
				active = max(0, active - 1)
				if active < self.v_scroll_pos - 1 or (active == 0 and divmod(len(entries), 2)[1] == 0):
					self.v_scroll(-2, redraw = False)
			elif key == self.KEY_DOWN:
				active = min(active + 1, len(entries) - 1)
				if active > self.v_scroll_pos:
					self.v_scroll(2, redraw = False)
			elif key == self.KEY_ENTER:
				done = True
			if onchange:
				try:
					onchange(active, *onchange_args, **onchange_kwargs)
				except:
					warnings.warn("On-Change function of list dialog element failed", RuntimeWarning)
		selected = entries[active]
		if selected[1]:
			try:
				selected[1][0](*selected[1][1], **selected[1][2])
			except:
				pass
		return active, selected[0]
	
	def input_dialog(self, title, align = 'left', onchange = None, onchange_args = (), onchange_kwargs = {}):
		done = False
		while not done:
			title = self._align(title, align)
			self.update([title], home = False)
			self.redraw()
			self.display.set_cursor_position(0, 1)
			response = ""
			while True:
				key = self.input.read_key()
				if key == self.KEY_ENTER:
					done = True
					break
				else:
					if key:
						response += key
					self.display.write(key)
				if onchange:
					try:
						onchange(response, *onchange_args, **onchange_kwargs)
					except:
						warnings.warn("On-Change function of text input element failed", RuntimeWarning)
		return response
	
	def slider_dialog(self, title, minimum = 0, maximum = 100, step = 1, big_step = 10, align = 'left', value = 0, char = "*", fill_char = "-", style = 'slider', onchange = None, onchange_args = (), onchange_kwargs = {}):
		assert value >= minimum
		assert value <= maximum
		done = False
		while not done:
			title = self._align(title, align)
			slider_row = self.format_slider(minimum, maximum, value, align = align, char = char, fill_char = fill_char, style = style)
			self.update((title, slider_row))
			self.redraw()
			key = None
			while key is None:
				key = self.input.read_key()
			if key == self.KEY_LEFT:
				value = max(value - step, minimum)
			elif key == self.KEY_RIGHT:
				value = min(value + step, maximum)
			elif key == self.KEY_UP:
				value = min(value + big_step, maximum)
			elif key == self.KEY_DOWN:
				value = max(value - big_step, minimum)
			elif key == self.KEY_ENTER:
				done = True
			if onchange:
				try:
					onchange(value, *onchange_args, **onchange_kwargs)
				except:
					warnings.warn("On-Change function of slider element failed", RuntimeWarning)
		return value
	
	def multiple_choice_dialog(self, title, entries, align = 'left', active = 0, selected = [], char = "*", onchange = None, onchange_args = (), onchange_kwargs = {}):
		done = False
		first_loop = True
		while not done:
			title = self._align(title, align)
			entry_rows = self.format_multiple_choice_entries(entries, align = align, active = active, selected = selected, char = char)
			self.update([title] + list(entry_rows), home = first_loop)
			self.redraw()
			first_loop = False
			key = None
			while key is None:
				key = self.input.read_key()
			if key == " ":
				if active in selected:
					selected.remove(active)
				else:
					selected.append(active)
			elif key == self.KEY_UP:
				active = max(0, active - 1)
				if active < self.v_scroll_pos - 1 or (active == 0 and divmod(len(entries), 2)[1] == 0):
					self.v_scroll(-2, redraw = False)
			elif key == self.KEY_DOWN:
				active = min(active + 1, len(entries) - 1)
				if active > self.v_scroll_pos:
					self.v_scroll(2, redraw = False)
			elif key == self.KEY_ENTER:
				done = True
			if onchange:
				try:
					onchange(selected, *onchange_args, **onchange_kwargs)
				except:
					warnings.warn("On-Change function of multiple choice dialog element failed", RuntimeWarning)
		selected = [(i, entries[i]) for i in sorted(selected)]
		return selected
	
	def message(self, data, align = 'left', wrap = True, duration = 0.0):
		if type(data) in [str, unicode]:
			data = data.splitlines()
		data = self.format_lines(data, align, wrap)
		self.update(data)
		self.redraw()
		time.sleep(duration)
	
	def v_scroll(self, amount = 1, to = None, redraw = True):
		if to is not None:
			amount = -(self.h_scroll_pos - to)
		l = len(self.line_buffer) - self.display.line_count
		self.v_scroll_pos = (self.v_scroll_pos + amount) if self.v_scroll_pos + amount > 0 else 0
		self.v_scroll_pos = self.v_scroll_pos if self.v_scroll_pos < l else l
		self.update(home = False)
		if redraw:
			self.redraw()
	
	def h_scroll(self, amount = 1, to = None):
		if to is not None:
			amount1 = -(self.h_scroll_pos - to)
			amount2 = self.display.max_chars_per_line * 2 + amount1
			amount = amount1 if abs(amount1) < abs(amount2) else amount2
		for i in range(abs(amount)):
			self.display.scroll(right = amount < 0)
		self.h_scroll_pos += amount
		while self.h_scroll_pos < 0:
			self.h_scroll_pos = self.display.max_chars_per_line * 2 + self.h_scroll_pos
		self.update(home = False)
	
	def dim(self, level, animate = True, delay = 0.001, duration = None):
		if level == self.display.brightness:
			return
		if animate:
			if duration is not None:
				p = duration / abs(level - self.display.brightness)
			else:
				p = delay
			mod = 1 if level > self.display.brightness else -1
			for i in range(self.display.brightness + mod, level + mod, mod):
				self.display.set_brightness(i)
				time.sleep(p)
		else:
			self.display.set_brightness(level)
