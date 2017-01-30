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
  customize:
    - entity_id: sensor.HOSTNAME_cpu_temperature
      icon: mdi:thermometer
      friendly_name: CPU Temp
    - entity_id: sensor.HOSTNAME_cpu_use
      icon: mdi:raspberrypi
      friendly_name: CPU Use
    - entity_id: sensor.HOSTNAME_ram_use
      icon: mdi:raspberrypi
      friendly_name: chip
    - entity_id: sensor.HOSTNAME_uptime
      icon: mdi:timer
      friendly_name: Uptime
    - entity_id: sensor.HOSTNAME_last_seen
      icon: mdi:calendar-clock
      friendly_name: Last Seen
	- entity_id: switch.HOSTNAME_reboot
	  icon: mdi:refresh
	  friendly_name: Reboot
	  assumed_state: false
	- entity_id: switch.HOSTNAME_shutdown
	  icon: mdi:close-network
	  friendly_name: Shutdown
	  assumed_state: false

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
  pi_HOSTNAME_on:
    name: HOSTNAME
    control: hidden
    entities:
	  - sensor.HOSTNAME_uptime
	  - switch.HOSTNAME_reboot
	  - switch.HOSTNAME_shutdown
	  - sensor.HOSTNAME_cpu_temperature
	  - sensor.HOSTNAME_cpu_use
	  - sensor.HOSTNAME_ram_use
  pi_HOSTNAME_off:
    name: HOSTNAME
    entities:
	  - sensor.HOSTNAME_last_seen

automation:
  - alias: 'Home Assistant Start'
    trigger:
      platform: event
      event_type: homeassistant_start
    action:
      - service: group.set_visibility
        entity_id: group.pi_HOSTNAME_on
        data:
          visible: False

  - alias: 'HOSTNAME is on'
    trigger:
      platform: mqtt
      topic: 'pis/HOSTNAME/last-seen'
    condition:
      - condition: template
        value_template: '{{ states.group.pi_HOSTNAME_on.attributes.hidden }}'
    action:
      - service: group.set_visibility
        entity_id: group.pi_HOSTNAME_on
        data:
          visible: True
      - service: group.set_visibility
        entity_id: group.pi_HOSTNAME_off
        data:
          visible: False

  - alias: 'HOSTNAME not seen'
    trigger:
      platform: time
      minutes: '/2'
      seconds: 00
    condition:
      condition: and
      conditions:
        - condition: template
          value_template: '{{ states.group.pi_HOSTNAME_off.attributes.hidden }}'
        - condition: or
          conditions:
          - condition: template
            value_template: '{{ "unknown" == states.sensor.HOSTNAME_last_seen.state }}'
          - condition: template
            value_template: '{{ ( as_timestamp( now() ) - as_timestamp( states.sensor.HOSTNAME_last_seen.state ) ) > 120 }}'
    action:
      - service: group.set_visibility
        entity_id: group.pi_HOSTNAME_on
        data:
          visible: False
      - service: group.set_visibility
        entity_id: group.pi_HOSTNAME_off
        data:
          visible: True
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
