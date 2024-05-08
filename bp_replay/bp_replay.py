from flask import Blueprint, render_template, current_app, request, flash, escape
import os
import config
from datetime import datetime, timedelta
import grblUtils
import logging


bp_replay = Blueprint('bp_replay', __name__)


#---------------------------------------------------------------------------------------
#list of GRBL files
def getGRBLfiles():
    return [l for l in os.listdir(config.myconfig['upload folder']) if os.path.isfile(os.path.join(config.myconfig['upload folder'], l)) and l.lower()[-3:] == '.nc']

#List the recently sent files
@bp_replay.route('/replay', methods=['GET','POST'])
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
    
