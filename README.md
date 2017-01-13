# home-assistant-pi
Simple service to run on Raspberry Pis and report data back to Home Assistant. Also provides switches so you can reboot or shutdown the Pi from within HA.

## Installation

* Install [psutil](https://pypi.python.org/pypi/psutil)
* Install [paho-mqtt](https://pypi.python.org/pypi/paho-mqtt)
* Clone this repo to `/home/pi`
* Create a file named `ha-password.txt` in the `home-assistant-temperature-monitor` directory
* Configure the settings at the top of the `home-assistant-pi.py` file. If you change any of the topic or entity values, you'll need to adjust your Home Assistant config example below to reflect those differences.
* Configure Home Assistant. Replace every instance of `HOSTNAME` below with the hostname set on your Pi. Here's an example of some `configuration.yaml` settings:
```
homeassistant:
  # You should have a bunch of other
  # settings here in your config
  customize:
    sensor.HOSTNAME_cpu_temperature:
      icon: mdi:thermometer
      friendly_name: CPU Temp
    sensor.HOSTNAME_cpu_use:
      icon: mdi:raspberrypi
      friendly_name: CPU Use
    sensor.HOSTNAME_ram_use:
      icon: mdi:raspberrypi
      friendly_name: RAM Use
    sensor.HOSTNAME_uptime:
      icon: mdi:clock
      friendly_name: Uptime
    sensor.HOSTNAME_last_seen:
      icon: mdi:clock
      friendly_name: Last Seen
	switch.HOSTNAME_reboot:
	  icon: mdi:refresh
	  friendly_name: Reboot
	switch.HOSTNAME_shutdown:
	  icon: mdi:close-network
	  friendly_name: Shutdown

sensor:
  - platform: mqtt
    state_topic: 'pis/HOSTNAME/cpu-temp'
    name: 'HOSTNAME CPU Temperature'
    unit_of_measurement: '°F'
  - platform: mqtt
    state_topic: 'pis/HOSTNAME/cpu-use'
    name: 'HOSTNAME CPU Use'
    unit_of_measurement: '%'
  - platform: mqtt
    state_topic: 'pis/HOSTNAME/ram-use'
    name: 'HOSTNAME RAM Use'
    unit_of_measurement: '%'
  - platform: mqtt
    state_topic: 'pis/HOSTNAME/uptime'
    name: 'HOSTNAME Uptime'
  - platform: mqtt
    state_topic: 'pis/HOSTNAME/last-seen'
    name: 'HOSTNAME Last Seen'

switch:
  platform: command_line
  switches:
  HOSTNAME_reboot:
	command_on: "echo 'Reboot HOSTNAME'"
  HOSTNAME_shutdown:
	command_on: "echo 'Shutdown HOSTNAME'"

group:
  pi_HOSTNAME:
    name: HOSTNAME
    control: hidden
    entities:
	  - sensor.HOSTNAME_uptime
	  - sensor.HOSTNAME_last_seen
	  - switch.HOSTNAME_reboot
	  - switch.HOSTNAME_shutdown
	  - sensor.HOSTNAME_cpu_temperature
	  - sensor.HOSTNAME_cpu_use
	  - sensor.HOSTNAME_ram_use
```
* You probably want to [run this program as a service ](http://www.diegoacuna.me/how-to-run-a-script-as-a-service-in-raspberry-pi-raspbian-jessie/), so I've provided some help here.
```
sudo cp home-assistant-pi.service /lib/systemd/system/

sudo chmod 644 /lib/systemd/system/home-assistant-pi.service

chmod +x /home/pi/home-assistant-pi/home-assistant-pi.py

sudo systemctl daemon-reload

sudo systemctl enable home-assistant-pi.service

sudo systemctl start home-assistant-pi.service
```

### Interact with the service
```
# Check status
sudo systemctl status home-assistant-pi.service

# Start service
sudo systemctl start home-assistant-pi.service

# Stop service
sudo systemctl stop home-assistant-pi.service

# Check service's log
sudo journalctl -f -u home-assistant-pi.service
```
