from  notifiers.baseNotifier import BaseNotifier, FlashNotifier
import logging

myconfig = {
    "isProd" : False,
    "app_port" : 12380,
    "upload folder" : "/tmp",
    "secret_key" : "whatever you want!!",
    "notif on startup" : True,

    "device port" : "/dev/ttyACM0",

    "logfile" : "/tmp/grblLogs.log",

    "notifiers" : [ BaseNotifier(), FlashNotifier() ],

    "log level" : logging.DEBUG,

    "connectors" : []
}