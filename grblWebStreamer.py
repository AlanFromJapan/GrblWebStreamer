import config
import device
from persistence.db import LaserJobDB

from flask import Flask, current_app
import sys
import os
import logging
import socket

from werkzeug.serving import get_interface_ip

#Blueprints
from bp_device.device import bp_device
from bp_home.bp_home import bp_home
from bp_os.bp_os import bp_os
from bp_replay.bp_replay import bp_replay
from bp_processOne.bp_processOne import bp_processOne
from bp_api.bp_api import bp_api

############################ BEFORE ANYTHING ELSE #################################
#logging
logging.basicConfig(filename=config.myconfig["logfile"], level=config.myconfig.get("log level", logging.DEBUG), format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting app")

#make sure upload folder exists
if not os.path.exists(config.myconfig["upload folder"]):
    os.makedirs(config.myconfig["upload folder"])

############################ FLASK VARS #################################
app = Flask(__name__, static_url_path='')
app.secret_key = config.myconfig["secret_key"]

#register the blueprint
app.register_blueprint(bp_device)
app.register_blueprint(bp_home)
app.register_blueprint(bp_os)
app.register_blueprint(bp_replay)
app.register_blueprint(bp_processOne)
app.register_blueprint(bp_api)



#The shared variables to be stored in the app context
with app.app_context():
    if not hasattr(current_app, "D") or current_app.D is None:
        current_app.D = device.Device(config.myconfig["device port"])
    current_app.latest_file = None


############################ App Events ###############################
#push a message to say that flask is ready (so I get a notif via Line)
def flask_ready():
    for x in config.myconfig["notifiers"]: 
        try:
            x.NotifyServerReady(get_interface_ip(socket.AF_INET) + ":" + str(config.myconfig["app_port"]))
        except Exception as ex:
            #ignore
            #print(ex)
            pass

########################################################################################
## Main entry point
#
if __name__ == '__main__':
    print ("""
USAGE:
    python3 grblWebStreamer.py [path_to_cert.pem path_to_key.perm]

If you don't provide the *.pem files it will start as an HTTP app. You need to pass both .pem files to run as HTTPS.
    """)
    try:
        #init the DB   
        LaserJobDB.initialize(config.myconfig.get("db_file", "laser_jobs.db"))

        #start web interface
        app.debug = not config.myconfig["isProd"]
        
        #notif of the startup
        if "notif on startup" in config.myconfig and config.myconfig["notif on startup"]:
            flask_ready()

        #try to find the device
        with app.app_context():
            device.Device.start_thread_check_for_device(current_app.D)

        #run as HTTPS?
        if len(sys.argv) == 3:
            #go HTTPS
            logging.info("start as HTTPSSSSSSSSSSS")
            app.run(host='0.0.0.0', port=int(config.myconfig["app_port"]), threaded=True, ssl_context=(sys.argv[1], sys.argv[2]))
        else:
            #not secured HTTP
            logging.info("start as HTTP unsecured")
            app.run(host='0.0.0.0', port=int(config.myconfig["app_port"]), threaded=True)

    finally:
        #close the DB
        LaserJobDB.close()

        pass
