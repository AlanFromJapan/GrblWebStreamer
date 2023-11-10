#!/bin/bash

here=`dirname $0`
logdir="/var/local/GrblWebStreamer/logs"

echo Restart initiated at `date` > "$logdir"restart_log.log
echo ***STOP*** >> "$logdir"restart_log.log
$here/stop-service.sh >> "$logdir"restart_log.log 2>&1
echo ***START*** >> "$logdir"restart_log.log
$here/start-service.sh >> "$logdir"restart_log.log 2>&1
echo Restart completed at `date` >> "$logdir"restart_log.log
