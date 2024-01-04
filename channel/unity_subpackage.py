from flask import jsonify
from flask import send_from_directory
import os


def apply(msg: dict):
    api = msg.get('api')
    if not api:
        return jsonify({
            "code": 400,
            "err": "You must specify the api."
        })
    if api == 'get_app_version':
        # 返回最新版本号
        return jsonify({
            "code": 200,
            "content": getNewVersion()
        })
    elif api == 'upgrade':
        # 升级应用
        try:
            version = msg.get('version')
            version_path = f'./bin/unity_subpackage/{version}'
            if os.path.exists(version_path):
                return send_from_directory(version_path, 'main.exe')
            else:
                return jsonify({
                    "code": 404,
                    "err": "version not found."
                })
        except Exception as e:
            return str(e)
    else:
        return jsonify({
            "code": 404,
            "err": "undefine api."
        })

def getVersionCode(v: str):
    return int(v.replace('.', ''))


def getNewVersion():
    version_dirs = os.listdir(os.path.join(
        os.getcwd(), 'bin/unity_subpackage/'))
    maxVersionCode = 0
    maxVersion = ""
    for version in version_dirs:
        versionCode = getVersionCode(version)
        if versionCode > maxVersionCode:
            maxVersionCode = versionCode
            maxVersion = version
    return maxVersion
