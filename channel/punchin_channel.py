from flask import jsonify
from flask import send_from_directory
import os
import tools.log as log

off_duty = '0'

def apply(msg: dict):
    global off_duty

    api = msg.get('api')
    if not api:
        return jsonify({
            "code": 400,
            "err": "You must specify the api."
        })
    
    if api == 'get_status':
        return off_duty
    
    elif api == 'set_status':
        off_duty = str(msg.get('new_status'))
        log.debug(f'set status: {off_duty}')
        return jsonify({
            "code": 200
        })

    return jsonify({
            "code": 404,
            "err": "undefine api."
        })