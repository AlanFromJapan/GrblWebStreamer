# GrblWebStreamer
A simple python headless and web interface UI to stream GRBL to a CNC/Laser.

Why? Because I don't want my laptop stuck to the laser all the time it burns. And because LightBurn is great but crashes EVERY TIME my Ubuntu locks screen (that hopefully will be fixed by them one day but until then). And because I find it fun to do (maybe mostly, ok).

## Inspirations
If you want to do MORE than just stream a GRBL file on a raspi (nearly headless), there's many more complex options: 
 - Streamer script from GRBL https://github.com/gnea/grbl/blob/master/doc/script/stream.py
 - CNCJS https://github.com/cncjs/cncjs
 - Grbl-Stream https://github.com/fragmuffin/grbl-stream
 - bCNC https://pypi.org/project/bCNC/


## Helpful
 - Online GRBL simulator for playing https://nraynaud.github.io/webgcode/
 - GRBL commands list https://www.sainsmart.com/blogs/news/grbl-v1-1-quick-reference

## Technical
Runs on python3, dependecies:
 - Flask
 - pySerial
 
# Setup
## Basics
 - sudo apt install python3-pip
 - sudo python3 -m pip install -r requirements.txt

We'll have it run with a power user account because this is NOT MEANT to be accisble from the net. If you do it, make another account and use that one instead (make it part of *dialout* group to access serial). My power user will be "pi".

## Configuration
 - Copy config.sample.py to config.py and customize at will
 - Make it start at start-up: edit /etc/rc.local and add "*/path/to/installation/*GrblWebStreamer/start-service.sh"
 - Reboot and test

# G-code things to remember
This helped me so in case:
 - Fxxxx sets the move speed in unit per minute (xxx=1800 == 30mm/sec)
 - Sxxx sets the laser power in per thousands (xxx=600 == 60.0%)
 - G0 is move but don't burn, G1 is move n burn
