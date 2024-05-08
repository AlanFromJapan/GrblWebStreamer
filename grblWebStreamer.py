import config
import serialUtils
import grblUtils
from  notifiers.baseNotifier import Job, JobType
import device
from persistence.db import LaserJobDB

from flask import Flask, flash, request, send_file, render_template, abort, redirect, make_response, url_for, current_app
from datetime import datetime, timedelta
import sys
import os
import logging

from werkzeug.utils import secure_filename
import socket

from werkzeug.serving import get_interface_ip
from markupsafe import escape

#Blueprints
from bp_device.device import bp_device
from bp_home.bp_home import bp_home

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





#The shared variables to be stored in the app context
with app.app_context():
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

############################ Web requests ###############################


#---------------------------------------------------------------------------------------
#The "main" page to process a file
@app.route('/process-file/<filename>', methods=['GET','POST'])
def process_file(filename):      
    fileOnDisk = os.path.join(config.myconfig['upload folder'], secure_filename(filename))

    #exists?
    if not os.path.exists(fileOnDisk):
        flash(f'File [{escape(filename)}] not found', "error")
        logging.error(f"process_file(): [{fileOnDisk}] not found")
        return redirect("/")

    #remember latest    
    current_app.latest_file = filename

    jobDetails = None
    try:
        jobDetails = LaserJobDB.get_job(filename)
    except Exception as ex:
        flash("Error while fetching job details from DB", "error")
        pass

    #POST BACK POST BACK POST BACK
    if request.method == 'POST':
        if request.form["action"] == "deletefile":
            #delete the file from disk
            try:
                grblUtils.deleteThumbnailForJob(filename)
                os.remove(fileOnDisk)
                flash(f'Successfully deleted file [{escape(filename)}]', "success")
                current_app.latest_file = None
                return redirect("/")
            except Exception as ex:
                flash(f'Failed deleting file [{escape(filename)}]', "error")
                logging.error(f"ERROR while deleting file {filename} with message '{ex}'")
        elif request.form["action"] == "regen_thumbnail":
            #try to (re)make a thumbnail img
            genThumbnail(fileOnDisk)
        
        elif request.form["action"] == "stop":
            #STOP!
            current_app.D.emergencyStopRequested = True
            flash(f"Emergency stop requested. Check device status.", "success")

        else:
            # START A JOB 
            #start time
            jt = JobType.BURN
            try:
                #too lazy to check possible values etc. 
                jt = JobType[request.form["action"].upper()]
            except:
                pass
            
            #this job
            j = Job(secure_filename(filename), jobType=jt, details=jobDetails)

            #notify
            for x in config.myconfig["notifiers"]: x.NotifyJobStart(j)

            try:
                if request.form["action"] == "simulate":
                    #do the job but with no laser power
                    current_app.D.simulate(fileOnDisk, asynchronous=True, job = j)

                elif request.form["action"] == "burn":
                    #the real thing
                    current_app.D.burn(fileOnDisk, asynchronous=True, job = j)
                    
                elif request.form["action"] == "frame":
                    #frame the workspace SYNCHRONOUSLY
                    current_app.D.frame(fileOnDisk, asynchronous=True, job = j)

                elif request.form["action"] == "frameCornerPause":
                    #frame the workspace SYNCHRONOUSLY with a few second pause at each corner
                    current_app.D.frameWithCornerPause(fileOnDisk, asynchronous=True, job = j)
                    
                else:
                    flash("Unknow or TODO implement", "error")
            except Exception as ex:
                logging.error(f"ERROR while processing file {filename} with message '{ex}'")    
                #notify
                for x in config.myconfig["notifiers"]: x.NotifyJobError(j, extra=str(ex))

    body = ''
    MAX_LINES=100
    with open(fileOnDisk, mode="r") as f:
        #read up to 100 lines
        lines = f.readlines()
        body = '\n'.join(lines[:MAX_LINES if len(lines)> MAX_LINES else len(lines)])
        body += "\n[...]" if len(lines) > MAX_LINES else ""
    
    filesize = float(os.path.getsize(fileOnDisk)) / 1000.0
        
    return render_template("process01.html", pagename=f"Process file [{escape(filename)}]", filename=filename, filebody=body, filesize=f"{filesize:0.1f}", latest=current_app.latest_file, jobDetails=jobDetails)
    






