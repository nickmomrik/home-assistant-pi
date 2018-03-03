#!/usr/bin/python

import time
import os
import psutil
import subprocess
import json
import socket
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from datetime import datetime, timedelta

with open( "/home/pi/home-assistant-pi/config.json" ) as json_file :
    config = json.load( json_file )

last_update = 0

# Home Assistant
mqtt.Client.connected_flag = False
mqtt.Client.bad_connection_flag = False
mqtt.Client.retry_count = 0

def convert_c_to_f( celcius ) :
	return celcius * 1.8 + 32

def get_cpu_temperature() :
	res = os.popen( 'vcgencmd measure_temp' ).readline()

	return int( convert_c_to_f( float( res.replace( "temp=", "" ).replace( "'C\n", "" ) ) ) )

def get_uptime() :
	with open( '/proc/uptime', 'r' ) as f :
		uptime_seconds = float( f.readline().split()[0] )

	return str( timedelta( seconds = uptime_seconds ) ).split(".")[0]

def get_disk_used_percent() :
	disk = psutil.disk_usage('/')

	return float( disk.percent )

def get_ip() :
    s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    try:
        s.connect( ( 'google.com', 1 ) )
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# http://www.ridgesolutions.ie/index.php/2013/02/22/raspberry-pi-restart-shutdown-your-pi-from-python-code/
def shutdown( restart = None ) :
	time.sleep( 5 )

	client.disconnect()
	client.loop_stop()

	type = 'h'
	if ( restart ):
		type = 'r'

	command = "/usr/bin/sudo /sbin/shutdown -" + type + " now"
	process = subprocess.Popen( command.split(), stdout = subprocess.PIPE )
	output = process.communicate()[0]

def reboot() :
	shutdown( True )

def on_connect( client, userdata, flags, rc ) :
	if ( 0 == rc ) :
		client.connected_flag = True
		client.subscribe( [( config['reboot_command_topic'], 1 ), ( config['shutdown_command_topic'], 1 )] )

def on_message( client, userdata, msg ) :
	message = msg.payload.decode( "utf-8" )
	if ( 'ON' == message and 1 != msg.retain ) :
		if ( config['reboot_command_topic'] == msg.topic ) :
			client.publish( config['reboot_topic'], message )
			reboot()
		elif ( config['shutdown_command_topic'] == msg.topic ) :
			client.publish( config['shutdown_topic'], message )
			shutdown()

client = mqtt.Client()
client.connected_flag = False
client.on_connect = on_connect
client.on_message = on_message
client.loop_start()
client.connect( config['ip'] )
while ( not client.connected_flag ) :
	time.sleep( 1 )

try :
	while ( True ) :
		client.publish( config['last_seen_topic'], str( datetime.now().strftime( '%Y-%m-%d %H:%M' ) ) )
		client.publish( config['uptime_topic'], get_uptime() )
		client.publish( config['cpu_temp_topic'], get_cpu_temperature() )
		client.publish( config['cpu_use_topic'], psutil.cpu_percent() )
		client.publish( config['ram_use_topic'], psutil.virtual_memory().percent )
		client.publish( config['disk_use_topic'], get_disk_used_percent() )
		client.publish( config['ipv4_address_topic'], get_ip() )
		client.publish( config['reboot_topic'], 'OFF' )
		client.publish( config['shutdown_topic'], 'OFF' )

		time.sleep( config['loop_sleep'] )
except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()
