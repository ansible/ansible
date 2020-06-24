# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: Client Class
#
#   @author: zhang
#   @Date:
#=========================================================================
'''
import json


PRINT_FORMAT = '%-17s%-2s%-20s'


class RedfishClient():
    '''
    请求访问接口封装
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.host = ''
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
        self.host = host
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
                data=None, files=None, timeout=50):
        '''
        if self.type == 'M4':
            if self.port is not None:
                url = r'http://%s:%d/%s' % (self.host, int(self.port), resource)
            else:
                url = r'http://%s/%s' % (self.host, resource)
        else:
        '''
        import requests
        requests.packages.urllib3.disable_warnings()
        if self.restport is not None:
            url = r'https://%s:%d/%s' % (self.host, int(self.restport), resource)
        else:
            url = r'https://%s/%s' % (self.host, resource)
        r = None
        try:
            if method == 'POST':
                if headers is None:
                    data = json.dumps(data)
                    r = requests.post(url=url, headers=None, verify=False, data=data, timeout=50, auth='')
                else:
                    data = json.dumps(data)
                    r = requests.post(url=url, headers=headers, verify=False, data=data, timeout=50, auth='')
            elif method == 'GET':
                data = json.dumps(data)
                r = requests.get(url=url + '?' + data, headers=headers, verify=False)
            elif method == 'DELETE':
                r = requests.delete(url=url, headers=headers, verify=False)
            elif method == 'PATCH':
                data = json.dumps(data)
                r = requests.patch(url=url, headers=headers, verify=False, data=data)
            elif method == 'PUT':
                r = requests.put(url, data=data, headers=headers,
                                 auth=self.auth, verify=False, json=json, timeout=timeout)
            elif method == 'FILE':
                # print('file',headers)
                r = requests.post(url, files=files, headers=headers, verify=False)
            else:
                print('测试')
        except Exception as e:
            # print('Failure: failed to establish connection to the host, please check the user/passcode/host/port')
            # print('usage: utool [-h] [-V] -H <HOST> -U <USERNAME> -P <PASSWORD> -p <PORT> subcommand ...')
            return r
        return r
        # 以下注释可打印HTTP的所有数据
        # print(r._content)
        # if r.status_code == 200:
        #     return r
        # elif r.status_code==405:
        #     return r
        # elif r.status_code==401:
        #     return r
        # else:
        #     print("HTTP Error"+str(r.status_code))
        #     print(type(r))
        #     print(r.status_code)
        #     print(r.headers)
        #     print(r.url)
        #     print(r.request.headers)
        #     print(r.request.body)
        #     return None
