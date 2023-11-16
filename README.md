# GrblWebStreamer
A simple python headless and web interface UI to stream GRBL to a Laser engraver, that can push you notifications to Naver Line.

Why? Because I don't want my laptop stuck to the laser all the time it burns. And because LightBurn is great but crashes EVERY TIME my Ubuntu locks screen (that hopefully will be fixed by them one day but until then). And because I find it fun to do (maybe mostly, ok).

![Job processing](https://github.com/AlanFromJapan/GrblWebStreamer/blob/main/sample.gcode/Screenshot01.png?raw=true)
                  
## Inspirations
If you want to do MORE than just stream a GRBL file on a raspi (nearly headless), there's many more complex options: 
 - Streamer script from GRBL https://github.com/gnea/grbl/blob/master/doc/script/stream.py
 - CNCJS https://github.com/cncjs/cncjs
 - Grbl-Stream https://github.com/fragmuffin/grbl-stream
 - bCNC https://pypi.org/project/bCNC/


## Helpful
 - Online GRBL simulator for playing https://nraynaud.github.io/webgcode/
 - GRBL commands list https://www.sainsmart.com/blogs/news/grbl-v1-1-quick-reference

# Technical
Runs on python3, dependencies:
 - Flask (installed as OS package on Raspberry Pi)
 - pySerial (installed as OS package on Raspberry Pi)
 - [grbl2image](https://github.com/AlanFromJapan/grbl2image)
 - line-bot-sdk
 
# Setup
## Basics
Run the **install-script.sh** but this is what it should do👇

Notes:
- Raspbian bookworm (late 2023) doesn't like pip packages installed globally, so you have to either use the .deb with your precompiled lib (recommended) or make a venv and get that lib
- Because of the above, flask if installed via venv comes with dependency on Rust and Cargo to be built and installed (space and time wasted)... just pick the .deb instead

```bash
sudo apt install git python3 python3-pip python3-venv libopenjp2-7 --yes
#getting python libs as prebuilt debian packages
sudo apt install python3-flask python3-serial --yes

mkdir GrblWebStreamer.venv
cd GrblWebStreamer.venv
git clone https://github.com/AlanFromJapan/GrblWebStreamer.git
#don't forget the --system-site-packages to get access to globally installed packages (flask & pySerial)
python3 -m venv --system-site-packages .
source bin/activate
#get via pip only the non-prebuilt packages
python -m pip install -r ./GrblWebStreamer/requirements.txt

sudo mkdir -p /var/local/GrblWebStreamer/logs
sudo mkdir -p /var/local/GrblWebStreamer/uploads
sudo chgrp -R pi /var/local/GrblWebStreamer
sudo chmod -R g+rw /var/local/GrblWebStreamer

```

We'll have it run with a power user account because this is **NOT MEANT** to be accessible from the net. If you do it, *make another account that is not sudoer* and use that one instead (make it part of *dialout* group to access serial). My power user will be "pi".

## Configuration
 - Copy config.sample.py to config.py and customize at will
 - Make it start at start-up: edit */etc/rc.local* and add `/path/to/installation/GrblWebStreamer/start-service.sh`
 - Add port mapping rules to access from port 80 (see the install script)
 - Reboot and test

## How to setup the Naver Line notifier
Add in your config.py in the "notifiers" list member a member :
```python
    LineBotNotifier(
        #Generate the token in your Line developer channel (RTFM it's super straight forward)
        channelAccessToken="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 
        #Your Unique user ID so the bot talks to you
        targetID="U123456abcd..."
    )
```
That you will find in your Line developer channel (see https://pypi.org/project/line-bot-sdk/).

# G-code things to remember
This helped me so in case:
 - Fxxxx sets the move speed in unit per minute (xxx=1800 == 30mm/sec)
 - Sxxx sets the laser power in per thousands (xxx=600 == 60.0%)
 - G0 is move but don't burn, G1 is move n burn
 - G90 means positions ABSOLUTE, G91 means positions are RELATIVE
