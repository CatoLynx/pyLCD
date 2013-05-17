# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

import sys
import time
from .utils import *

class K8055Backend:
	def __init__(self, display, pinmap, board = None, port = 0):
		self.display = display
		if board:
			self.board = board
		else:
			try:
				import pyk8055
				self.board = pyk8055.k8055(port)
			except:
				raise IOError("Could not establish a connection to the K8055 board.")
		
		self.reverse_pinmap = dict([(value, key) for key, value in pinmap.iteritems()])
		for pin, output in pinmap.iteritems():
			setattr(self, 'PIN_%s' % pin, output)
			if pin == 'LED':
				self.led_pwm = output > 8
	
	def high(self, output):
		self.board.SetDigitalChannel(output)
	
	def low(self, output):
		self.board.ClearDigitalChannel(output)
	
	def pulse(self, output):
		self.high(output)
		self.low(output)
	
	def all_low(self):
		self.board.ClearAllDigital()
		self.board.ClearAllAnalog()
	
	def write_nibble(self, nibble, data = True):
		mask = nibble_to_mask(nibble, data = data)
		self.board.WriteAllDigital(mask)
	
	def write_byte(self, byte, data = True):
		return self.write_nibble(byte, data = data)
	
	def set_brightness(self, level):
		assert level >= 0
		assert level <= 1023
		self.display.brightness = level
		if self.led_pwm:
			level = int(level * (255.0 / 1023.0))
			self.board.OutputAnalogChannel(self.PIN_LED - 8, level)
		else:
			if level > 0:
				self.board.SetDigitalChannel(self.PIN_LED)
			else:
				self.board.ClearDigitalChannel(self.PIN_LED)

class GPIOBackend:
	def __init__(self, display, pinmap):
		self.display = display
		try:
			import wiringpi
			self.gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_GPIO)
		except:
			raise IOError("Could not export the GPIO pins. Make sure that you have the wiringpi library installed, run as root and are on a Raspberry Pi.")
		
		self.reverse_pinmap = dict([(value, key) for key, value in pinmap.iteritems()])
		for pin, output in pinmap.iteritems():
			setattr(self, 'PIN_%s' % pin, output)
			if pin == 'LED':
				self.led_pwm = output == 18
			self.gpio.pinMode(output, self.gpio.PWM_OUTPUT if pin == 'LED' and self.led_pwm else self.gpio.OUTPUT)
	
	def high(self, output):
		self.gpio.digitalWrite(output, True)
	
	def low(self, output):
		self.gpio.digitalWrite(output, False)
	
	def pulse(self, output):
		self.high(output)
		time.sleep(0.001)
		self.low(output)
	
	def all_low(self):
		for output in self.reverse_pinmap.keys():
			self.low(output)
	
	def write_nibble(self, nibble, data = True):
		self.gpio.digitalWrite(self.PIN_RS, data)
		self.gpio.digitalWrite(self.PIN_D4, nibble[3])
		self.gpio.digitalWrite(self.PIN_D5, nibble[2])
		self.gpio.digitalWrite(self.PIN_D6, nibble[1])
		self.gpio.digitalWrite(self.PIN_D7, nibble[0])
	
	def write_byte(self, byte, data = True):
		self.gpio.digitalWrite(self.PIN_RS, data)
		for i in range(8):
			self.gpio.digitalWrite(getattr(self, "PIN_D%i" % i), byte[i])
	
	def set_brightness(self, level):
		assert level >= 0
		assert level <= 1023
		self.display.brightness = level
		if self.led_pwm:
			self.gpio.pwmWrite(self.PIN_LED, level)
		else:
			self.gpio.digitalWrite(self.PIN_LED, level > 0)

