#!/usr/bin/python
"""Simple script to run on Raspberry Pis and report device information to a mqtt broaker.

Also provides switches so you can reboot or shutdown the Pi from within HA.
"""
import time
import os
import subprocess
import json
import socket

from datetime import datetime, timedelta

import psutil

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print('Please install paho-mqtt')
    raise


with open(os.path.join(os.path.dirname(__file__), "CONFIG.json")) as json_file:
    CONFIG = json.load(json_file)

LAST_UPDATE = 0


def convert_c_to_f(celsius):
    """Convert the specified temperature in Celsius to Fahrenheid."""
    return celsius * 1.8 + 32


def get_cpu_temperature(use_fahrenheid=True):
    """Retrieve the device temperature."""
    res = os.popen('vcgencmd measure_temp').readline()
    temperature = float(res.replace("temp=", "").replace("'C\n", ""))
    if use_fahrenheid:
        temperature = convert_c_to_f(temperature)
    return int(temperature)


def get_uptime():
    """Retrieve the uptime."""
    with open('/proc/uptime', 'r') as file:
        uptime_seconds = float(file.readline().split()[0])

    return str(timedelta(seconds=uptime_seconds)).split(".")[0]


def get_disk_used_percent():
    """Retrieve the disk usage."""
    return float(psutil.disk_usage('/'))


def get_ip():
    """Retrieve the IP-address."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((CONFIG['ip'], 1))
        addr = sock.getsockname()[0]
    except Exception:   # pylint: disable=W0703
        addr = '127.0.0.1'
    finally:
        sock.close()
    return addr


def on_connect(client, _userdata, _flags, result):
    """Called when the broker responds to our connection request.

    @param client    the client instance for this callback.
    @param _userdata the private user data as set in Client() or user_data_set().
    @param _flags    response flags sent by the broker.
    @param result    the connection result.
    """
    if result == 0:  # Connection successful
        client.connected_flag = True
        client.subscribe([(CONFIG['reboot_command_topic'], 1), (CONFIG['shutdown_command_topic'], 1)])


def on_message(client, _userdata, msg):
    """Called when a message has been received on a topic that the client subscribes to
    and the message does not match an existing topic filter callback.

    @param client    the client instance for this callback.
    @param userdata  the private user data as set in Client() or user_data_set().
    @param message   an instance of MQTTMessage. This is a class with members topic, payload, qos, retain.
    """
    # TODO: Use message_callback_add() to define a callback that will be called for specific topic filters.

    # http://www.ridgesolutions.ie/index.php/2013/02/22/raspberry-pi-restart-shutdown-your-pi-from-python-code/
    def shutdown(restart=None):
        """Shutdown or optionally reboot the device."""
        time.sleep(5)

        client.disconnect()
        client.loop_stop()

        option = 'h'
        if restart:
            option = 'r'

        command = "/usr/bin/sudo /sbin/shutdown -" + option + " now"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        process.communicate()

    message = msg.payload.decode("utf-8")
    if (message == 'ON') and (msg.retain != 1):
        if CONFIG['reboot_command_topic'] == msg.topic:
            client.publish(CONFIG['reboot_topic'], message)
            shutdown(True)
        elif CONFIG['shutdown_command_topic'] == msg.topic:
            client.publish(CONFIG['shutdown_topic'], message)
            shutdown()


def main():
    """Main script entry"""
    mqtt.Client.connected_flag = False
    mqtt.Client.bad_connection_flag = False
    mqtt.Client.retry_count = 0

    client = mqtt.Client()
    client.connected_flag = False
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_start()
    client.connect(CONFIG['ip'])
    while not client.connected_flag:
        time.sleep(1)

    try:
        while True:
            client.publish(CONFIG['last_seen_topic'], str(datetime.now().strftime('%Y-%m-%d %H:%M')))
            client.publish(CONFIG['uptime_topic'], get_uptime())
            client.publish(CONFIG['cpu_temp_topic'], get_cpu_temperature())
            client.publish(CONFIG['cpu_use_topic'], psutil.cpu_percent())
            client.publish(CONFIG['ram_use_topic'], psutil.virtual_memory().percent)
            client.publish(CONFIG['disk_use_topic'], get_disk_used_percent())
            client.publish(CONFIG['ipv4_address_topic'], get_ip())
            client.publish(CONFIG['reboot_topic'], 'OFF')
            client.publish(CONFIG['shutdown_topic'], 'OFF')

            time.sleep(CONFIG['loop_sleep'])
    except KeyboardInterrupt:
        client.disconnect()
        client.loop_stop()


if __name__ == '__main__':
    main()
