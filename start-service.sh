#!/bin/bash

here=`dirname $0`
logdir="/var/local/GrblWebStreamer.files/logs"

sudo -u pi -s nohup $here/run.sh > $logdir/ipcampy.log 2>&1 &

#if ran from /etc/rc.local it must complete nicely
exit 0
