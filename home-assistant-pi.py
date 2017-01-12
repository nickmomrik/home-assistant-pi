#!/usr/bin/python

########
# CONFIG

# How often to update Home Assistant (in seconds)
frequency = 60

# Home Assistant
import socket
ha_ip                 = '192.168.2.149'
topic_prefix          = 'pis/' + socket.gethostname() + '/'
ha_cpu_temp_topic     = topic_prefix + 'cpu-temp'
ha_cpu_use_topic      = topic_prefix + 'cpu-use'
ha_ram_use_topic      = topic_prefix + 'ram-use'
ha_uptime_topic       = topic_prefix + 'uptime'
ha_last_seen_topic    = topic_prefix + 'last-seen'
switch_prefix         = 'switch.' + socket.gethostname().replace( '-', '_' )
ha_reboot_entity_id   = switch_prefix + '_reboot'
ha_shutdown_entity_id = switch_prefix + '_shutdown'

# END CONFIG
############

import time
import os
import psutil
import subprocess
import requests
import json
import datetime
from datetime import timedelta
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

last_update = time.time() - frequency

def mqtt_connect( ip ):
	connected = False
	i = 0

	while not connected:
		try:
			client.connect( ip )
			client.loop_start()
			connected = True
		except Exception as e:
			if ( i < 10 ):
				i = i + 1
				time.sleep( 3 )
			else:
				raise

def convert_c_to_f( celcius ):
	return celcius * 1.8 + 32

def get_cpu_temperature():
	res = os.popen( 'vcgencmd measure_temp' ).readline()

	return int( convert_c_to_f( float( res.replace( "temp=", "" ).replace( "'C\n", "" ) ) ) )

def get_uptime():
	with open( '/proc/uptime', 'r' ) as f:
		uptime_seconds = float( f.readline().split()[0] )

	return str( timedelta( seconds = uptime_seconds ) )

# http://www.ridgesolutions.ie/index.php/2013/02/22/raspberry-pi-restart-shutdown-your-pi-from-python-code/
def shutdown( restart = None ):
	type = 'h'
	if ( restart ):
		type = 'r'

	command = "/usr/bin/sudo /sbin/shutdown -" + type + " now"
	process = subprocess.Popen( command.split(), stdout = subprocess.PIPE )
	output = process.communicate()[0]
	print output

def reboot():
	shutdown( True )

def get_home_assistant_switch_state( entity_id, default_value ):
	ret = default_value
	try:
		response = requests.get( url + entity_id, headers = headers )
		if ( 200 == response.status_code ):
			value = response.json()['state']
			if ( value ):
				ret = value
	except requests.exceptions.RequestException as e:
		print e

	return ret

def set_home_assistant_switch_off( entity_id ):
	try:
		data = json.dumps({'state': 'off'})
		requests.post( url + entity_id, data, headers = headers )
	except requests.exceptions.RequestException as e:
		print e

# Home Assistant
url = 'http://' + ha_ip + ':8123/api/states/'
with open( '/home/pi/home-assistant-pi/ha-password.txt', 'r' ) as f:
	password = f.readline().strip()
headers = {'x-ha-access': password,
			'content-type': 'application/json'}
client = mqtt.Client( "ha-client" )
mqtt_connect( ha_ip )

while True:
	now = time.time();
	if ( now > last_update + frequency ):
		last_update = now

		client.publish( ha_cpu_temp_topic, get_cpu_temperature() )
		client.publish( ha_cpu_use_topic, psutil.cpu_percent() )
		client.publish( ha_ram_use_topic, psutil.virtual_memory().percent )
		client.publish( ha_uptime_topic, get_uptime() )
		client.publish( ha_last_seen_topic, now )

	if ( 'on' == get_home_assistant_switch_state( ha_reboot_entity_id, 'off' ) ):
		set_home_assistant_switch_off( ha_reboot_entity_id )
		reboot()
	elif ( 'on' == get_home_assistant_switch_state( ha_shutdown_entity_id, 'off' ) ):
		set_home_assistant_switch_off( ha_shutdown_entity_id )
		shutdown()

	time.sleep( 1 )
