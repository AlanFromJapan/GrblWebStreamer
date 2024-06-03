from flask import Blueprint, render_template, current_app, request, flash, redirect, url_for, escape
from werkzeug.utils import secure_filename
import os
import logging
from persistence.db import LaserJobDB
import grblUtils
import config

bp_home = Blueprint('bp_home', __name__)



ALLOWED_EXTENSIONS = set(['nc', 'gc'])

# return if filename is in the list of acceptable files
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



#---------------------------------------------------------------------------------------
#landing page
@bp_home.route('/')
@bp_home.route('/home')
def homepage():    

    # #not logged in? go away
    # if None == request.cookies.get('username'):
    #     return redirect("login")
    
    latest_file = current_app.latest_file
    return render_template("home01.html", pagename="Home", latest=latest_file)


#---------------------------------------------------------------------------------------
#handler for file upload that redirect to file process (not a page)
@bp_home.route('/upload-file', methods=['POST'])
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
            stats = grblUtils.genThumbnail(os.path.join(config.myconfig['upload folder'], filename))

            logging.info(f"{filename} > stats: {stats}")

            #save in DB
            j = LaserJobDB(filename, stats=stats)
            LaserJobDB.record_job(j)

            return redirect(url_for('bp_processOne.process_file', filename=filename))
        else:

            flash(f"Forbidden file extension, use one of {ALLOWED_EXTENSIONS}", "error")
            return redirect("/")


#handler for files fetching from all the connectors. As get too so can get wget-cron-ed easily. Useful maybe?
@bp_home.route('/fetch-file-connectors', methods=['POST', 'GET'])
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
                    stats = grblUtils.genThumbnail(os.path.join(config.myconfig['upload folder'], filename))

                    logging.info(f"{filename} > stats: {stats}")

                    #save in DB
                    j = LaserJobDB(filename, stats=stats)
                    LaserJobDB.record_job(j)
                else:
                    break
        flash(f"Done fetching {count} file(s) from connectors.", "info")
    except Exception as ex:
        logging.error(f"ERROR while fetching files from connectors with message '{ex}'")
        flash(f"ERROR while fetching files from connectors with message '{ex}'", "error")
    
    return redirect("/")
