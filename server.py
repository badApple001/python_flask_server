import datetime
from flask import Flask
from flask import request, jsonify
from channel import channel_manager
from apscheduler.schedulers.blocking import BlockingScheduler
import hot_update
import time

app = Flask(__name__)
request_history = {}  #请求历史信息 包含ip 最后一次请求时间戳 频繁请求计数 违规次数
blacklist = [] #黑名单 通知一次玩家已经是在黑名单了
locklist = []  #锁定列表 返回空字符串

def request_parse(req_data):
    if req_data.method == 'POST':
        data = req_data.json
    elif req_data.method == 'GET':
        data = req_data.args
    return data


@app.route('/hello')
def hello_world():
    return 'Hello World!'


@app.route('/callApi')
def callApi():
    ip = request.remote_addr

    # 锁定ip列表
    if ip in locklist:
        return ""

    # 黑名端 会通知一次客户端
    if ip in blacklist:
        locklist.append(ip)
        return jsonify({
                    "code": 201,
                    "err": "You are currently blacklisted."
                })

    # 1秒内请求限制5次
    if ip not in request_history.keys():
        request_history[ip] = [time.time(), 1, 0 ]  # 最近call的时间, 短时间内调用的次数, 频繁计数
    else:
        if time.time() - request_history[ip][0] < 1:
            request_history[ip][1] += 1
           
            # 频繁请求 违规处理
            if request_history[ip][1] >= 5:
                
                #违规次数统计
                request_history[ip][2] += 1
                if request_history[ip][2] >= 64:
                    blacklist.append(ip) #加入黑名端
                
                return jsonify({
                    "code": 201,
                    "err": "Requesting too often."
                })
        else:
            request_history[ip][1] = 1
        request_history[ip][0] = time.time()

    # 主逻辑
    data = request_parse(request)
    try:
        # 验证token
        token = data.get('token')

        # 验证不通过 返回错误代码
        if not token:
            return jsonify({
                "code": 401,
                "err": "error token."
            })

        # 获取处理的管线
        channel = data.get('channel')
        if not channel:
            return jsonify({
                "code": 401,
                "err": "not contains channel."
            })

        # 派遣任务
        res = channel_manager.dispatch(data)
        if None != res:
            return res

        # 未找到对应的管线
        return jsonify({
            "code": 404,
            "err": "channel not found."
        })

    # 异常反馈
    except Exception as e:
        return jsonify({
            "code": 412,
            "err": str(e)
        })


def openserver():
    print('服务器启动中.....')
    app.run(host="0.0.0.0", port=8091, ssl_context=(
        './certificate/www.geek7.top.crt', './certificate/www.geek7.top.key'))


def dojob():
    # 创建调度器：BlockingScheduler
    scheduler = BlockingScheduler()
    # 添加任务,1分钟更新15次
    scheduler.add_job(channel_manager.update, 'interval',
                      seconds=60/15, id='main_thread_tick')
    # 延时一秒执行一次
    scheduler.add_job(openserver, 'date', run_date=datetime.datetime.now(
    )+datetime.timedelta(seconds=1))
    scheduler.start()


if __name__ == '__main__':
    hot_update.start()
    dojob()
