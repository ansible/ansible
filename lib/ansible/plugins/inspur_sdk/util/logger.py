# -*- coding:utf-8 -*-
import logging
from logging import handlers
import os
import sys
import time


class Logger(object):
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }


def myLogger(file_new):
    loggers = logging.getLogger("utool")
    format_str = logging.Formatter(
        '[%(levelname)s] %(asctime)s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S')
    th = handlers.TimedRotatingFileHandler(
        filename=file_new,
        when='D',
        interval=1,
        backupCount=5,
        encoding='utf-8'
    )
    th.setFormatter(format_str)
    # 防止多次import logger时添加多个handlers 打印多次日志
    if loggers.handlers == []:
        loggers.addHandler(th)
    loggers.setLevel(logging.DEBUG)
    return loggers


localtime = time.localtime()
log_name = time.strftime("%Y-%m-%d", localtime)

log_path = os.path.join(
    os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "log")
if not os.path.exists(log_path):
    os.makedirs(log_path)
    time.sleep(5)

log_file = os.path.join(log_path, log_name)


utoolLog = myLogger(log_file)
