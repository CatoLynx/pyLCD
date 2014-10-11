#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Script to monitor the system state
"""

import datetime
import os
import psutil
import pxssh
import pylcd
import random
import socket
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

TEMP_PLOT_MAX_POINTS = 46
CPU_PLOT_MAX_POINTS = 112
LOAD_PLOT_MAX_POINTS = 112
TIMESTAMP_0 = datetime.datetime(1970, 1, 1, 0, 0, 0)

def main():
	try:
		brightness = int(sys.argv[1])
	except:
		brightness = 1023
	
	display = pylcd.ks0108.Display(backend = pylcd.GPIOBackend, pinmap = PINMAP, debug = False)
	draw = pylcd.ks0108.DisplayDraw(display)
	display.commit(full = True)
	
	display.set_brightness(brightness)
	
	ssh = pxssh.pxssh()
	
	plot_data = {
		'cpu_load': [],
		'load_avg': [],
		'cpu_temp': []
	}
	
	data_timestamps = {
		'cpu_load': TIMESTAMP_0,
		'ram_usage': TIMESTAMP_0,
		'disk_usage': TIMESTAMP_0,
		'ip_adress': TIMESTAMP_0,
		'cpu_temp': TIMESTAMP_0,
		'uptime': TIMESTAMP_0,
		'random_word': TIMESTAMP_0,
		'load_avg': TIMESTAMP_0,
		'ssh_data': TIMESTAMP_0,
	}
	
	while True:
		redraw = True
		timestamp_before_rebuild = datetime.datetime.now()
		display.clear()
		
		"""
		Load stuff
		"""
		
		# CPU load
		if data_timestamps['cpu_load'] < timestamp_before_rebuild - datetime.timedelta(seconds = 1):
			#print "cpu_load"
			cpu_load = psutil.cpu_percent(0.5) / 100
			plot_data['cpu_load'].append(cpu_load)
			
			if len(plot_data['cpu_load']) > CPU_PLOT_MAX_POINTS:
				del plot_data['cpu_load'][0]
			
			data_timestamps['cpu_load'] = timestamp_before_rebuild
		
		# RAM usage
		if data_timestamps['ram_usage'] < timestamp_before_rebuild - datetime.timedelta(seconds = 5):
			#print "ram_usage"
			ram_usage = psutil.virtual_memory().percent / 100
			data_timestamps['ram_usage'] = timestamp_before_rebuild
		
		# Disk usage
		if data_timestamps['disk_usage'] < timestamp_before_rebuild - datetime.timedelta(seconds = 10):
			#print "disk_usage"
			disk_usage = psutil.disk_usage("/").percent / 100
			data_timestamps['disk_usage'] = timestamp_before_rebuild
		
		# IP adress
		if data_timestamps['ip_adress'] < timestamp_before_rebuild - datetime.timedelta(seconds = 30):
			#print "ip_adress"
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				s.connect(("192.168.2.1", 80))
				ip = s.getsockname()[0]
				s.close()
			except:
				ip = "NO NETWORK"
			
			data_timestamps['ip_adress'] = timestamp_before_rebuild
		
		# CPU temperature
		if data_timestamps['cpu_temp'] < timestamp_before_rebuild - datetime.timedelta(seconds = 5):
			#print "cpu_temp"
			res = os.popen('vcgencmd measure_temp').readline()
			cpu_temp = float(res.replace("temp=", "").replace("'C\n", ""))
			plot_data['cpu_temp'].append(cpu_temp)
			
			if len(plot_data['cpu_temp']) > TEMP_PLOT_MAX_POINTS:
				del plot_data['cpu_temp'][0]
			
			data_timestamps['cpu_temp'] = timestamp_before_rebuild
		
		# Uptime
		if data_timestamps['uptime'] < timestamp_before_rebuild - datetime.timedelta(seconds = 60):
			#print "uptime"
			with open("/proc/uptime", 'r') as f:
				uptime_seconds = float(f.readline().split()[0])
			
			uptime_minutes, uptime_seconds = divmod(uptime_seconds, 60)
			uptime_hours, uptime_minutes = divmod(uptime_minutes, 60)
			uptime_days, uptime_hours = divmod(uptime_hours, 24)
			uptime_string = "UP %id %02i:%02i" % (uptime_days, uptime_hours, uptime_minutes)
			
			data_timestamps['uptime'] = timestamp_before_rebuild
		
		# Random word
		if data_timestamps['random_word'] < timestamp_before_rebuild - datetime.timedelta(seconds = 60 * 60 * 24):
			#print "random_word"
			with open("/usr/share/dict/words", 'r') as f:
				words = f.readlines()
				length = 99
				
				while length > 16:
					random_word = random.choice(words).upper()
					length = len(random_word)
			
			data_timestamps['random_word'] = timestamp_before_rebuild
		
		# Load average
		if data_timestamps['load_avg'] < timestamp_before_rebuild - datetime.timedelta(seconds = 1):
			#print "load_avg"
			with open("/proc/loadavg", 'r') as f:
				load_avg = float(f.read().split()[0])
			
			plot_data['load_avg'].append(load_avg)
			
			if len(plot_data['load_avg']) > LOAD_PLOT_MAX_POINTS:
				del plot_data['load_avg'][0]
			
			data_timestamps['load_avg'] = timestamp_before_rebuild
		
		# Data over SSH
		"""if data_timestamps['ssh_data'] < timestamp_before_rebuild - datetime.timedelta(seconds = 60):
			#print "ssh_data"
			if not ssh.login("192.168.2.111", "mezgrman"):
				print "\nSSH login failed!"
			else:
				ssh.sendline('ls -l')
				ssh.prompt()
				print ssh.before
				ssh.logout()
			
			data_timestamps['ssh_data'] = timestamp_before_rebuild"""
		
		"""
		Draw stuff
		"""
		
		# CPU bar
		draw.text("CPU", 0, 0, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		draw.progress_bar(12, 0, 127, 5, cpu_load)
		
		# RAM bar
		draw.text("RAM", 0, 7, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		draw.progress_bar(12, 7, 127, 12, ram_usage)
		
		# Disk bar
		draw.text("HDD", 0, 14, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		draw.progress_bar(12, 14, 127, 19, disk_usage)
		
		# Date and time
		draw.text(timestamp_before_rebuild.strftime("%d.%m.%y"), 'left', 'bottom', font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		draw.text(timestamp_before_rebuild.strftime("%H:%M"), 'right', 'bottom', font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		
		# IP adress
		draw.text(ip, ('center', 32, 107), 'bottom', font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		
		# Uptime
		draw.text(uptime_string, 0, 21, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		
		# Random word
		draw.text(random_word, 0, 27, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		
		# Vertical divider line
		#draw.line(64, 21, 64, 57)
		
		# Temperature plot
		draw.text("TEMP", 66, ('top', 21, 31), font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		draw.text("%.1f" % cpu_temp, 66, ('bottom', 21, 31), font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		draw.plot(82, 21, 127, 31, plot_data['cpu_temp'], range_x = (0, TEMP_PLOT_MAX_POINTS - 1))
		
		# CPU plot
		draw.text("CPU%", 0, ('top', 33, 44), font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		cpu_load_string = "%.1f" % (cpu_load * 100) if cpu_load < 1.0 else "%.0f" % (cpu_load * 100)
		draw.text(cpu_load_string, ('right', 0, 14), ('bottom', 33, 44), font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		draw.plot(16, 33, 127, 44, plot_data['cpu_load'], range_x = (0, CPU_PLOT_MAX_POINTS - 1), range_y = (0, 1))
		
		# Load plot
		draw.text("LOAD", 0, ('top', 46, 57), font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		draw.text("%.2f" % load_avg, 0, ('bottom', 46, 57), font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
		draw.plot(16, 46, 127, 57, plot_data['load_avg'], range_x = (0, LOAD_PLOT_MAX_POINTS - 1))
		
		if redraw:
			timestamp_before_commit = datetime.datetime.now()
			display.commit()
			timestamp_after_commit = datetime.datetime.now()
			rebuild_time_needed = (timestamp_before_commit - timestamp_before_rebuild).total_seconds()
			commit_time_needed = (timestamp_after_commit - timestamp_before_commit).total_seconds()
			total_time_needed = rebuild_time_needed + commit_time_needed
			sys.stdout.write("\rRebuilt in %.2fs, committed in %.2fs, total %.2fs" % (rebuild_time_needed, commit_time_needed, total_time_needed))
			sys.stdout.flush()
		
		#break
		#time.sleep(2)

if __name__ == "__main__":
	main()
