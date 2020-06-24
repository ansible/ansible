# -*- coding:utf-8 -*-
from ansible.plugins.inspur_sdk.command import IpmiFunc
import json
import sys
import os
import re
import time
from os import path
import platform
from ansible.plugins.inspur_sdk.util import RequestClient
# cur_path = os.path.split(os.path.realpath(__file__))[0]
# path.insert(1, cur_path  + '/command')
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "command"))

# 利用IPMI fru命令验证远程主机的机型
#


class HostTypeClient():

    def __init__(self):
        self.productName = ""
        self.firmwareVersion = ""

    # 从命令行参数利用IPMI fru命令验证远程主机的机型
    def getProductNameByIPMI(self, args):
        host, username, passcode, port = self.getParam(args)
        if (host is None) or (username is None) or (passcode is None):
            # 默认M5登陆***************************
            if '-V' in args or '-h' in args or '-v' in args:
                return
            # *************************************
            result = {"State": "Failure",
                      "Message": ["Parameter is missing,please check -H <HOST> -U <USERNAME> -P <PASSWORD>"]}
            return result
        else:
            client = RequestClient.RequestClient()
            client.setself(host, username, passcode, port, "lanplus")
            productName = IpmiFunc.getProductNameByIpmi(client)
            firmwareVersion = IpmiFunc.getFirmwareVersoinByIpmi(client)
            return productName, firmwareVersion

    # 从命令行参数利用IPMI fru命令验证远程主机的机型
    # 返回 机型、host、username、password
    # raw 0x3c 0x42 获取型号不通用，仅在Korea定制化使用。5288返回5280

    def getHostInfoByRaw(self, args):
        sysstr = platform.system()
        if sysstr == 'Windows':
            cmd = "..\\tools\\ipmitool\\ipmitool.exe -I lanplus -H " + args.host + " -U " + args.username + " -P " + args.password + " raw 0x3c 0x42 2>nul"
        elif sysstr == 'Linux':
            cmd = "ipmitool -I lanplus -H " + args.host + " -U " + args.username + " -P " + args.password + " raw 0x3c 0x42" + " 2>/dev/null"
        result = self.execCmd(cmd).strip()
        if len(result) == 0:
            userInfo = self.getUserInfo(args)
            if userInfo == "":
                return userInfo(args)
            else:
                return [userInfo]
        arr = result.split(" ")
        PN = ""
        for i in range(8):
            PN = PN + chr(int(arr[i], 16))
        #print PN
        if PN == "NF5280M5":
            if sysstr == 'Windows':
                cmdb = "..\\tools\\ipmitool\\ipmitool.exe -I lanplus -H " + args.host + " -U " + args.username + " -P " + args.password + " mc info|findstr /c:\"Firmware Revision\" 2>nul"
            elif sysstr == 'Linux':
                cmdb = "ipmitool -I lanplus -H " + args.host + " -U " + args.username + " -P " + args.password + " mc info |grep 'Firmware Revision'" + " 2>/dev/null"
            resultb = self.execCmd(cmdb).strip()
            #print (resultb)
            if "1." in resultb:
                PN = "NF5288M5"
        PNL = [PN]
        #print (PNL)
        return PNL

        # 发现getHostInfo无法获取机型
    # 需要判断是
    # 1-M4不支持
    # 2-密码错误
    def getUserInfo(self, args):
        sysstr = platform.system()
        if sysstr == 'Windows':
            cmd = "..\\tools\\ipmitool\\ipmitool.exe -I lanplus -H " + args.host + " -U " + args.username + " -P " + args.password + " user list" + " 2>nul"
        elif sysstr == 'Linux':
            cmd = "ipmitool -I lanplus -H " + args.host + " -U " + args.username + " -P " + args.password + " user list" + " 2>/dev/null"
        result = self.execCmd(cmd).strip()
        if len(result) == 0:
            return "PWError"
        return "M4"
    # 获取参数

    def getParam(self, args):
        # i = 0
        host = args.host
        username = args.username
        passcode = args.passcode
        ipmiport = 623
        return host, username, passcode, ipmiport

    # 执行cmd命令，返回命令行获得的结果
    def execCmd(self, cmd):
        r = os.popen(cmd)
        text = r.read()
        r.close()
        return text

    # 对命令行结果进行解析，返回机型信息
    # result execCmd返回的数据
    # key   获得的某行（“Product Name”）数据的值
    def getFru(self, result, key):
        # print(result)
        par1 = key + r"[\. ]+: ([\w]+)"
        fru = re.findall(par1, result)
        return fru
