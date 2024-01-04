import time
import logging
import logging.handlers
import os
import traceback

__inited = False
__logger = None
__handler = None


def __init():
    global __logger, __handler
    logging.basicConfig()
    __logger = logging.getLogger("script")
    __logger.setLevel(logging.DEBUG)
    __handler = {
        'DEBUG': lambda x: __logger.debug(x),
        'INFO': lambda x: __logger.info(x),
        'WARNING': lambda x: __logger.warning(x),
        'ERROR': lambda x: __logger.error(x)
    }

    log_dir = os.path.join(os.getcwd(), 'log')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    # 输出到本地
    timefilehandler = logging.handlers.TimedRotatingFileHandler(
        "log/log.log",  # 日志路径
        when='D',      # S秒 M分 H时 D天 W周 按时间切割 测试选用S
        interval=1,    # 多少天切割一次
        backupCount=30  # 保留多少天
    )
    formatter = logging.Formatter(
        '%(message)s')
    timefilehandler.suffix = '%Y-%m-%d'
    timefilehandler.setFormatter(formatter)

    # 添加到句柄
    __logger.addHandler(timefilehandler)


def __getTimeString():
    now = int(time.time())
    timeArray = time.localtime(now)
    return time.strftime("%H:%M:%S", timeArray)


def __log(msg, level):
    global __inited
    if not __inited:
        __init()
        __inited = True

    msg = f"{__getTimeString()} {level}:{msg}"
    __handler[level](msg)


def debug(msg):
    __log(msg, 'DEBUG')


############## 日志接口太多 将毫无意义 ###############

# def info(msg):
#     __log(msg, 'INFO')

# def warning(msg):
#     __log(msg, 'WARNING')

####################################################


def error(msg):
    __log(msg, 'ERROR')


def print_exc():
    __log(traceback.format_exc(), 'ERROR')


def print_stack():
    __log(traceback.format_stack(), 'DEBUG')


def print_exception():
    __log(traceback.format_exception(), 'ERROR')
