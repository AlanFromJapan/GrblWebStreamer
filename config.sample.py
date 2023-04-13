from  notifiers.baseNotifier import BaseNotifier, FlashNotifier

myconfig = {
    "isProd" : False,
    "app_port" : 56554,
    "upload folder" : "/tmp",
    "secret_key" : "whatever you want!!",

    "device port" : "/dev/ttyACM0",

    "logfile" : "/tmp/grblLogs.log",

    "notifiers" : [ BaseNotifier(), FlashNotifier() ]
}