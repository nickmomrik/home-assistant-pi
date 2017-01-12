#!/usr/bin/python

########
# CONFIG

# How often to update Home Assistant (in seconds)
frequency = 60

# Home Assistant
ha_ip                  = '192.168.2.149'
import socket
topic_prefix           = 'pis/' + socket.gethostname() + '/'
ha_cpu_temp_topic      = topic_prefix + 'cpu-temp'
ha_cpu_use_topic       = topic_prefix + 'cpu-use'
ha_ram_use_topic       = topic_prefix + 'ram-use'
ha_uptime_topic        = topic_prefix + 'uptime'

# END CONFIG
############

import time
import os
import psutil
from datetime import timedelta
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

last_update  = time.time() - frequency

# Home Assistant
url = 'http://' + ha_ip + ':8123/api/states/'
with open( '/home/pi/home-assistant-pi/ha-password.txt', 'r' ) as f:
	password = f.readline().strip()
headers = {'x-ha-access': password,
			'content-type': 'application/json'}
client = mqtt.Client( "ha-client" )
client.connect( ha_ip )
client.loop_start()

def convert_c_to_f( celcius ):
	return celcius * 1.8 + 32

def get_cpu_temperature():
	res = os.popen( 'vcgencmd measure_temp' ).readline()

	return int( convert_c_to_f( float( res.replace( "temp=", "" ).replace( "'C\n", "" ) ) ) )

def get_uptime():
	with open( '/proc/uptime', 'r' ) as f:
		uptime_seconds = float( f.readline().split()[0] )

		return str( timedelta( seconds = uptime_seconds ) )


while True:
	now = time.time();
	if ( now > last_update + frequency ):
		last_update = now

		client.publish( ha_cpu_temp_topic, get_cpu_temperature() )
		client.publish( ha_cpu_use_topic, psutil.cpu_percent() )
		client.publish( ha_ram_use_topic, psutil.virtual_memory().percent )
		client.publish( ha_uptime_topic, get_uptime() )

	time.sleep( 1 )