#---------------------------------------------------------------------------------------
#list of GRBL files
def getGRBLfiles():
    return [l for l in os.listdir(config.myconfig['upload folder']) if os.path.isfile(os.path.join(config.myconfig['upload folder'], l)) and l.lower()[-3:] == '.nc']

#List the recently sent files
@app.route('/replay', methods=['GET','POST'])
def replay_page():    

    #list of files
    l = getGRBLfiles()
        
    #POST BACK POST BACK POST BACK
    if request.method == 'POST':
        # Shutdown
        if request.form["action"] in ["deleteall", "deleteall1w"]:
            count = 0
            for f in l:
                try:
                    if request.form["action"] == "deleteall1w":
                        #delete only files older than 1 week
                        if (datetime.now() - timedelta(days=7)) < datetime.fromtimestamp(os.path.getmtime(os.path.join(config.myconfig['upload folder'], f))):
                            continue
                    os.remove(os.path.join(config.myconfig['upload folder'], f))
                    grblUtils.deleteThumbnailForJob(f)
                    count += 1
                except Exception as ex:
                    flash(f'Failed deleting file [{escape(f)}]', "error")
                    logging.error(f"ERROR while deleting file {f} with message '{ex}'")
            flash(f'Successfully deleted {count} file(s)', "success")

            #refresh list
            l = getGRBLfiles()


    body = ''
    content = ""

    #sorted ignorecase
    l = sorted(l, key=lambda x: str(x).lower())

    body += """
Click to (re)process uploaded files:"""

    content = ""
    for f in l:
        content += f"""<div class='replayBlock'><a href='/process-file/{ f }'><img src='/thumbnails/{ f }.png'/><br/>{ f }</a></div>"""

    body += "<div class='replayBlockList'>" +  content + "</div>"


    content = ""
    for f in l:
        content += f"<li><a href='/process-file/{ f }'>{ f }</a></li>"
    body += """<ul class="replaylist">""" + content + "</ul>"


    body += """<br/>
Remember: go to the <a href="/">Home page</a> to upload a script!"""

    return render_template("replay01.html", pagename="Replay", pagecontent=body, latest=current_app.latest_file)
    



#---------------------------------------------------------------------------------------
#The page to turn off the PC
@app.route('/OS', methods=['GET','POST'])
def os_page():    
    
    #POST BACK POST BACK POST BACK
    if request.method == 'POST':
        # Shutdown
        if request.form["action"] == "shutdown":
            os.system("sudo shutdown -h now")
            flash(f"Going for SHUTDOWN now. If it does not happen, maybe you're not sudoer or you need to edit visudo to allow the user to run /sbin/shudown without password.", "success")
        #Reboot
        elif request.form["action"] == "reboot":
            os.system("sudo shutdown -r now")
            flash(f"Going for REBOOT now. If it does not happen, maybe you're not sudoer or you need to edit visudo to allow the user to run /sbin/shudown without password.", "success")
        else:
            flash("Unknow or TODO implement", "error")    
    
    return render_template("os01.html", pagename="OS", latest=current_app.latest_file)





#---------------------------------------------------------------------------------------
#Shows the log file
@app.route('/logs', methods=['GET','POST'])
def logs_page():    

    #POST BACK POST BACK POST BACK
    if request.method == 'POST':
        # One button, submit type so has to be clean. If need more make a special page and rewrite it like other pages future lazy me

        #"touch" clear the file a la python
        open (config.myconfig["logfile"], "w").close()
 

    body = f"""
<h1>Logs</h1>
<p>File is at <code>{ config.myconfig["logfile"] }</code>:</p>
    <form id="theForm" method="post" >
        <input type="submit" name="action" value="Purge logs" />
    </form>
<pre>""" 

    try:
        with open (config.myconfig["logfile"], "r") as f:
            body += f.read()
    except Exception as ex:
        body += "*** NO LOG FILE ***<br/>"
        body += "Exception message: "+ str(ex)

    body += "</pre>"

    return render_template("template01.html", pagename="Logs", pagecontent=body, latest=current_app.latest_file)
    



#---------------------------------------------------------------------------------------
#Returns current status (Webservice - NOT A PAGE)
@app.route('/status')
def status_ws():
    stat = f"{{ \"status\": \"{current_app.D.status.name}\", \"port\": \"{current_app.D.port}\" }}"
    return stat


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
