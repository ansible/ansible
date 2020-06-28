# -*- coding:utf-8 -*-
import argparse
import os
import sys
import json
import signal
from importlib import import_module
from ansible.plugins.inspur_sdk.command import RestFunc
import time
from ansible.plugins.inspur_sdk.util import configUtil
from ansible.plugins.inspur_sdk.util import parameterConversion
import collections
try:
    from ansible.plugins.inspur_sdk.util import HostTypeJudge
    from ansible.plugins.inspur_sdk.util import RequestClient
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
sys.path.append(os.path.join(sys.path[0], "interface"))
current_time = time.strftime('%Y-%m-%d   %H:%M:%S', time.localtime(time.time()))
__version__ = '1.09'


ERR_dict = {
    'ERR_CODE_CMN_FAIL': 'data acquisition exception',
    'ERR_CODE_PARAM_NULL': 'parameter is null',
    'ERR_CODE_INPUT_ERROR': 'parameter error',
    'ERR_CODE_INTF_FAIL': 'create link exception',
    'ERR_CODE_INTERNAL_ERROR': 'internal error',
    'ERR_CODE_ALLOC_MEM': 'allocated memory exception',
    'ERR_CODE_NETWORK_CONNECT_FAIL': 'network connection failed',
    'ERR_CODE_AUTH_NAME_OR_PWD_ERROR': 'incorrect user name or password',
    'ERR_CODE_USER_NOT_EXIST': 'user not exist'
}


# argsparse 自定义输出格式类
class CustomHelpFormatter(argparse.HelpFormatter):

    def _iter_indented_subactions(self, action):
        self._max_help_position = 30
        self._width = 120
        self._action_max_length = 30

        try:
            get_subactions = action._get_subactions
        except AttributeError:
            # print("AttributeError")
            pass
        else:
            self._indent()
            if isinstance(action, argparse._SubParsersAction):
                for subaction in sorted(get_subactions(), \
                                        key=lambda x: x.dest):
                    yield subaction
            else:
                for subaction in get_subactions():
                    yield subaction
            self._dedent()


def main(params):

    def logout(signum, frame):
        if hasattr(client, "header"):
            RestFunc.logout(client)

    signal.signal(signal.SIGINT, logout)
    signal.signal(signal.SIGTERM, logout)
    signal.signal(signal.SIGABRT, logout)
    # windows下注释下面两行
    signal.signal(signal.SIGHUP, logout)
    signal.signal(signal.SIGQUIT, logout)
    #signal.signal(signal.SIGSTOP, logout)
    #signal.signal(signal.SIGKILL, logout)
    res = {}
    if not HAS_REQUESTS:
        res['State'] = "Failure"
        res['Message'] = ["Please install the requests library"]
        return res
    parser = argparse.ArgumentParser(
        prog='uTool',
        add_help=True,
        formatter_class=CustomHelpFormatter,
        description='uTool version: ' + __version__
    )
    param = parameterConversion.getParam(params)
    args = dict_to_object(param)
    args.hostPlatform = 'M5'
    args.port = None
    # 使用fru获取机型信息
    hostTypeClient = HostTypeJudge.HostTypeClient()
    productName, firmwareVersion = hostTypeClient.getProductNameByIPMI(args)
    if productName is None:
        res['State'] = "Not Support"
        res['Message'] = ["cannot get productName", productName, firmwareVersion]
        print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=True))
        return res
    elif productName in ERR_dict:
        res['State'] = "Failure"
        res['Message'] = [ERR_dict.get(productName)]
        print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=True))
        return res
    if firmwareVersion is None:
        res['State'] = "Failure"
        res['Message'] = ["cannot get BMC version"]
        print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=True))
        return
    configutil = configUtil.configUtil()
    impl = configutil.getRouteOption(productName, firmwareVersion)
    if 'Error' in impl:
        res['State'] = "Failure"
        res['Message'] = [impl]
        print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=True))
        return res
    if 'M5' not in impl and 'T6' not in impl:
        res['State'] = "Failure"
        res['Message'] = ['Not Support']
        print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=True))
        return res
    module_impl = 'ansible.plugins.inspur_sdk.interface.' + impl
    obj = import_module(module_impl)
    targetclass = getattr(obj, impl)
    obj = targetclass()
    if args.subcommand is None:
        res['State'] = "Failure"
        res['Message'] = ["please input a subcommand"]
        print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=True))
        return res
    targetMed = getattr(obj, args.subcommand)
    client = RequestClient.RequestClient()
    client.setself(args.host, args.username, args.passcode, args.port, 'lanplus')
    try:
        resultJson = targetMed(client, args)
    except KeyError as k:
        res['State'] = "Not Support"
        res['Message'] = ["Unable to parse keywords '" + str(k) + "', this server may not be supported."]
        print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=True))
        return res
    except Exception as e:
        # 保留日志
        import traceback
        utool_path = os.path.dirname(os.path.abspath(__file__))
        # print(utool_path)
        log_path = os.path.join(utool_path, "log")
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        # TIME
        localtime = time.localtime()
        f_localdate = time.strftime("%Y-%m-%d", localtime)
        f_localtime = time.strftime("%Y-%m-%dT%H:%M:%S ", localtime)

        log_file = os.path.join(log_path, f_localdate)
        res_info = "[" + args.subcommand + "]" + traceback.format_exc()
        with open(log_file, 'a+') as logfile:
            utoollog = "[ERROR]" + f_localtime + res_info
            logfile.write(utoollog)
            logfile.write("\n")

        res['State'] = "Failure"
        res['Message'] = ["Error occurs, request failed..."]
        # res['log_file'] = [log_file]
        print(json.dumps(res, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=True))
        return res
    # 打印state在前面
    sortedRes = collections.OrderedDict()
    # sortedRes["proposed"] = params
    sortedRes["State"] = resultJson.State
    sortedRes["Message"] = resultJson.Message
    # print(json.dumps(sortedRes, default=lambda o: o.__dict__, indent=4, ensure_ascii=True))
    return sortedRes


class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__


def dict_to_object(dictobj):
    if not isinstance(dictobj, dict):
        return dictobj
    inst = Dict()
    for k, v in dictobj.items():
        if k == 'password':
            k = 'passcode'
        inst[k] = dict_to_object(v)
    return inst

# 程序入口


if __name__ == "__main__":
    main()
