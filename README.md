# home-assistant-pi
Simple service to run on Raspberry Pis and report data back to Home Assistant

### Run as a service
* `cp home-assistant-pi.service /lib/systemd/system/`
* `sudo chmod 644 /lib/systemd/system/home-assistant-pi.service`
* `chmod +x /home/pi/home-assistant-pi/home-assistant-pi.py`
* `sudo systemctl daemon-reload`
* `sudo systemctl enable hello.service`
* `sudo systemctl start hello.service`
