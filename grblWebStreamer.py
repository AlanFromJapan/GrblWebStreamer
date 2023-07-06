import config
import serialUtils
import grblUtils
from  notifiers.baseNotifier import Job, JobType

from flask import Flask, flash, request, send_file, render_template, abort, redirect, make_response, url_for
from datetime import datetime, timedelta
import sys
import os
import time

from werkzeug.utils import secure_filename
import socket

from werkzeug.serving import get_interface_ip
from markupsafe import escape

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
        grblUtils.createThumbnailForJob(fileFullPath)
        flash(f'Successfully created thumbnail for [{escape(filename)}]', "success")
    except Exception as ex:
        flash(f'Failed creating thumbnail for [{escape(filename)}] with message "{str(ex)}"', "error")
        #TODO LOG
        print ("error on making thumbnail: " + str(ex))


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
    # #not logged in? go away
    # if None == request.cookies.get('username'):
    #     return redirect("login")
    return render_template("home01.html", pagename="Home")


#---------------------------------------------------------------------------------------
#handler for file upload that redirect to file process (not a page)
@app.route('/upload-file', methods=['POST'])
def upload_file():
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
            genThumbnail(os.path.join(config.myconfig['upload folder'], filename))

            return redirect(url_for('process_file', filename=filename))
        else:

            flash(f"Forbidden file extension, use one of {ALLOWED_EXTENSIONS}", "error")
            return redirect("/")





#---------------------------------------------------------------------------------------
#The "main" page to process a file
@app.route('/process-file/<filename>', methods=['GET','POST'])
def process_file(filename):
    fileOnDisk = os.path.join(config.myconfig['upload folder'], secure_filename(filename))

    #POST BACK POST BACK POST BACK
    if request.method == 'POST':
        if request.form["action"] == "deletefile":
            #delete the file from disk
            try:
                grblUtils.deleteThumbnailForJob(filename)
                os.remove(fileOnDisk)
                flash(f'Successfully deleted file [{escape(filename)}]', "success")
                return redirect("/")
            except Exception as ex:
                flash(f'Failed deleting file [{escape(filename)}]', "error")
                print(f"ERROR while deleting file {filename} with message '{ex}'")
        elif request.form["action"] == "regen_thumbnail":
            #try to (re)make a thumbnail img
            genThumbnail(fileOnDisk)
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
                    serialUtils.simulateFile(config.myconfig["device port"], fileOnDisk)
                    j.finish()

                    #notify
                    for x in config.myconfig["notifiers"]: x.NotifyJobCompletion(j)
                elif request.form["action"] == "burn":
                    #the real thing
                    serialUtils.processFile(config.myconfig["device port"], fileOnDisk)
                    j.finish()
                    
                    #notify
                    for x in config.myconfig["notifiers"]: x.NotifyJobCompletion(j)
                elif request.form["action"] == "frame":
                    #frame the workspace
                    grblUtils.generateFrame(fileOnDisk)
                    j.finish()
                    
                    #notify
                    for x in config.myconfig["notifiers"]: x.NotifyJobCompletion(j)
                else:
                    flash("Unknow or TODO implement", "error")
            except Exception as ex:
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
        
    return render_template("process01.html", pagename=f"Process file [{escape(filename)}]", filename=filename, filebody=body, filesize=f"{filesize:0.1f}")
    



