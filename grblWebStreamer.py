import config
import serialUtils

from flask import Flask, flash, request, send_file, render_template, abort, redirect, make_response, url_for
from datetime import datetime, timedelta
import sys
import os
import time

from werkzeug.utils import secure_filename
from markupsafe import escape

############################ FLASK VARS #################################
app = Flask(__name__, static_url_path='')
app.secret_key = config.myconfig["secret_key"]

ALLOWED_EXTENSIONS = set(['nc'])


# return if filename is in the list of acceptable files
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

############################ Web requests ###############################

#---------------------------------------------------------------------------------------
#landing page
@app.route('/')
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
            file.save(os.path.join(config.myconfig['upload folder'], filename))

            flash(f'Successfully uploaded file [{escape(filename)}]', "success")

            return redirect(url_for('process_file', filename=filename))




#---------------------------------------------------------------------------------------
#The "main" page to process a file
@app.route('/process-file/<filename>', methods=['GET','POST'])
def process_file(filename):
    fileOnDisk = os.path.join(config.myconfig['upload folder'], secure_filename(filename))

    #POST BACK POST BACK POST BACK
    if request.method == 'POST':
        if request.form["action"] == "simulate":
            #do the job but with no laser power
            serialUtils.simulateFile(config.myconfig["device port"], fileOnDisk)
            flash(f"Finished SIMULATING file '{ secure_filename(filename)}'")


    body = ''
    with open(fileOnDisk, mode="r") as f:
        body = '\n'.join(f.readlines())
        
    return render_template("process01.html", pagename=f"Process file [{escape(filename)}]", filename=filename, filebody=body)
    



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
        #Send status
        elif request.form["action"] == "status":
            res = serialUtils.sendCommand(config.myconfig["device port"], serialUtils.CMD_STATUS )
            flash(f"Sent command '{ serialUtils.CMD_STATUS }', got response '{ res }'")
        #Send goto orign
        elif request.form["action"] == "goto-origin":
            res = serialUtils.sendCommand(config.myconfig["device port"], serialUtils.CMD_GOTO_ORIGIN )
            flash(f"Sent command '{ serialUtils.CMD_GOTO_ORIGIN }', got response '{ res }'")
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

    for f in [l for l in os.listdir(config.myconfig['upload folder']) if os.path.isfile(os.path.join(config.myconfig['upload folder'], l)) and l.lower()[-3:] == '.nc']:
        body += f"<li><a href='/process-file/{ f }'>{ f }</a></li>"

    body = """
<h1>Recently uploaded files</h1>
Click to (re)process uploaded files:
<ul>""" + body + "</ul>"
    return render_template("template01.html", pagename="Replay", pagecontent=body)




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
        
        #run as HTTPS?
        if len(sys.argv) == 3:
            #go HTTPS
            print("INFO: start as HTTPSSSSSSSSSSS")
            app.run(host='0.0.0.0', port=int(config.myconfig["app_port"]), threaded=False, ssl_context=(sys.argv[1], sys.argv[2]))
        else:
            #not secured HTTP
            print("INFO: start as HTTP unsecured")
            app.run(host='0.0.0.0', port=int(config.myconfig["app_port"]), threaded=False)

    finally:
        pass
