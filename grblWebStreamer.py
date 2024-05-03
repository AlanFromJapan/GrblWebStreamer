import config
import serialUtils
import grblUtils
from  notifiers.baseNotifier import Job, JobType
import device
from persistence.db import LaserJobDB

from flask import Flask, flash, request, send_file, render_template, abort, redirect, make_response, url_for
from datetime import datetime, timedelta
import sys
import os
import logging

from werkzeug.utils import secure_filename
import socket

from werkzeug.serving import get_interface_ip
from markupsafe import escape

############################ BEFORE ANYTHING ELSE #################################
#logging
logging.basicConfig(filename=config.myconfig["logfile"], level=config.myconfig.get("log level", logging.DEBUG), format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting app")

latest_file = None
D = device.Device(config.myconfig["device port"])

#make sure upload folder exists
if not os.path.exists(config.myconfig["upload folder"]):
    os.makedirs(config.myconfig["upload folder"])

############################ FLASK VARS #################################
app = Flask(__name__, static_url_path='')
app.secret_key = config.myconfig["secret_key"]

ALLOWED_EXTENSIONS = set(['nc', 'gc'])

# return if filename is in the list of acceptable files
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#Makes a thumnail for a GRBL file
def genThumbnail(fileFullPath):
    #try to make a thumbnail img
    filename = secure_filename(os.path.basename(fileFullPath))
    try:
        stats = grblUtils.createThumbnailForJob(fileFullPath)
        flash(f'Successfully created thumbnail for [{escape(filename)}]', "success")
        return stats
    except Exception as ex:
        flash(f'Failed creating thumbnail for [{escape(filename)}] with message "{str(ex)}"', "error")

        logging.error ("error on making thumbnail: " + str(ex))


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
#landing page
@app.route('/')
@app.route('/home')
def homepage():    
    global latest_file

    # #not logged in? go away
    # if None == request.cookies.get('username'):
    #     return redirect("login")
    return render_template("home01.html", pagename="Home", latest=latest_file)


#---------------------------------------------------------------------------------------
#handler for file upload that redirect to file process (not a page)
@app.route('/upload-file', methods=['POST'])
def upload_file():    
    global latest_file
        
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', "error")
            return redirect("/")
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', "error")
            return redirect("/")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            #force extension to .nc
            filename = filename[:filename.rfind(".")] + ".nc"

            file.save(os.path.join(config.myconfig['upload folder'], filename))

            flash(f'Successfully uploaded file [{escape(filename)}]', "success")

            #try to make a thumbnail img
            stats = genThumbnail(os.path.join(config.myconfig['upload folder'], filename))

            logging.info(f"{filename} > stats: {stats}")

            #save in DB
            j = LaserJobDB(filename, stats=stats)
            LaserJobDB.record_job(j)

            return redirect(url_for('process_file', filename=filename))
        else:

            flash(f"Forbidden file extension, use one of {ALLOWED_EXTENSIONS}", "error")
            return redirect("/")


#handler for files fetching from all the connectors. As get too so can get wget-cron-ed easily. Useful maybe?
@app.route('/fetch-file-connectors', methods=['POST', 'GET'])
def fetch_files_connectors():    
    try:
        count = 0
        for conn in config.myconfig.get("connectors", []):
            flash(f"Fetching files from { str(conn) } ...", "info")
            while True:            
                filename = conn.fetchLatest()
                if filename:
                    count = count + 1
                    flash(f"Successfully fetched file [{escape(filename)}]", "success")
                    #try to make a thumbnail img
                    genThumbnail(os.path.join(config.myconfig['upload folder'], filename))
                else:
                    break
        flash(f"Done fetching {count} file(s) from connectors.", "info")
    except Exception as ex:
        logging.error(f"ERROR while fetching files from connectors with message '{ex}'")
        flash(f"ERROR while fetching files from connectors with message '{ex}'", "error")
    
    return redirect("/")


#---------------------------------------------------------------------------------------
#The "main" page to process a file
@app.route('/process-file/<filename>', methods=['GET','POST'])
def process_file(filename):    
    global latest_file
    
    fileOnDisk = os.path.join(config.myconfig['upload folder'], secure_filename(filename))

    #exists?
    if not os.path.exists(fileOnDisk):
        flash(f'File [{escape(filename)}] not found', "error")
        logging.error(f"process_file(): [{fileOnDisk}] not found")
        return redirect("/")

    #remember latest
    latest_file = filename

    #POST BACK POST BACK POST BACK
    if request.method == 'POST':
        if request.form["action"] == "deletefile":
            #delete the file from disk
            try:
                grblUtils.deleteThumbnailForJob(filename)
                os.remove(fileOnDisk)
                flash(f'Successfully deleted file [{escape(filename)}]', "success")
                latest_file = None
                return redirect("/")
            except Exception as ex:
                flash(f'Failed deleting file [{escape(filename)}]', "error")
                logging.error(f"ERROR while deleting file {filename} with message '{ex}'")
        elif request.form["action"] == "regen_thumbnail":
            #try to (re)make a thumbnail img
            genThumbnail(fileOnDisk)
        
        elif request.form["action"] == "stop":
            #STOP!
            D.emergencyStopRequested = True
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
            j = Job(secure_filename(filename), jobType=jt)

            #notify
            for x in config.myconfig["notifiers"]: x.NotifyJobStart(j)

            try:
                if request.form["action"] == "simulate":
                    #do the job but with no laser power
                    D.simulate(fileOnDisk, asynchronous=True, job = j)

                elif request.form["action"] == "burn":
                    #the real thing
                    D.burn(fileOnDisk, asynchronous=True, job = j)
                    
                elif request.form["action"] == "frame":
                    #frame the workspace SYNCHRONOUSLY
                    D.frame(fileOnDisk, asynchronous=True, job = j)

                elif request.form["action"] == "frameCornerPause":
                    #frame the workspace SYNCHRONOUSLY with a few second pause at each corner
                    D.frameWithCornerPause(fileOnDisk, asynchronous=True, job = j)
                    
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
        
    return render_template("process01.html", pagename=f"Process file [{escape(filename)}]", filename=filename, filebody=body, filesize=f"{filesize:0.1f}", latest=latest_file)
    



#---------------------------------------------------------------------------------------
#The page to play with the device
@app.route('/device', methods=['GET','POST'])
def device_page():    
    global latest_file
    
    #POST BACK POST BACK POST BACK
    if request.method == 'POST':
        # Change port
        if request.form["action"] == "change-port":
            p = request.form["newtarget"]
            p = p[:p.index(" ")]
            D.reconnect(p)
            flash(f"Updated in use target serial port to '{p}'.", "success")
        #Send command
        elif request.form["action"] == "cmd":
            res = D.sendCommand(request.form["cmd"] )
            flash(f"Sent command '{ request.form['cmd'] }', got response '{ res }'")
        #Send Resume command
        elif request.form["action"] == "resume":
            res = D.sendCommand(device.WellKnownCommands.CMD_RESUME.value )
            flash(f"Sent RESUME command (~), got response '{ res }'.\nCheck if device is in IDLE status now.")

            res = D.sendCommand(device.WellKnownCommands.CMD_STATUS.value )
            flash(f"Sent command '{ device.WellKnownCommands.CMD_STATUS.value }', got response '{ res }'")
        #Send status
        elif request.form["action"] == "status":
            res = D.sendCommand(device.WellKnownCommands.CMD_STATUS.value )
            flash(f"Sent command '{ device.WellKnownCommands.CMD_STATUS.value }', got response '{ res }'")
        #Send goto orign
        elif request.form["action"] == "goto-origin":
            res = D.sendCommand(device.WellKnownCommands.CMD_GOTO_ORIGIN.value )
            flash(f"Sent command '{ device.WellKnownCommands.CMD_GOTO_ORIGIN.value }', got response '{ res }'")
        #Disconnect
        elif request.form["action"] == "disconnect":
            D.disconnect()
            flash(f"Disconnected from '{ D.port }'", "success")
        else:
            flash("Unknow or TODO implement", "error")

    #Page generation
    body = ''

    body += f'<li>Current target Serial port: { D.port }</li>'

    ports = serialUtils.listAvailableSerialPorts() 
    if len(ports) > 0:
        body += "<ul>"
        for p in ports:
            body += f'<li>Currently available port: { p }</li>'

        body += "</ul>"

        if not D.port in [p[:p.index(" ")] for p in ports]:
            flash("Target port is not available: change the port or check connections.", "error")    
    else:
        flash("No opened serial port found. Is laser/CNC connected?", "error")

    body = """<ul>""" + body + "</ul>"

    return render_template("device01.html", pagename="Device", settings=body, ports=ports, latest=latest_file)



#---------------------------------------------------------------------------------------
#list of GRBL files
def getGRBLfiles():
    return [l for l in os.listdir(config.myconfig['upload folder']) if os.path.isfile(os.path.join(config.myconfig['upload folder'], l)) and l.lower()[-3:] == '.nc']

#List the recently sent files
@app.route('/replay', methods=['GET','POST'])
def replay_page():    
    global latest_file

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

    return render_template("replay01.html", pagename="Replay", pagecontent=body, latest=latest_file)
    



#---------------------------------------------------------------------------------------
#The page to turn off the PC
@app.route('/OS', methods=['GET','POST'])
def os_page():    
    global latest_file
    
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
    
    return render_template("os01.html", pagename="OS", latest=latest_file)





#---------------------------------------------------------------------------------------
#Shows the log file
@app.route('/logs', methods=['GET','POST'])
def logs_page():    
    global latest_file

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

    return render_template("template01.html", pagename="Logs", pagecontent=body, latest=latest_file)
    



#---------------------------------------------------------------------------------------
#Returns current status (Webservice - NOT A PAGE)
@app.route('/status')
def status_ws():
    stat = f"{{ \"status\": \"{D.status.name}\", \"port\": \"{D.port}\" }}"
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