class ArduinoBackend:
	def __init__(self, display, pinmap, device = "/dev/ttyACM0", pwm_outputs = [3, 5, 6, 9, 10, 11]):
		self.display = display
		try:
			import serial
			self.serial = serial.serial_for_url(device, timeout = 0)
		except:
			raise IOError("Could not open the Arduino. Make sure you are running as root and are using the correct device name.")
		
		self.reverse_pinmap = dict([(value, key) for key, value in pinmap.iteritems()])
		for pin, output in pinmap.iteritems():
			setattr(self, 'PIN_%s' % pin, output)
			if pin == 'LED':
				self.led_pwm = output in pwm_outputs
	
	def high(self, output):
		self.serial.write("".join(chr(b) for b in [output, 1]))
	
	def low(self, output):
		self.serial.write("".join(chr(b) for b in [output, 0]))
	
	def pulse(self, output):
		self.high(output)
		self.low(output)
	
	def all_low(self):
		for output in self.reverse_pinmap.keys():
			self.low(output)
	
	def write_nibble(self, nibble, data = True):
		self.serial.write("".join(chr(b) for b in [self.PIN_RS, int(data), self.PIN_D4, int(nibble[3]), self.PIN_D5, int(nibble[2]), self.PIN_D6, int(nibble[1]), self.PIN_D7, int(nibble[0])]))
	
	def write_byte(self, byte, data = True):
		raise NotImplementedError
	
	def set_brightness(self, level):
		assert level >= 0
		assert level <= 1023
		self.display.brightness = level
		if self.led_pwm:
			level = int(level * (255.0 / 1023.0))
			self.serial.write("".join(chr(b) for b in [self.PIN_LED, level]))
		else:
			self.serial.write("".join(chr(b) for b in [self.PIN_LED, int(level > 0)]))

class DebugBackend:
	def __init__(self, display, pinmap, led_pwm = False, delay = 0.01):
		self.display = display
		self.led_pwm = led_pwm
		self.delay = delay
		self.printed = False
		self.output_states = [
			['RS', False],
			['RW', False],
			['E', False],
			['D0', False],
			['D1', False],
			['D2', False],
			['D3', False],
			['D4', False],
			['D5', False],
			['D6', False],
			['D7', False],
			['LED', False],
		]
		self.pinmap = dict([(key, [_key for _key, value in self.output_states].index(key)) for key, value in pinmap.iteritems()])
		self.reverse_pinmap = dict([(value, key) for key, value in pinmap.iteritems()])
		for pin, output in self.pinmap.iteritems():
			setattr(self, 'PIN_%s' % pin, output)
		sys.stdout.write("\033[?25l")
	
	def _update(self):
		if not self.printed:
			sys.stdout.write(" ".join([key.ljust(3) for key, value in self.output_states]) + "\n")
			self.printed = True
		sys.stdout.write("\r" + " ".join(["#  " if value else "-  " for key, value in self.output_states]))
		sys.stdout.flush()
		time.sleep(self.delay)
	
	def high(self, output):
		self.output_states[output][1] = True
		self._update()
	
	def low(self, output):
		self.output_states[output][1] = False
		self._update()
	
	def pulse(self, output):
		self.high(output)
		self.low(output)
	
	def all_low(self):
		self.output_states = [[key, False] for key, value in self.output_states]
		self._update()
	
	def write_nibble(self, nibble, data = True):
		self.output_states[self.PIN_RS][1] = data
		self.output_states[self.PIN_D4][1] = nibble[3]
		self.output_states[self.PIN_D5][1] = nibble[2]
		self.output_states[self.PIN_D6][1] = nibble[1]
		self.output_states[self.PIN_D7][1] = nibble[0]
		self._update()
	
	def write_byte(self, byte, data = True):
		raise NotImplementedError
	
	def set_brightness(self, level):
		assert level >= 0
		assert level <= 1023
		self.display.brightness = level
		if self.led_pwm:
			raise NotImplementedError("Later.")
		else:
			self.output_states[self.PIN_LED][1] = level > 0
		self._update()

class DummyBackend:
	def __init__(self, display, pinmap):
		pass
	
	def __getattr__(self, descriptor):
		return None
	
	def _update(self):
		pass
	
	def high(self, output):
		pass
	
	def low(self, output):
		pass
	
	def pulse(self, output):
		pass
	
	def all_low(self):
		pass
	
	def write_nibble(self, nibble, data = True):
		pass
	
	def write_byte(self, byte, data = True):
		pass
	
	def set_brightness(self, level):
		pass
