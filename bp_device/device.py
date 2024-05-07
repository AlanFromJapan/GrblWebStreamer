from flask import Blueprint, render_template, request, flash, current_app

import device
import serialUtils

bp_device = Blueprint('bp_device', __name__)

#---------------------------------------------------------------------------------------
#The page to play with the device
@bp_device.route('/device', methods=['GET','POST'])
def device_page():    
    latest_file = current_app.latest_file
    D = current_app.D
    
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
