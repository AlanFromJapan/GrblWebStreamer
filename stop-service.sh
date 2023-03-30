#!/bin/bash

PID=`ps -fe | grep 'grblWebStreamer.py' |  grep python3 | grep -v root | awk '{print $2}' `
if [ -z "$PID" ]; then
    echo Not running
else
    CMD="sudo kill "$PID
    echo $CMD
    eval $CMD
fi
