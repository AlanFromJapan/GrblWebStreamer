#!/bin/bash

here=`dirname $0`
logdir="/tmp/"

sudo -u pi -s nohup $here/run_ssl.sh > "$logdir"ipcampy.log 2>&1 &

#if ran from /etc/rc.local it must complete nicely
exit 0