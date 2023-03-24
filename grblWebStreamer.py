import config
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

@app.route('/')
def homepage():
    # #not logged in? go away
    # if None == request.cookies.get('username'):
    #     return redirect("login")
    return render_template("home01.html", pagename="Home")


#handler for file upload that redirect to file process (not a page)
@app.route('/upload-file', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect("/")
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect("/")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(config.myconfig['upload folder'], filename))

            flash(f'Successfully uploaded file [{escape(filename)}]')

            return redirect(url_for('process_file', filename=filename))


#The "main" page to process a file
@app.route('/process-file/<filename>')
def process_file(filename):
    body = ''
    with open(os.path.join(config.myconfig['upload folder'], secure_filename(filename)), mode="r") as f:
        body = '\n'.join(f.readlines())
        
    return render_template("process01.html", pagename=f"Process file [{escape(filename)}]", filename=filename, filebody=body)
    

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
            app.run(host='0.0.0.0', port=int(config.myconfig["app_port"]), threaded=True, ssl_context=(sys.argv[1], sys.argv[2]))
        else:
            #not secured HTTP
            print("INFO: start as HTTP unsecured")
            app.run(host='0.0.0.0', port=int(config.myconfig["app_port"]), threaded=True)

    finally:
        pass
