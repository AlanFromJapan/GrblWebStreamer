from flask import Blueprint, current_app


bp_api = Blueprint('bp_api', __name__)


#---------------------------------------------------------------------------------------
#Returns current status (Webservice - NOT A PAGE)
@bp_api.route('/status')
def status_ws():
    stat = f"{{ \"status\": \"{current_app.D.status.name}\", \"port\": \"{current_app.D.port}\" }}"
    return stat