#---------------------------------------------------------------------------------------
#The page to play with the device
@app.route('/device', methods=['GET','POST'])
def device_page():
    #POST BACK POST BACK POST BACK
    if request.method == 'POST':
        # Change port
        if request.form["action"] == "change-port":
            p = request.form["newtarget"]
            p = p[:p.index(" ")]
            config.myconfig["device port"] = p
            flash(f"Updated in use target serial port to '{p}'.", "success")
        #Send command
        elif request.form["action"] == "cmd":
            res = serialUtils.sendCommand(config.myconfig["device port"], request.form["cmd"] )
            flash(f"Sent command '{ request.form['cmd'] }', got response '{ res }'")
        #Send Resume command
        elif request.form["action"] == "resume":
            res = serialUtils.sendCommand(config.myconfig["device port"], serialUtils.CMD_RESUME )
            flash(f"Sent RESUME command (~), got response '{ res }'.\nCheck if device is in IDLE status now.")
        #Send status
        elif request.form["action"] == "status":
            res = serialUtils.sendCommand(config.myconfig["device port"], serialUtils.CMD_STATUS )
            flash(f"Sent command '{ serialUtils.CMD_STATUS }', got response '{ res }'")
        #Send goto orign
        elif request.form["action"] == "goto-origin":
            res = serialUtils.sendCommand(config.myconfig["device port"], serialUtils.CMD_GOTO_ORIGIN )
            flash(f"Sent command '{ serialUtils.CMD_GOTO_ORIGIN }', got response '{ res }'")
        #Disconnect
        elif request.form["action"] == "disconnect":
            serialUtils.disconnect()
            flash(f"Disconnected from '{ config.myconfig['device port'] }'", "success")
        else:
            flash("Unknow or TODO implement", "error")

    #Page generation
    body = ''

    body += f'<li>Current target Serial port: { config.myconfig["device port"] }</li>'

    ports = serialUtils.listAvailableSerialPorts() 
    if len(ports) > 0:
        body += "<ul>"
        for p in ports:
            body += f'<li>Currently available port: { p }</li>'

        body += "</ul>"

        if not config.myconfig["device port"] in [p[:p.index(" ")] for p in ports]:
            flash("Target port is not available: change the port or check connections.", "error")    
    else:
        flash("No opened serial port found. Is laser/CNC connected?", "error")

    body = """<ul>""" + body + "</ul>"

    return render_template("device01.html", pagename="Device", settings=body, ports=ports)



#---------------------------------------------------------------------------------------
#List the recently sent files
@app.route('/replay')
def replay_page():
    body = ''
    content = ""

    #list of files
    l = [l for l in os.listdir(config.myconfig['upload folder']) if os.path.isfile(os.path.join(config.myconfig['upload folder'], l)) and l.lower()[-3:] == '.nc']
    #sorted ignorecase
    l = sorted(l, key=lambda x: str(x).lower())

    body += """
<h1>Recently uploaded files</h1>
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

    return render_template("template01.html", pagename="Replay", pagecontent=body)
    



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
    
    return render_template("os01.html", pagename="OS")





#---------------------------------------------------------------------------------------
#Shows the log file
@app.route('/logs')
def logs_page():
    body = f"""
<h1>Logs</h1>
<p>File is at <code>{ config.myconfig["logfile"] }</code>:</p>
<pre>""" 

    try:
        with open (config.myconfig["logfile"], "r") as f:
            body += f.read()
    except Exception as ex:
        body += "*** NO LOG FILE ***<br/>"
        body += "Exception message: "+ str(ex)

    body += "</pre>"

    return render_template("template01.html", pagename="Logs", pagecontent=body)
    



#---------------------------------------------------------------------------------------
#Returns current status (Webservice - NOT A PAGE)
@app.route('/status')
def status_ws():
    stat = ''
    stat += f'Port: {config.myconfig["device port"]}\n'

    connStatus = serialUtils.serialStatusEnum()
    stat += f'Connection: {connStatus.name}\n'

    state = grblUtils.getDeviceStatus()
    stat += f'Device: {state}'

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
        #start web interface
        app.debug = not config.myconfig["isProd"]
        
        #notif of the startup
        if "notif on startup" in config.myconfig and config.myconfig["notif on startup"]:
            flask_ready()

        #run as HTTPS?
        if len(sys.argv) == 3:
            #go HTTPS
            print("INFO: start as HTTPSSSSSSSSSSS")
            app.run(host='0.0.0.0', port=int(config.myconfig["app_port"]), threaded=True, ssl_context=(sys.argv[1], sys.argv[2]))
        else:
            #not secured HTTP
            print("INFO: start as HTTP unsecured")
            app.run(host='0.0.0.0', port=int(config.myconfig["app_port"]), threaded=True)

    finally:
        pass
