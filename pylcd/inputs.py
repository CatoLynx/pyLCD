# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

import datetime
import sys
import termios
import time
import tty

class SystemInput:
	def __init__(self, ui = None):
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
	
	def read_key_states(self):
		return {}
	
	def read_pressed_keys(self):
		return []
	
	def set_output(self, name, state):
		pass

class GPIOInput:
	def __init__(self, pinmap):
		try:
			import wiringpi
			self.gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_GPIO)
		except:
			raise IOError("Could not export the GPIO pins. Make sure that you have the wiringpi library installed, run as root and are on a Raspberry Pi.")
		
		self.pinmap = dict([(key, value if type(value) in [list, tuple] else (value, False, 1)) for key, value in pinmap.iteritems()])
		self.reverse_pinmap = dict([(value[0], key) for key, value in self.pinmap.iteritems()])
		for name, pin_data in self.pinmap.iteritems():
			pin, output, pullup = pin_data
			
			setattr(self, 'PIN_%s' % name, pin)
			self.gpio.pinMode(pin, self.gpio.OUTPUT if output else self.gpio.INPUT)
			if pullup != 0:
				wiringpi.pullUpDnControl(pin, wiringpi.PUD_UP if pullup > 0 else wiringpi.PUD_DOWN)
	
	def read_key_states(self):
		states = {}
		for name, pin_data in self.pinmap.iteritems():
			pin, output, pullup = pin_data
			if output:
				continue
			states[name] = not self.gpio.digitalRead(pin) if pullup else self.gpio.digitalRead(pin)
		
		return states
	
	def read_pressed_keys(self):
		states = self.read_key_states()
		return [name for name, state in states.iteritems() if state]
	
	def read_key(self, timeout = None):
		if timeout:
			start = datetime.datetime.now()
		while True:
			keys = self.read_pressed_keys()
			if keys:
				return keys[0]
			if timeout:
				secs = (datetime.datetime.now() - start).total_seconds()
				if secs >= timeout:
					return None
			time.sleep(0.1)
	
	def set_output(self, name, state):
		if name not in self.pinmap:
			raise ValueError("No '%s' pin configured" % name)
		
		self.gpio.digitalWrite(self.pinmap[name], state)

class NoInput:
	def __init__(self, ui):
		pass
	
	def read_key_states(self):
		return {}
	
	def read_pressed_keys(self):
		return []
	
	def read_key(self):
		while True:
			time.sleep(1)
	
	def set_output(self, name, state):
		pass