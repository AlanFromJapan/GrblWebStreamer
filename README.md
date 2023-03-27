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
 

# G-code things to remember
This helped me so in case:
 - Fxxxx sets the move speed in unit per minute (xxx=1800 == 30mm/sec)
 - Sxxx sets the laser power in per thousands (xxx=600 == 60.0%)
 - G0 is move but don't burn, G1 is move n burn
