# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

import sys
import termios
import time
import tty

from .backends import GPIOBackend

class SystemInput:
	def __init__(self, ui):
		self.buffer = []
		self.in_seq = False
		self.seq = []

	def read_key(self):
		if sys.stdin.isatty():
			fd = sys.stdin.fileno()
			old_settings = termios.tcgetattr(fd)
			try:
				tty.setraw(sys.stdin.fileno())
				char = sys.stdin.read(1)
				code = ord(char)
				if code == 3:
					raise KeyboardInterrupt
				if code == 27:
					self.in_seq = True
				if self.in_seq:
					self.seq.append(char)
					if len(self.seq) == 3:
						self.in_seq = False
						seq = self.seq[:]
						self.seq = []
						return "".join(seq)
					return
			finally:
				termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		else:
			if not self.buffer:
				self.buffer = list(sys.stdin.read())
			try:
				char = self.buffer.pop(0)
			except IndexError:
				raise SystemExit
		return char
	
	def set_error(self, state):
		return False
	
	def set_ready(self, state):
		return False

class GPIOInput:
	def __init__(self, ui, pinmap):
		if not isinstance(ui.display.backend, GPIOBackend):
			raise NotImplementedError("The GPIO input module can only be used with the GPIO backend.")
		
		self.key_pressed = False
		
		import wiringpi
		self.ui = ui
		self.gpio = self.ui.display.backend.gpio
		self.reverse_pinmap = dict([(value, key) for key, value in pinmap.iteritems()])
		for pin, output in pinmap.iteritems():
			setattr(self, 'PIN_%s' % pin, output)
			is_input = pin in ('UP', 'LEFT', 'OK', 'RIGHT', 'DOWN')
			self.gpio.pinMode(output, self.gpio.INPUT if is_input else self.gpio.OUTPUT)
			if is_input:
				wiringpi.pullUpDnControl(output, wiringpi.PUD_UP)
	
	def read_key(self):
		self.set_ready(True)
		while True:
			up = not self.gpio.digitalRead(self.PIN_UP)
			left = not self.gpio.digitalRead(self.PIN_LEFT)
			ok = not self.gpio.digitalRead(self.PIN_OK)
			right = not self.gpio.digitalRead(self.PIN_RIGHT)
			down = not self.gpio.digitalRead(self.PIN_DOWN)
			
			if ok and left:
				if not self.key_pressed:
					self.key_pressed = True
					self.set_ready(False)
					raise KeyboardInterrupt
			elif up:
				if not self.key_pressed:
					self.key_pressed = True
					self.set_ready(False)
					return "\x1b[A"
			elif left:
				if not self.key_pressed:
					self.key_pressed = True
					self.set_ready(False)
					return "\x1b[D"
			elif ok:
				if not self.key_pressed:
					self.key_pressed = True
					self.set_ready(False)
					return chr(13)
			elif right:
				if not self.key_pressed:
					self.key_pressed = True
					self.set_ready(False)
					return "\x1b[C"
			elif down:
				if not self.key_pressed:
					self.key_pressed = True
					self.set_ready(False)
					return "\x1b[B"
			else:
				self.key_pressed = False
			time.sleep(0.025)
	
	def set_error(self, state):
		if state:
			self.ui.display.backend.high(self.PIN_ERROR)
		else:
			self.ui.display.backend.low(self.PIN_ERROR)
	
	def set_ready(self, state):
		if state:
			self.ui.display.backend.high(self.PIN_READY)
		else:
			self.ui.display.backend.low(self.PIN_READY)

class NoInput:
	def __init__(self, ui):
		pass

	def read_key(self):
		while True:
			time.sleep(1)
	
	def set_error(self, state):
		return False
	
	def set_ready(self, state):
		return False