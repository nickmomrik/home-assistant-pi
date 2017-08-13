#!/usr/bin/python

import time
import os
import psutil
import subprocess
import requests
import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from datetime import datetime, timedelta

with open( "/home/pi/home-assistant-pi/config.json" ) as json_file:
    config = json.load( json_file )

last_update = 0

# Home Assistant
url = config['ha_url'] + '/api/states/'
headers = {'x-ha-access': config['ha_password'],
	'content-type': 'application/json'}
mqtt.Client.connected_flag = False
mqtt.Client.bad_connection_flag = False
mqtt.Client.retry_count = 0

def convert_c_to_f( celcius ):
	return celcius * 1.8 + 32

def get_cpu_temperature():
	res = os.popen( 'vcgencmd measure_temp' ).readline()

	return int( convert_c_to_f( float( res.replace( "temp=", "" ).replace( "'C\n", "" ) ) ) )

def get_uptime():
	with open( '/proc/uptime', 'r' ) as f:
		uptime_seconds = float( f.readline().split()[0] )

	return str( timedelta( seconds = uptime_seconds ) ).split(".")[0]

def get_disk_used_percent():
	disk = psutil.disk_usage('/')

	return float( disk.percent )

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
		data = json.dumps( new_state )
		requests.post( url + entity_id, data, headers = headers )
	except requests.exceptions.RequestException as e:
		print e

def on_disconnect( client, userdata, flags, rc = 0 ):
	client.connected_flag = False

def on_connect( client, userdata, flags, rc ):
	if ( 0 == rc ):
		client.connected_flag = True
	else:
		client.bad_connection_flag = True

def update_home_assistant_sensors():
	#http://www.steves-internet-guide.com/client-connections-python-mqtt/

	global last_update

	client = mqtt.Client()
	client.on_connect = on_connect
	client.on_disconnect = on_disconnect

	run_main = False
	run_flag = True
	while ( run_flag ):
		while ( not client.connected_flag and client.retry_count < 3 ):
			count = 0
			run_main = False
			try:
				client.connect( config['ha_ip'] )
				break
			except:
				client.retry_count += 1
				if ( client.retry_count > 5 ):
					run_flag = False

			time.sleep( 3 )

		if ( run_main ):
			run_flag = False

			client.publish( config['ha_last_seen_topic'], str( datetime.now().strftime('%Y-%m-%d %H:%M') ) )
			client.publish( config['ha_uptime_topic'], get_uptime() )
			client.publish( config['ha_cpu_temp_topic'], get_cpu_temperature() )
			client.publish( config['ha_cpu_use_topic'], psutil.cpu_percent() )
			client.publish( config['ha_ram_use_topic'], psutil.virtual_memory().percent )
			client.publish( config['ha_disk_use_topic'], get_disk_used_percent() )

			switch = get_home_assistant_switch_state( config['ha_reboot_entity_id'] )
			if ( switch is not None and 'on' == switch['state'] ):
				set_home_assistant_switch_off( config['ha_reboot_entity_id'], switch )
				reboot()
				break

			switch = get_home_assistant_switch_state( config['ha_shutdown_entity_id'] )
			if ( switch is not None and 'on' == switch['state'] ):
				set_home_assistant_switch_off( config['ha_shutdown_entity_id'], switch )
				shutdown()
				break

			last_update = time.time()
		else:
			client.loop_start()
	        while ( True ):
				if ( client.connected_flag ):
					client.retry_count = 0
					run_main = True
					break
				elif ( count > 6 or client.bad_connection_flag ):
					client.loop_stop()
					client.retry_count += 1
					if ( client.retry_count > 5 ):
						run_flag = False
						break
				else:
					time.sleep( 3 )
					count += 1

	client.disconnect()
	client.loop_stop()

while ( True ):
	if ( time.time() > ( last_update + config['update_frequency'] ) ):
		update_home_assistant_sensors()

	time.sleep( 1 )
