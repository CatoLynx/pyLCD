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
import pylcd
import socket
import sys
import thread
import time
import traceback

class SystemMonitor(object):
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
	
	PLOT_MAX_POINTS = 46
	CPU_LOAD = []
	RAM_USAGE = []
	DISK_USAGE = 0
	CPU_TEMP = []
	LOAD_AVG = []
	IP_ADRESS = ""
	UPTIME_STRING = ""

	def get_data(self, single = False):
		while True:
			# CPU load
			cpu_load = psutil.cpu_percent(1.0) / 100
			self.CPU_LOAD.append(cpu_load)
			
			if len(self.CPU_LOAD) > self.PLOT_MAX_POINTS:
				del self.CPU_LOAD[0]
			
			# RAM usage
			ram_usage = psutil.virtual_memory().percent / 100
			self.RAM_USAGE.append(ram_usage)
			
			if len(self.RAM_USAGE) > self.PLOT_MAX_POINTS:
				del self.RAM_USAGE[0]
			
			# Disk usage
			self.DISK_USAGE = psutil.disk_usage("/").percent / 100
			
			# IP Adress
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				s.connect(("192.168.2.1", 80))
				self.IP_ADRESS = s.getsockname()[0]
				s.close()
			except:
				self.IP_ADRESS = "NO NETWORK"
			
			# CPU temperature
			res = os.popen('vcgencmd measure_temp').readline()
			cpu_temp = float(res.replace("temp=", "").replace("'C\n", ""))
			self.CPU_TEMP.append(cpu_temp)
			
			if len(self.CPU_TEMP) > self.PLOT_MAX_POINTS:
				del self.CPU_TEMP[0]
			
			# Uptime
			with open("/proc/uptime", 'r') as f:
				uptime_seconds = float(f.readline().split()[0])
			
			uptime_minutes, uptime_seconds = divmod(uptime_seconds, 60)
			uptime_hours, uptime_minutes = divmod(uptime_minutes, 60)
			uptime_days, uptime_hours = divmod(uptime_hours, 24)
			self.UPTIME_STRING = "UP %id %02i:%02i" % (uptime_days, uptime_hours, uptime_minutes)
			
			# Load average
			with open("/proc/loadavg", 'r') as f:
				load_avg = float(f.read().split()[0])
			
			self.LOAD_AVG.append(load_avg)
			
			if len(self.LOAD_AVG) > self.PLOT_MAX_POINTS:
				del self.LOAD_AVG[0]
			
			if single:
				break
			
			time.sleep(1)

	def run(self):
		thread.start_new_thread(self.get_data, (True, ))
		try:
			brightness = int(sys.argv[1])
		except:
			brightness = 1023
		
		display = pylcd.ks0108.Display(backend = pylcd.GPIOBackend, pinmap = self.PINMAP, debug = False)
		draw = pylcd.ks0108.DisplayDraw(display)
		display.commit(full = True)
		
		display.set_brightness(brightness)
		
		thread.start_new_thread(self.get_data, ())
		
		while True:
			try:
				redraw = True
				timestamp_before_rebuild = datetime.datetime.now()
				display.clear()
				
				# Draw a CPU bar
				draw.text("CPU", 0, 0, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				draw.progress_bar(12, 0, 127, 5, self.CPU_LOAD[-1])
				
				# Draw a RAM bar
				draw.text("RAM", 0, 7, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				draw.progress_bar(12, 7, 127, 12, self.RAM_USAGE[-1])
				
				# Draw a storage bar
				draw.text("HDD", 0, 14, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				draw.progress_bar(12, 14, 127, 19, self.DISK_USAGE)
				
				# Draw date and time
				draw.text(timestamp_before_rebuild.strftime("%d.%m.%y"), 'left', 'bottom', font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				draw.text(timestamp_before_rebuild.strftime("%H:%M"), 'right', 'bottom', font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				
				# Draw the IP adress
				draw.text(self.IP_ADRESS, ('center', 32, 107), 'bottom', font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				
				# Draw CPU temperature
				draw.text("CPU TEMP %.1f°C" % self.CPU_TEMP[-1], 0, 21, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				
				# Draw uptime
				draw.text(self.UPTIME_STRING, 0, 28, font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				
				# Draw divider line
				draw.line(64, 21, 64, 57)
				
				# Draw plots
				draw.text("CPU%", 66, ('middle', 21, 31), font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				draw.plot(82, 21, 127, 31, self.CPU_LOAD, range_x = (0, self.PLOT_MAX_POINTS - 1), range_y = (0, 1))
				
				draw.text("LOAD", 66, ('middle', 33, 44), font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				draw.plot(82, 33, 127, 44, self.LOAD_AVG, range_x = (0, self.PLOT_MAX_POINTS - 1))
				
				draw.text("TEMP", 66, ('middle', 46, 57), font = "/home/pi/projects/pyLCD/fonts/3x5.fnt")
				draw.plot(82, 46, 127, 57, self.CPU_TEMP, range_x = (0, self.PLOT_MAX_POINTS - 1))
				
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
				time.sleep(1)
			except KeyboardInterrupt:
				raise
			except:
				traceback.print_exc()

def main():
	mon = SystemMonitor()
	mon.run()

if __name__ == "__main__":
	main()
