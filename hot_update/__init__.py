#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# @Project ：cpos-df
# @File    ：aa.py
# @IDE     ：PyCharm
# @Author  ：xu.lai
# @Date    ：2022/11/23 10:31

"""
代码热更
"""

import importlib
import threading
import time
import os
import traceback

from types import FunctionType, MethodType
from enum import IntEnum
import tools.log as _logger

root_name = os.getcwd()
update_file_name = root_name + "\\hot_update\\update_file.txt"  # 操作文件路径
update_file_log = root_name + "\\hot_update\\update_log.txt"  # 日志文件路径



def start():
    CUpdate().start()
    _logger.error("init hot update")


def get_now_time():
    time_struct = time.localtime(time.time())
    return time.strftime('%Y-%m-%d %H:%M:%S', time_struct)


class CUpdate(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.update_file_io = open(update_file_name, "a+", encoding='utf-8')
        self.update_file_log = open(update_file_log, "a+", encoding='utf-8')
        self.pre_file_update_time = int(os.path.getmtime(update_file_name))
        self.is_print_test_log = False

    def run(self):
        while True:
            time.sleep(1)
            if not self.check_is_update_file():
                continue
            try:
                self.do_update()
            except Exception as err:
                self.log("run 运行错误 %s \n%s" % (err,
                                               traceback.format_exc()))

    def check_is_update_file(self):
        """ 检擦文件是否有改动，有改动才更新 """
        now_update_time = int(os.path.getmtime(update_file_name))
        if self.pre_file_update_time >= now_update_time:
            return False
        self.pre_file_update_time = now_update_time
        return True

    def do_update(self):
        """ 读取文件并更新 """
        if not self.update_file_io:
            return
        self.update_file_io.seek(0, 0)
        line = self.update_file_io.readline()

        for _ in range(10):
            if "#" not in line:
                break
            if "?" in line:
                self.is_print_test_log = True
            line = self.update_file_io.readline()
        if not line:
            return

        line_slip_list = line.split(",")
        for mod in line_slip_list:
            try:
                self.update_mod(mod)
            except Exception as err:
                self.log("update 运行错误 %s: %s \n%s" % (mod, err,
                                                      traceback.format_exc()))
        self.is_print_test_log = False

    def log(self, msg):
        if "test" in msg and not self.is_print_test_log:
            return
        self.update_file_log.seek(0, 2)
        self.update_file_log.write(msg + "\n")
        self.update_file_log.flush()

    def update_mod(self, mod):
        """ 更新mod模块 """
        if not mod:
            return
        name = mod.replace(" ", "").replace("\n", "")
        message = "%s 更新文件: %s" % (get_now_time(), str(name))
        if "__init__" in name:
            old_model = __import__(name)
        else:
            old_model = importlib.import_module(name)
        old_model_data = {}
        attr_list = dir(old_model)
        for attr_name in attr_list:
            old_model_data[attr_name] = getattr(old_model, attr_name)
        self.log("[test]pre mode: %s %s %s" % (name, old_model, id(old_model)))

        importlib.reload(old_model)
        # 说明: 为什么__init__.py文件只能使用__import__的方式？
        # 因为 __init__.py 模块比较特殊，python将这个文件作为一个目录的默认文件，代表一个目录
        # 而importlib.import_module只是非常单纯的加载一个__init__.py
        # 所以两种方式加载__init__.py 会是两个完全独立的命名空间
        # 又因为系统是使用 __import__ 加载 __init__.py
        # 所以这里要替换__init__.py 的旧函数，只能使用 __import__ 加载
        if "__init__" in name:
            new_model = __import__(name)
        else:
            new_model = importlib.import_module(name)
        self.log(
            "[test]after mode: %s %s %s" % (name, new_model, id(new_model)))

        for attr_name in dir(new_model):
            if attr_name not in old_model_data:
                continue
            # 不用更新模块级函数及属性
            if self.check_mod_attr_type(old_model_data[attr_name]):
                self.log("[test]update no %s new:%s old:%s" % (
                    old_model_data[attr_name],
                    id(getattr(new_model, attr_name)),
                    id(old_model_data[attr_name])))
                continue
            if isinstance(old_model_data[attr_name], type):
                self.replace_class_func(getattr(new_model, attr_name),
                                        old_model_data[attr_name])
                self.log("[test]update replace %s new:%s old:%s" % (
                    old_model_data[attr_name],
                    id(getattr(new_model, attr_name)),
                    id(old_model_data[attr_name])))
                # 模块属性指向旧模块
                setattr(new_model, attr_name, old_model_data[attr_name])
            else:
                self.log("[test]update pre %s new:%s old:%s" % (
                    old_model_data[attr_name],
                    id(getattr(new_model, attr_name)),
                    id(old_model_data[attr_name])))
                setattr(new_model, attr_name, old_model_data[attr_name])
                self.log("[test]update %s after %s new:%s old:%s" % (
                    attr_name,
                    old_model_data[attr_name],
                    id(getattr(new_model, attr_name)),
                    id(old_model_data[attr_name])))
        message += "  ok"
        self.log(message)

    def replace_class_func(self, new_class, old_class):
        """ 替换类属性，指向新值 """
        for attr_name in dir(new_class):
            if self.ban_update_func(attr_name):
                self.log("[test]ban1 %s %s" % (
                    getattr(old_class, "__name__", "No-class_name"),
                    attr_name,
                ))
                continue
            attr = getattr(new_class, attr_name)
            if not self.check_class_attr_type(attr):
                self.log("[test]ban2 %s %s id:%s %s" % (
                    getattr(old_class, "__name__", "No-class_name"),
                    attr_name, id(getattr(old_class, attr_name, None)),
                    id(attr)
                ))
                continue
            self.log("[test]func class:%s attr:%s old:%s new:%s" % (
                getattr(old_class, "__name__", "No-class_name"),
                attr, id(getattr(old_class, attr_name, None)), id(attr)))
            # 类属性指向新属性
            try:
                setattr(old_class, attr_name, attr)
            except Exception as err:
                self.log("[err set attr]%s: %s %s %s" % (err, old_class, attr_name, attr))

    @classmethod
    def ban_update_func(cls, attr_name: str) -> bool:
        """ 禁止更新的内部函数 """
        if attr_name == "__init__":
            return False
        if attr_name.startswith("__") or attr_name.endswith("__"):
            return True
        return False

    @classmethod
    def check_mod_attr_type(cls, attr):
        """ 更新模块的属性类型 """
        if isinstance(attr, FunctionType):
            return True
        if isinstance(attr, int):
            return True
        if isinstance(attr, float):
            return True
        if isinstance(attr, str):
            return True
        return False

    @classmethod
    def check_class_attr_type(cls, attr):
        """ 更新类的属性类型 """
        if isinstance(attr, IntEnum):
            return False

        if isinstance(attr, MethodType):  # 类方法
            return True
        if isinstance(attr, FunctionType):  # 属性方法
            return True
        if isinstance(attr, int):
            return True
        if isinstance(attr, float):
            return True
        if isinstance(attr, str):
            return True
        if isinstance(attr, list):
            return True
        if isinstance(attr, dict):
            return True
        return False
