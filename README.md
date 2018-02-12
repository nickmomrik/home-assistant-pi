# home-assistant-pi
Simple service to run on Raspberry Pis and report data back to Home Assistant. Also provides switches so you can reboot or shutdown the Pi from within HA.

![Home Assistant Pi](./group-home-assistant.png?raw=true "Home Assistant Pi")

## Installation

* Install [psutil](https://pypi.python.org/pypi/psutil)
* Install [paho-mqtt](https://pypi.python.org/pypi/paho-mqtt)
* Clone this repo to `/home/pi`
* `cd home-assistant-pi`
* `cp config-sample.json config.json`
* Edit `config.json` to set all of the options. Change `HOSTNAME` to whatever you want to use as a name and make sure your HA config also matches.
* Configure Home Assistant. Here's an example of some `configuration.yaml` settings:
```
homeassistant:
  # You should have a bunch of other
  # settings here in your config

  customize_glob::
	"sensor.*cpu_temperature":
	  icon: mdi:thermometer
	  friendly_name: CPU Temp
	"sensor.*cpu_use*":
	  icon: mdi:raspberrypi
	  friendly_name: CPU
	"sensor.*ram_use*":
	  icon: mdi:chip
	  friendly_name: RAM
	"sensor.*disk_use*":
	  icon: mdi:harddisk
	  friendly_name: Disk
	"sensor.*_uptime":
	  icon: mdi:timer
	  friendly_name: Uptime
	"sensor.*_last_seen":
	  icon: mdi:calendar-clock
	  friendly_name: Last Seen
	"switch.*_reboot":
	  icon: mdi:refresh
	  friendly_name: Reboot
	  assumed_state: false
	"switch.*_shutdown":
	  icon: mdi:close-network
	  friendly_name: Shutdown
	  assumed_state: false
	"sensor.*ipv4_address":
  	  icon: mdi:server-network
  	  friendly_name: IP

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
    state_topic: 'pis/HOSTNAME/disk-use'
    name: 'HOSTNAME DISK Use'
    unit_of_measurement: '%'
  - platform: mqtt
    state_topic: 'pis/HOSTNAME/uptime'
    name: 'HOSTNAME Uptime'
  - platform: mqtt
    state_topic: 'pis/HOSTNAME/last-seen'
    name: 'HOSTNAME Last Seen'
  - platform: mqtt
    state_topic: 'pis/HOSTNAME/ipv4-address'
    name: 'HOSTNAME IPv4 Address'

binary_sensor:
  - platform: template
    sensors:
	  pi_HOSTNAME_on:
	    value_template: >-
		  {%- if states( 'sensor.apple_last_seen' ) != 'unknown'
		    and ( as_timestamp( now() ) - as_timestamp( states( 'sensor.apple_last_seen' ) ) ) <= 240 -%}
		  True
		  {%- else -%}
		  False
		  {%- endif %}

switch:
  platform: command_line
  switches:
  HOSTNAME_reboot:
	command_on: "echo 'Reboot HOSTNAME'"
  HOSTNAME_shutdown:
	command_on: "echo 'Shutdown HOSTNAME'"

group:
  pi_HOSTNAME_on:
    name: HOSTNAME
    control: hidden
    entities:
	  - sensor.HOSTNAME_ipv4_address
	  - sensor.HOSTNAME_uptime
	  - switch.HOSTNAME_reboot
	  - switch.HOSTNAME_shutdown
	  - sensor.HOSTNAME_cpu_temperature
	  - sensor.HOSTNAME_cpu_use
	  - sensor.HOSTNAME_ram_use
	  - sensor.HOSTNAME_disk_use
  pi_HOSTNAME_off:
    name: HOSTNAME
    entities:
	  - sensor.HOSTNAME_last_seen

automation:
- alias: 'Home Assistant Start'
  trigger:
    platform: homeassistant
    event: start
  action:
    - service: group.set_visibility
      entity_id:
        - group.pi_HOSTNAME_on
      data:
        visible: False

- alias: 'pi is on'
  trigger:
    platform: state
    entity_id:
      - binary_sensor.pi_HOSTNAME_on
    from: 'off'
    to: 'on'
  action:
    - service: group.set_visibility
      data_template:
        entity_id: "group.pi_{{ trigger.entity_id | replace( 'binary_sensor.pi_', '' ) }}"
        visible: True
    - service: group.set_visibility
      data_template:
        entity_id: "group.pi_{{ trigger.entity_id | replace( 'binary_sensor.pi_', '' ) | replace( '_on', '' ) }}_off"
        visible: False

- alias: 'pi not seen'
  trigger:
    platform: state
    entity_id:
      - binary_sensor.pi_HOSTNAME_on
    from: 'on'
    to: 'off'
  action:
    - service: group.set_visibility
      data_template:
        entity_id: "group.pi_{{ trigger.entity_id | replace( 'binary_sensor.pi_', '' ) | replace( '_on', '' ) }}_on"
        visible: False
    - service: group.set_visibility
      data_template:
        entity_id: "group.pi_{{ trigger.entity_id | replace( 'binary_sensor.pi_', '' ) | replace( '_on', '' ) }}_off"
        visible: True
    - service: notify.ios_PHONENAME
      data_template:
        title: "Pi Offline"
        message: "{{ trigger.entity_id | replace( 'binary_sensor.pi_', '' ) | replace( '_on', '' ) }}"

- alias: 'pi disk use'
  trigger:
    platform: numeric_state
    entity_id:
      - sensor.HOSTNAME_disk_use
    above: 90
  action:
    - service: notify.ios_PHONENAME
      data_template:
        title: "Pi Disk Use > 90%"
        message: "{{ trigger.entity_id | replace( 'sensor.', '' ) | replace( '_disk_use', '' ) }}"

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
Check status

`sudo systemctl status home-assistant-pi.service`

Start service

`sudo systemctl start home-assistant-pi.service`

Stop service

`sudo systemctl stop home-assistant-pi.service`

Check service's log

`sudo journalctl -f -u home-assistant-pi.service`
