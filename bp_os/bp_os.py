from flask import Blueprint, render_template, current_app, request, flash
import os
import config

bp_os = Blueprint('bp_os', __name__)



#---------------------------------------------------------------------------------------
#The page to turn off the PC
@bp_os.route('/OS', methods=['GET','POST'])
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
@bp_os.route('/logs', methods=['GET','POST'])
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
    

