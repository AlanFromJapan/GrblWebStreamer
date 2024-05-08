from flask import Blueprint, render_template, current_app, request, flash, escape, redirect
import os
import config
import grblUtils
import logging
from werkzeug.utils import secure_filename
from persistence.db import LaserJobDB
from  notifiers.baseNotifier import Job, JobType


bp_processOne = Blueprint('bp_processOne', __name__)


#---------------------------------------------------------------------------------------
#The "main" page to process a file
@bp_processOne.route('/process-file/<filename>', methods=['GET','POST'])
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
            grblUtils.genThumbnail(fileOnDisk)
        
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
    
