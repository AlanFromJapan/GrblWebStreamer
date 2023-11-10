#!/bin/bash

here=`dirname $0`
logdir="/var/local/GrblWebStreamer/logs"

sudo -u pi -s nohup $here/run.sh > $logdir/grblWebStreamer.log 2>&1 &

#if ran from /etc/rc.local it must complete nicely
exit 0
