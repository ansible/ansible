# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: Client Class
#
#   @author:
#   @Date:
#=========================================================================
'''
import re
from ansible.plugins.inspur_sdk.util import logger
import json
import sys
import time
import os
import requests
sys.path.append(os.path.dirname(sys.path[0]))


PRINT_FORMAT = '%-17s%-2s%-20s'


class RequestClient():
    '''
    请求访问接口封装
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.host = ''
        self.resthost = ''
        self.username = ''
        self.passcode = ''
        self.port = ''
        self.restport = 443
        self.lantype = ''

        self.token = ''
        self.etag = ''
        self.headerhost = None
        self.auth = None

    def setself(self, host, username, password, port=623, lantype="lanplus"):
        '''
        #=====================================================================
        #   @Method:  设置带内hos，port,username,password值
        #   @Param:
        #   @Return:
        #   @author:
        #=====================================================================
        '''

        p = '^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}' \
            '|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))' \
            '|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d' \
            '|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})' \
            '|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))' \
            '|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d' \
            '|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})' \
            '|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))' \
            '|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d' \
            '|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})' \
            '|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))' \
            r'|:)))(%.+)?\s*$'
        if re.search(p, host, re.I):
            resthost = '[' + host + ']'
        else:
            resthost = host
        self.host = host
        self.resthost = resthost
        self.username = username
        self.passcode = password
        if port is None:
            self.port = 623
        else:
            self.port = port
        if lantype is None:
            self.lantype = 'lanplus'
        else:
            self.lantype = lantype

    def setHearder(self, header):
        self.header = header

    def getHearder(self):
        return self.header

    # 请求一个URI资源
    # method  POST GET DELETE PATCH PUT
    # resource uri
    # headers HTTP头
    # stream None
    # data python字典数据，转化为Http写入Body中，a=1&b=2转化为urlEncode格式
    # json python字典数据，转化为Http写入Body中，{'a':1,'b':2}转化为Josn格式
    # files 上传文件
    # timeout 请求过期时间

    def request(self, method, resource, headers=None, stream=None,
                data=None, files=None, json=None, timeout=80):
        '''
        if self.type == 'M4':
            if self.port is not None:
                url = r'http://%s:%d/%s' % (self.host, int(self.port), resource)
            else:
                url = r'http://%s/%s' % (self.host, resource)
        else:
        '''
        if self.restport is not None:
            url = r'https://%s:%d/%s' % (self.resthost, int(self.restport), resource)
        else:
            url = r'https://%s/%s' % (self.resthost, resource)
        # print(url)
        r = None
        requests.packages.urllib3.disable_warnings()
        try:
            if method == 'POST':
                # print("post")
                # print(json)
                r = requests.post(url, data=data, files=files, headers=headers, json=json, auth=self.auth, verify=False, timeout=timeout)
            elif method == 'GET':
                r = requests.get(url, data=data, headers=headers,
                                 auth=self.auth, verify=False, timeout=timeout)
            elif method == 'DELETE':
                r = requests.delete(url, data=data, headers=headers,
                                    auth=self.auth, verify=False, json=json, timeout=timeout)
            elif method == 'PATCH':
                r = requests.patch(url, data=data, headers=headers,
                                   auth=self.auth, verify=False, json=json, timeout=timeout)
            elif method == 'PUT':
                r = requests.put(url, data=data, headers=headers,
                                 auth=self.auth, verify=False, json=json, timeout=timeout)
            elif method == 'FILE':
                # print('file',headers)
                r = requests.post(url, files=files, headers=headers, verify=False)
            else:
                r = requests.models.Response()
                r.status_code = 1500
                str_error = '{"code":1500,"error":"Method error，choose from POST/GET/DELETE/PATCH/PUT/FILE"}'
                r._content = str_error.encode()
        except Exception as e:
            logger.utoolLog.error("An exception occurred while calling the rest interface", exc_info=True)
            if "ConnectionRefusedError" in str(e):
                r = requests.models.Response()
                r.status_code = 1500
                str_error = '{"code":1500,"error":"BMC web service is not ready, please wait for about 1 minute"}'
                r._content = str_error.encode()
            else:
                # 异常返回
                r = requests.models.Response()
                r.status_code = 1500
                str_error = '{"code":1500,"error":"' + str(e) + '"}'
                r._content = str_error.encode()

        # log
        res_info = "[" + method + "] " + url + ":"
        if method == 'PUT' or method == 'POST':
            if data is not None:
                if isinstance(data, dict):
                    if "password" in data:
                        data["password"] = "-"
                    res_info = res_info + " [DATA] " + str(data)
                else:
                    res_info = res_info + " [DATA] " + str(type(data))
            if json is not None:
                res_info = res_info + " [JSON] " + str(json)
        if r is None:
            logger.utoolLog.critical(res_info + "error occurred, response is None")
        elif r.status_code == 200:
            try:
                res_info = res_info + " [RES] " + str(r.json())
            except BaseException:
                res_info = res_info
            logger.utoolLog.info(res_info)
        else:
            try:
                res_info = res_info + " [RES] " + str(r.json())
            except BaseException:
                res_info = res_info
            logger.utoolLog.error(res_info)
        return r

