from flask import jsonify
from flask import send_from_directory
import tools.log as log
import requests

tradplusSDKListUrl = 'https://docs.tradplusad.com/api/sdk/list'
tradplusConfigUrl = 'https://docs.tradplusad.com/api/sdk/config'
tradplusDependsUrl = 'https://docs.tradplusad.com/api/sdk/package'
adsChannel = ['UnityAds']

sdkmapping = {}
adsmapping = {}
addCrossAndAdx = []
region = '2' # 1: 中国  2: 其它地区

# 829 : 叁一
valid_codes = [ '829' ]  

eromsg = ''

def logInfo( msg ):
    global eromsg
    log.debug(msg)
    eromsg += f'{msg}\n'

def InitSDKMapping():
    data = {
        'os': '0'
    }
    r = requests.post(tradplusSDKListUrl, data=data)
    j = r.json()

    data = j['data']
    if None == data:
        logInfo("数据解析异常 未知data")
        return

    androidXSDKlist = data['androidVersions']
    if None == androidXSDKlist:
        logInfo("AndroidX SDK获取失败")
        return

    for sdk in androidXSDKlist:
        sdkmapping[sdk['version']] = sdk['sdkId']

def InitConfig( sdk_version = "10.2.0.1"):
    if sdk_version not in sdkmapping.keys():
        logInfo(f"unknow version: {sdk_version}")
        return
    
    data = {
        'os': '1',
        'sdkId':sdkmapping[sdk_version]
    }
    r = requests.post(tradplusConfigUrl, data=data)
    j = r.json()
    if 'data' not in j:
        logInfo('Get config fail')
        return
    d = j['data']
    if 'networks' not in d:
        logInfo('Get networks fail')
        return
    networks = d['networks']
    addCrossAndAdx.clear()
    for network in networks:
        adsmapping[network['nameEn']]=network['networkId']

        if network['isAddCrossAndAdx'] == '1' and network['region'] == region:
            addCrossAndAdx.append(network['networkId'])

def GetDependencies( sdk_version = "10.2.0.1" ):
    if len(adsChannel) == 0:
        logInfo('ads platform count must greater than 0')
        return
    
    if sdk_version not in sdkmapping.keys():
        logInfo(f"unknow version: {sdk_version}")
        return
    
    if len(adsmapping.keys()) == 0:
        logInfo(f"adsmapping init fail")
        return

    ads = []
    for channel in adsChannel:
        if channel in adsmapping.keys():
            ads.append(adsmapping[channel])
        else:
            logInfo(f'channel absence: {channel}')
    
    logInfo(','.join(adsChannel))

    ads.extend(addCrossAndAdx)
    data = {
        'os': '1',
        'sdkId':sdkmapping[sdk_version],
        'isUnity':'0',
        'isNogradle':'0',
    }
    for i in range( len(ads) ):
        data[f'networkIds[{i}]'] = ads[i]

    r = requests.post(tradplusDependsUrl, data=data)
    j = r.json()
    if 'data' not in j:
        logInfo('fail dependen')
        return
    data = j['data']
    if 'appGradleCode' not in data:
        logInfo('not found apps build.gradle')
        return
    return data['appGradleCode']


def Run(  sdk_version = "10.2.0.1" ):
    InitSDKMapping()
    InitConfig(sdk_version)
    appGradleCode = GetDependencies(sdk_version)
    if None == appGradleCode:
        return jsonify({
        "code": 2001,
        "err": eromsg
        } )
    return jsonify({
        "code": 200,
        "data": appGradleCode
        } )

def apply(msg: dict):
    global adsChannel,region,eromsg,valid_codes
    eromsg = ''
    if 'adchannels' in msg.keys():
        req_code = msg['code']
        if req_code not in valid_codes:
            return jsonify({
                "code": 201,
                "err": f"tradplus has been updated. :{req_code}",
                'debug': len(valid_codes)
            })
        adsChannel = msg['adchannels']
        sdk_version = msg['version']
        region = msg['region']
        return Run(sdk_version)

    return jsonify({
        "code": 404,
        "err": "channels ero."
    })

