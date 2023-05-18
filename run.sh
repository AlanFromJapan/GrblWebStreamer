#!/bin/bash

here=`dirname $0`

#-u so the print() aren't buffered and you can see something in the logs!
python3 -u $here/grblWebStreamer.py
