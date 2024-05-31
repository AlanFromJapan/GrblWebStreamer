from  notifiers.baseNotifier import BaseNotifier, FlashNotifier
from  notifiers.linebot import LineBotNotifier
from connectors.baseConnector import BaseConnector
from connectors.zmqSimplestorageConnector import ZMQSimpleStorageConnector
import logging
import os

#extracted here since needed at multiple places
__STORAGE_PATH = "/tmp/grblWebStreamerStorage/"

myconfig = {
    "isProd" : False,
    "app_port" : 12380,
    "upload folder" : os.path.join(__STORAGE_PATH, "uploads"),
    "secret_key" : "whatever you want!!",
    "notif on startup" : True,

    "device port" : "/dev/ttyACM0",

    "logfile" : os.path.join(__STORAGE_PATH, "logs", "grblWebStreamer.log"),

    "notifiers" : [ BaseNotifier(), FlashNotifier() ],

    "log level" : logging.DEBUG,

    "connectors" : [],
    #"connectors" : [ ZMQSimpleStorageConnector(storagePath=os.path.join(__STORAGE_PATH, "uploads"), serverHostPort="myhomeserver:55554") ],

    "G4 delays handled by device" : True,

    "db_file": os.path.join(__STORAGE_PATH, "db", "laser_jobs.db"),
}

#Make sure necessary folders exist
os.makedirs(os.path.join(__STORAGE_PATH, "logs"), exist_ok=True)
os.makedirs(os.path.join(__STORAGE_PATH, "uploads"), exist_ok=True)
os.makedirs(os.path.join(__STORAGE_PATH, "db"), exist_ok=True)
