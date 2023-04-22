# GrblWebStreamer
A simple python headless and web interface UI to stream GRBL to a Laser engraver, that can push you notifications to Naver Line.

Why? Because I don't want my laptop stuck to the laser all the time it burns. And because LightBurn is great but crashes EVERY TIME my Ubuntu locks screen (that hopefully will be fixed by them one day but until then). And because I find it fun to do (maybe mostly, ok).

![Job processing](https://github.com/AlanFromJapan/grbl2image/blob/main/sample.gcode/Screenshot01.png?raw=true)

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
 - Flask
 - pySerial
 - [grbl2image](https://github.com/AlanFromJapan/grbl2image)
 - line-bot-sdk
 
# Setup
## Basics
 - `sudo apt install python3-pip`
 - `sudo python3 -m pip install -r requirements.txt`

We'll have it run with a power user account because this is **NOT MEANT** to be accessible from the net. If you do it, *make another account that is not sudoer* and use that one instead (make it part of *dialout* group to access serial). My power user will be "pi".

## Configuration
 - Copy config.sample.py to config.py and customize at will
 - Make it start at start-up: edit */etc/rc.local* and add `/path/to/installation/GrblWebStreamer/start-service.sh`
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
