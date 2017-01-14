#!/usr/bin/python

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

with open( "/home/pi/home-assistant-pi/config.json" ) as json_file:
    j = json.load( json_file )
print j
last_update = time.time() - j['update_frequency']

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

	return str( timedelta( seconds = uptime_seconds ) ).split(".")[0]

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

def get_home_assistant_switch_state( entity_id ):
	ret = None
	try:
		response = requests.get( url + entity_id, headers = headers )
		if ( 200 == response.status_code ):
			value = response.json()['state']
			if ( value ):
				ret = response.json()
	except requests.exceptions.RequestException as e:
		print e

	return ret

def set_home_assistant_switch_off( entity_id, state ):
	new_state = {
		'state': 'off',
		'attributes': {
			'icon': '',
			'friendly_name': ''
		}
	}
	# Otherwise Home Assistant resets these values!
	if ( state['attributes']['icon'] ):
		new_state['attributes']['icon'] = state['attributes']['icon']
	if ( state['attributes']['friendly_name'] ):
		new_state['attributes']['friendly_name'] = state['attributes']['friendly_name']

	try:
		data = json.dumps(new_state)
		requests.post( url + entity_id, data, headers = headers )
	except requests.exceptions.RequestException as e:
		print e

# Home Assistant
url = j['ha_url'] + '/api/states/'
headers = {'x-ha-access': j['ha_password'],
			'content-type': 'application/json'}
client = mqtt.Client( "ha-client" )
mqtt_connect( j['ha_ip'] )

while True:
	now = time.time();
	if ( now > last_update + j['update_frequency'] ):
		last_update = now

		client.publish( j['ha_cpu_temp_topic'], get_cpu_temperature() )
		client.publish( j['ha_cpu_use_topic'], psutil.cpu_percent() )
		client.publish( j['ha_ram_use_topic'], psutil.virtual_memory().percent )
		client.publish( j['ha_uptime_topic'], get_uptime() )
		client.publish( j['ha_last_seen_topic'], str( datetime.datetime.fromtimestamp( int( now ) ).strftime('%Y-%m-%d %H:%M') ) )

		switch = get_home_assistant_switch_state( j['ha_reboot_entity_id'] )
		if ( None != switch and'on' ==  switch['state'] ):
			set_home_assistant_switch_off( j['ha_reboot_entity_id'], switch )
			reboot()
			break

		switch = get_home_assistant_switch_state( j['ha_shutdown_entity_id'] )
		if ( None != switch and 'on' == switch['state'] ):
			set_home_assistant_switch_off( j['ha_shutdown_entity_id'], switch )
			shutdown()
			break

	time.sleep( 1 )
