#!/bin/bash

here=`dirname $0`
logdir="/tmp/"

echo Restart initiated at `date` > "$logdir"ipcampy_restart_latest.log
echo ***STOP*** >> "$logdir"ipcampy_restart_latest.log
$here/stop-service.sh >> "$logdir"ipcampy_restart_latest.log 2>&1
echo ***START*** >> "$logdir"ipcampy_restart_latest.log
$here/start-service.sh >> "$logdir"ipcampy_restart_latest.log 2>&1
echo Restart completed at `date` >> "$logdir"ipcampy_restart_latest.log
