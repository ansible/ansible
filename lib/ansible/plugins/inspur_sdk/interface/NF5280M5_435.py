# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: base Class
#
#   @author: zhang
#   @Date:
#=========================================================================
'''
from ansible.plugins.inspur_sdk.interface.Base import hexReverse
from ansible.plugins.inspur_sdk.interface.Base import ascii2hex
from ansible.plugins.inspur_sdk.interface.NF5280M5 import NF5280M5
from ansible.plugins.inspur_sdk.command import IpmiFunc
from ansible.plugins.inspur_sdk.command import RestFunc
from ansible.plugins.inspur_sdk.interface.ResEntity import *
import os
import re


class NF5280M5_435(NF5280M5):

    def getcapabilities(self, client, args):
        res = ResultBean()
        cap = CapabilitiesBean()
        getcomand = ['getadaptiveport', 'getbios', 'getcapabilities', 'getcpu', 'geteventlog', 'getfan', 'getfru', 'getfw', 'gethealth', 'getip', 'getnic', 'getpcie', 'getpdisk', 'getpower', 'getproduct', 'getpsu', 'getsensor', 'getservice', 'getsysboot', 'gettemp', 'gettime', 'gettrap', 'getuser', 'getvolt', 'getraid', 'getmemory', 'getldisk', 'getfirewall', 'gethealthevent', 'getvnc', 'getvncsession']
        getcomand_not_support = ['getbiossetting', 'getbiosresult', 'geteventsub', 'getpwrcap', 'getmgmtport', 'getupdatestate', 'getserialport', 'gettaskstate', 'getbiosdebug', 'getthreshold', 'get80port']
        setcommand = ['adduser', 'clearsel', 'collect', 'deluser', 'fancontrol', 'fwupdate', 'locatedisk', 'locateserver', 'mountvmm', 'powercontrol', 'resetbmc', 'restorebmc', 'sendipmirawcmd', 'settimezone', 'settrapcom', 'setbios', 'setip', 'setpriv', 'setpwd', 'setservice', 'setsysboot', 'settrapdest', 'setvlan', 'setbiospwd', 'setvnc', 'settime', 'clearbiospwd', 'restorebios', 'delvncsession', 'setproductserial', 'exportbmccfg', 'exportbioscfg', 'importbioscfg', 'importbmccfg', 'setfirewall', 'addwhitelist', 'delwhitelist']
        setcommand_ns = ['sethsc', 'setimageurl', 'setadaptiveport', 'setserialport', 'powerctrldisk', 'recoverypsu', 'downloadtfalog', 'setthreshold', 'downloadsol', 'canceltask', 'setbiosdebug']
        cap.GetCommandList(getcomand)
        cap.SetCommandList(setcommand)
        res.State('Success')
        res.Message(cap.dict)
        return res

    def exportbioscfg(self, client, args):
        '''
        export bios setup configuration
        :param client:
        :param args:
        :return:
        '''
        export = ResultBean()

        file_path = os.path.dirname(args.fileurl)
        file_name = os.path.basename(args.fileurl)

        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
            except BaseException:
                export.State("Failure")
                export.Message(["cannot build path."])
                return export
        if '.json' not in file_name and '.conf' not in file_name:
            export.State("Failure")
            export.Message(["please input filename with suffix .json/.conf."])
            return export
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.exportTwoBiosCfgByRest(client, args.fileurl, file_name)

        if res == {}:
            export.State("Failure")
            export.Message(["export bios setup configuration file failed."])
        elif res.get('code') == 0:
            export.State('Success')
            export.Message([res.get('data')])
        elif res.get('code') == 4:
            export.State('Failure')
            export.Message([res.get('data')])
        else:
            export.State("Failure")
            export.Message(["export bios setup configuration file error, " + res.get('data')])
        # logout
        RestFunc.logout(client)
        return export

    def importbioscfg(self, client, args):
        '''
        import bios cfg
        :param client:
        :param args:
        :return:
        '''
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # get
        res = RestFunc.importTwoBiosCfgByRest(client, args.fileurl)
        import_Info = ResultBean()
        if res == {}:
            import_Info.State("Failure")
            import_Info.Message(["import bios setup configuration file failed."])
        elif res.get('code') == 0:
            import_Info.State('Success')
            import_Info.Message(['import bios setup configuration file success.'])
        else:
            import_Info.State("Failure")
            import_Info.Message(["import bios setup configuration failed, " + str(res.get('data'))])
        # logout
        RestFunc.logout(client)
        return import_Info

    def exportbmccfg(self, client, args):
        checkparam_res = ResultBean()
        # check param

        checkparam_res = ResultBean()

        if args.fileurl == ".":
            file_name = "bmcconfig.json"
            file_path = os.path.abspath(".")
        elif args.fileurl == "..":
            file_name = "bmcconfig.json"
            file_path = os.path.abspath("..")
        elif re.search(r"^[C-Zc-z]\:$", args.fileurl, re.I):
            file_name = "bmcconfig.json"
            file_path = os.path.abspath(args.fileurl + "\\")
        else:
            file_name = os.path.basename(args.fileurl)
            file_path = os.path.dirname(args.fileurl)

            if file_name == "":
                file_name = "bmcconfig.json"
            if file_path == "":
                file_path = os.path.abspath(".")

        args.fileurl = os.path.join(file_path, file_name)

        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
            except BaseException:
                checkparam_res.State("Failure")
                checkparam_res.Message(["cannot build path."])
                return checkparam_res
        else:
            filename_0 = os.path.splitext(file_name)[0]
            filename_1 = os.path.splitext(file_name)[1]
            if os.path.exists(args.fileurl):
                name_id = 1
                name_new = filename_0 + "(1)" + filename_1
                file_new = os.path.join(file_path, name_new)
                while os.path.exists(file_new):
                    name_id = name_id + 1
                    name_new = filename_0 + "(" + str(name_id) + ")" + filename_1
                    file_new = os.path.join(file_path, name_new)
                args.fileurl = file_new

        # check param end
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # 查看进度 要是正好有人再导出 则直接导出该份文档
        # 否则才自己生成
        res = RestFunc.getBMCProgressByRest(client)
        bmcres = ResultBean()
        if res == {}:
            bmcres.State("Failure")
            bmcres.Message(["cannot get bmc cfg export express"])
        elif res.get('code') == 0 and res.get('data') is not None:
            data = res.get('data')
            if "filePath" in data and "state" in data:
                fp = data["filePath"]
                jj = os.path.splitext(fp)[1]

                if data["state"] == 0 and jj == ".json":
                    state = 0
                    count = 0
                    while state == 0:
                        if count > 60:
                            bmcres.State("Failure")
                            bmcres.Message(["generate log time out"])
                            break
                        count = count + 1
                        import time
                        time.sleep(5)
                        # 循环查找直到完成
                        process_res = RestFunc.getBMCProgressByRest(client)
                        #print (process_res)
                        if process_res == {}:
                            bmcres.State("Failure")
                            bmcres.Message(["get BMC cfg export progress error"])
                            break
                        elif process_res.get('code') == 0 and process_res.get('data') is not None:
                            data = process_res.get('data')
                            if "state" in data and data["state"] == 2:
                                state = 2
                                filepathinserver = data["filePath"]
                                filename = filepathinserver.split("/")[-1]
                                # download
                                download_res = RestFunc.downloadBMCcfgByRest(client, args.fileurl, filename)
                                if download_res == {}:
                                    bmcres.State("Failure")
                                    bmcres.Message(["cannot download BMC cfg"])
                                elif download_res.get('code') == 0 and download_res.get('data') is not None:
                                    bmcres.State("Success")
                                    #bmcres.Message(["export BMC cfg success"])
                                    bmcres.Message([download_res.get('data')])
                                elif download_res.get('code') != 0 and download_res.get('data') is not None:
                                    bmcres.State("Failure")
                                    bmcres.Message([download_res.get('data')])
                                else:
                                    bmcres.State("Failure")
                                    bmcres.Message(["download BMC cfg error"])
                                break
                            elif "state" in data and data["state"] == 0:
                                if "100" in data["progress"] or "complete" in data["progress"]:
                                    # download
                                    download_res = RestFunc.downloadBMCcfgByRest(client, args.fileurl, filename)
                                    if download_res == {}:
                                        bmcres.State("Failure")
                                        bmcres.Message(["download BMC cfg error"])
                                    elif download_res.get('code') == 0 and download_res.get('data') is not None:
                                        bmcres.State("Success")
                                        #bmcres.Message(["export BMC cfg success"])
                                        bmcres.Message([download_res.get('data')])
                                    elif download_res.get('code') != 0 and download_res.get('data') is not None:
                                        bmcres.State("Failure")
                                        bmcres.Message([download_res.get('data')])
                                    else:
                                        bmcres.State("Failure")
                                        bmcres.Message(["cannot download BMC cfg"])
                                    break
                            else:
                                bmcres.State("Failure")
                                bmcres.Message(["cannot get export progress"])
                                break
                        elif process_res.get('code') != 0 and process_res.get('data') is not None:
                            bmcres.State("Failure")
                            bmcres.Message([process_res.get('data')])
                            break
                        else:
                            bmcres.State("Failure")
                            bmcres.Message(["cannot generate BMC cfg"])
                            break
                elif data["state"] == 2 or jj == "":
                    # 从头开始
                    import random
                    filename = str(random.randint(100, 999)) + ".json"
                    generate_res = RestFunc.generateBMCcfgByRest(client, filename)
                    if generate_res == {}:
                        bmcres.State("Failure")
                        bmcres.Message(["cannot generate BMC cfg"])
                    elif generate_res.get('code') == 0 and generate_res.get('data') is not None:
                        data = generate_res.get('data')
                        if "filename" in data:
                            state = 0
                            count = 0
                            complete_flag = 0
                            while state == 0:
                                if count > 60:
                                    bmcres.State("Failure")
                                    bmcres.Message(["generate log time out"])
                                    break
                                count = count + 1
                                import time
                                time.sleep(5)
                                # 循环查找直到完成
                                process_res = RestFunc.getBMCProgressByRest(client)
                                if process_res == {}:
                                    bmcres.State("Failure")
                                    bmcres.Message(["get BMC cfg error"])
                                    break
                                elif process_res.get('code') == 0 and process_res.get('data') is not None:
                                    data = process_res.get('data')
                                    if "state" in data and data["state"] == 2:
                                        state = 2
                                        # download
                                        download_res = RestFunc.downloadBMCcfgByRest(client, args.fileurl, filename)
                                        if download_res == {}:
                                            bmcres.State("Failure")
                                            bmcres.Message(["download BMC cfg error"])
                                        elif download_res.get('code') == 0 and download_res.get('data') is not None:
                                            bmcres.State("Success")
                                            #bmcres.Message(["export BMC cfg success"])
                                            bmcres.Message([download_res.get('data')])
                                        elif download_res.get('code') != 0 and download_res.get('data') is not None:
                                            bmcres.State("Failure")
                                            bmcres.Message([download_res.get('data')])
                                        else:
                                            bmcres.State("Failure")
                                            bmcres.Message(["cannot download BMC cfg"])
                                    elif "state" in data and data["state"] == 0:
                                        if "100" in data["progress"] or "complete" in data["progress"]:
                                            # download
                                            download_res = RestFunc.downloadBMCcfgByRest(client, args.fileurl, filename)
                                            if download_res == {}:
                                                bmcres.State("Failure")
                                                bmcres.Message(["download BMC cfg error"])
                                            elif download_res.get('code') == 0 and download_res.get('data') is not None:
                                                bmcres.State("Success")
                                                #bmcres.Message(["export BMC cfg success"])
                                                bmcres.Message([download_res.get('data')])
                                            elif download_res.get('code') != 0 and download_res.get('data') is not None:
                                                bmcres.State("Failure")
                                                bmcres.Message([download_res.get('data')])
                                            else:
                                                bmcres.State("Failure")
                                                bmcres.Message(["cannot download BMC cfg"])
                                            break
                                    else:
                                        bmcres.State("Failure")
                                        bmcres.Message(["cannot get export progress"])
                                        break
                                elif process_res.get('code') != 0 and process_res.get('data') is not None:
                                    bmcres.State("Failure")
                                    bmcres.Message([process_res.get('data')])
                                    break
                                else:
                                    bmcres.State("Failure")
                                    bmcres.Message(["cannot generate BMC cfg"])
                                    break
                        else:
                            bmcres.State("Failure")
                            bmcres.Message(["cannot generate BMC cfg"])

                    elif generate_res.get('code') != 0 and generate_res .get('data') is not None:
                        bmcres.State("Failure")
                        bmcres.Message([generate_res.get('data')])
                    else:
                        bmcres.State("Failure")
                        bmcres.Message(["generate BMC cfg failed"])
            else:
                bmcres.State("Failure")
                bmcres.Message(["get export progress error"])
        elif res.get('code') != 0 and res.get('data') is not None:
            bmcres.State("Failure")
            bmcres.Message([res.get('data')])
        else:
            bmcres.State("Failure")
            bmcres.Message(["get export BMC cfg progress error"])
        # logout
        RestFunc.logout(client)
        return bmcres

    def importbmccfg(self, client, args):
        checkparam_res = ResultBean()
        # check param
        '''
        file_suf = os.path.splitext(args.fileurl)[-1]
        if file_suf != ".json":
            checkparam_res.State("Failure")
            checkparam_res.Message(["File should be xxx.json."])
            return checkparam_res
        '''
        if not os.path.exists(args.fileurl):
            checkparam_res.State("Failure")
            checkparam_res.Message(["File is not exist."])
            return checkparam_res
        # check file must be json
        try:
            f = open(args.fileurl, "r")
            fr = f.read()
            import json
            json.loads(fr)
        except ValueError:
            checkparam_res.State("Failure")
            checkparam_res.Message(["File is not json format."])
            return checkparam_res
        #
        # check param end
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        upload_res = RestFunc.uploadBMCfgByRest(client, args.fileurl)
        bmcres = ResultBean()

        if upload_res == {}:
            bmcres.State("Failure")
            bmcres.Message(["upload BMC cfg file error"])
        elif upload_res.get('code') == 0 and upload_res.get('data') is not None:
            # import
            import_res = RestFunc.importBMCfgByRest(client)
            if import_res == {}:
                bmcres.State("Failure")
                bmcres.Message(["import BMC cfg error"])
            elif import_res.get('code') == 0 and import_res.get('data') is not None:
                count = 0
                # 重试次数
                retrynum = 3
                while True:
                    # 定时器
                    if count > 120:
                        bmcres.State("Failure")
                        bmcres.Message(["import BMC cfg time out"])
                        break
                    count = count + 1
                    import time
                    time.sleep(5)
                    # 循环查找直到完成
                    process_res = RestFunc.getBMCImportProgressByRest(client)
                    if process_res == {}:
                        if retrynum > 0:
                            retrynum = retrynum - 1
                            continue
                        else:
                            bmcres.State("Failure")
                            bmcres.Message(["import BMC cfg error, import progress is null"])
                            break
                    elif process_res.get('code') == 0 and process_res.get('data') is not None:
                        data = process_res.get('data')
                        #print (data)
                        if "completeCode" in data and data["completeCode"] == 0:
                            if "state" in data and data["state"] == 2:
                                bmcres.State("Success")
                                bmcres.Message(["import BMC cfg succcess"])
                                break
                        elif "completeCode" in data and data["completeCode"] != 0:
                            bmcres.State("Failure")
                            errorlist = {1: "configuration file does not exist ", 2: "failed to create IPMI Session ", 3: "failed to parse Json file ", 4: "set operation over retry number ", 16: "service setting failed :Json format error ", 17: "service setting failed :Json array overbounds ", 18: "service setting failed: please enter valid id", 19: "service setting failed: please enter valid timeout ", 20: "service setting failed: configuration item missing ", 21: "service setting failed ", 32: "NTP setting failed: configuration item missing ", 33: "NTP setting failed: please enter the correct enable state ", 34: "NTP set failed: parse date failed ", 35: "NTP setting failed: parse time failed ", 36: "NTP setting failure: setting time failure ", 37: "NTP setting failed: setting UTC time zone failed ", 38: "NTP setting failed: failed to configure time zone ", 39: "NTP setting failed ", 48: "SMTP setting failed :Json format error ", 49: "SMTP setting failed :Json array out of bounds ", 50: "SMTP setting failed: configuration item missing ", 51: "SMTP setting failed: please enter valid network interface ", 52: "SMTP setting failed: please enter valid server IP address ", 53: "SMTP setting failed ", 64: "SNMP setting failure :Json format error ", 65: "SNMP setting fails :Json array overruns ", 66: "SNMP alarm IP setting fails ", 67: "SNMP warning email setting failed ", 68: "SNMP setting failed ", 80: "user setting failed :Json format error ", 81: "user setting failed :Json array overbounds ", 82: "user setting failed: add user failed ", 83: "user setting failed: modify user failed ", 84: "user setting fails: deletion fails ", 85: "failure of user setting: failure of obtaining user information ", 86: "user setting failed: please enter valid user ID", 87: "user setting failed: please enter valid user permissions ", 88: "user setting failed: user group name is empty ", 89: "user setting failed: user name is empty ", 90: "user setting fails: user name already exists ", 91: "user setting failed: password is empty ", 92: "user setting fails: password already exists ", 93: "user setting failed: old password is empty ", 94: "user setting failed: please enter a valid password change flag ", 95: "user setting fails: old password validation fails ", 96: "user setting failed: password length does not match ", 97: "user setting failed: password complexity not met ", 98: "user Settings fail: mailbox Settings fail ", 99: "user setting fails: mailbox format failed ", 100: "user setting failed: failed to add user to user group ", 112: "network setting failed :Json format error ", 113: "network setting failed :Json array overbounds ", 114: "network setting failed: please enter valid network interface ", 115: "network setting failed: please enter valid IP address ", 116: "network setting failed: please enter a valid subnet mask ", 117: "network setting failed: please enter valid default gateway ", 118: "network setting failed: please enter the correct enabling state ", 119: "network setting failed: configuration item missing ", 120: "network setting failed ", 121: "DNS setting failed ", 122: "network aggregation Settings failed ", 123: "network link setting failed ", 124: "network link setting failed: configuration item missing "}
                            bmcres.Message([errorlist[data["completeCode"]]])
                            break
                        else:
                            bmcres.State("Failure")
                            bmcres.Message(["import BMC cfg error, get import progress error"])
                            break
                    elif process_res.get('code') == 1:
                        if retrynum > 0:
                            retrynum = retrynum - 1
                            continue
                        else:
                            bmcres.State("Failure")
                            bmcres.Message([process_res.get('data')])
                            break
                    elif process_res.get('code') != 0 and process_res.get('data') is not None:
                        bmcres.State("Failure")
                        bmcres.Message([process_res.get('data')])
                        break
                    else:
                        if retrynum > 0:
                            retrynum = retrynum - 1
                            continue
                        else:
                            bmcres.State("Failure")
                            bmcres.Message(["cannot get import progress"])
                            break

            elif import_res.get('code') != 0 and import_res.get('data') is not None:
                bmcres.State("Failure")
                bmcres.Message([import_res.get('data')])
            else:
                bmcres.State("Failure")
                bmcres.Message(["cannot import BMC cfg"])

        elif upload_res.get('code') != 0 and upload_res .get('data') is not None:
            bmcres.State("Failure")
            bmcres.Message([upload_res.get('data')])
        else:
            bmcres.State("Failure")
            bmcres.Message(["cannot upload BMC cfg"])
        # logout
        RestFunc.logout(client)
        return bmcres

    def setvnc(self, client, args):
        '''
        set vnc setting
        :param client:
        :param args:
        :return:
        '''

        # set
        set_result = ResultBean()
        res = {}
        res_pwd = {}
        if args.enabled is not None and args.enabled == 'Disabled' and (
                args.secureport is not None or args.nonsecureport is not None or args.pwd is not None or args.timeout is not None):
            set_result.State("Failure")
            set_result.Message(["Settings are not supported when -e is set to Disabled."])
            return set_result
        if args.pwd is not None and (len(args.pwd) > 8 or len(args.pwd) < 1):
            set_result.State("Failure")
            set_result.Message(["the length of password is 1-8."])
            return set_result
        if args.enabled is not None:
            if 'Enabled' in args.enabled:
                enabled = ' 0x01'
            else:
                enabled = ' 0x00'
        if args.secureport is not None:
            if args.secureport < 1 or args.secureport > 65535:
                set_result.State("Failure")
                set_result.Message(["secureport is in 1-65535."])
                return set_result
            else:
                sp = '{:08x}'.format(args.secureport)
                sp_hex = hexReverse(sp)
        if args.pwd is not None:
            args.pwd = ascii2hex(args.pwd, len(args.pwd))
        if args.nonsecureport is not None:
            if args.nonsecureport < 1 or args.nonsecureport > 65535:
                set_result.State("Failure")
                set_result.Message(["non secure port is in 1-65535."])
                return set_result
            else:
                nsp = '{:08x}'.format(args.nonsecureport)
                nsp_hex = hexReverse(nsp)
        if args.timeout is not None:
            if args.timeout < 60 or args.timeout > 1800 or args.timeout % 60 != 0:
                set_result.State("Failure")
                set_result.Message(["timeout is in 60-1800 and is mutiple of 60."])
                return set_result
            else:
                time = '{:08x}'.format(args.timeout)
                timeout = hexReverse(time)

        if args.timeout is not None or args.secureport is not None or args.nonsecureport is not None or args.enabled is not None:
            interface_temp = "F" * 16
            interface = ascii2hex(interface_temp, 17)
            if args.timeout is None or args.secureport is None or args.nonsecureport is None or args.enabled is None:
                # 需要获取
                try:
                    Info_all = IpmiFunc.getM5VncByIpmi(client)
                except BaseException:
                    set_result.State('Failure')
                    set_result.Message(['this command is incompatible with current server.'])
                    return set_result
                if Info_all:
                    if Info_all.get('code') == 0 and Info_all.get('data') is not None:
                        Info = Info_all.get('data')
                        if args.enabled is None:
                            if Info['Status'] == 'Disabled':
                                set_result.State("Failure")
                                set_result.Message(["please set status to Enabled firstly."])
                                return set_result
                            status_dict = {'Disabled': '00', 'Enabled': '01'}
                            enabled = hex(int(status_dict[Info['Status']]))
                        if args.nonsecureport is None:
                            if Info['NonsecurePort'] == 'N/A':
                                nsp_hex = "0xff " * 4
                            else:
                                nsp = '{:08x}'.format(Info['NonsecurePort'])
                                nsp_hex = hexReverse(nsp)
                        if args.secureport is None:
                            if Info['SecurePort'] == 'N/A':
                                sp_hex = "0xff " * 4
                            else:
                                sp = '{:08x}'.format(Info['SecurePort'])
                                sp_hex = hexReverse(sp)
                        if args.timeout is None:
                            if Info['Timeout'] == "N/A":
                                timeout = "0xff " * 4
                            else:
                                t = '{:08x}'.format(Info['Timeout'])
                                timeout = hexReverse(t)
                        if Info['InterfaceName'] == 'N/A':
                            interface_temp = "F" * 16
                            interface = ascii2hex(interface_temp, 17)
                        else:
                            interface = ascii2hex(Info['InterfaceName'], 17)
                    else:
                        set_result.State("Failure")
                        set_result.Message(["get current vnc status failed. " + Info_all.get('data')])
                        return set_result
                else:
                    set_result.State("Failure")
                    set_result.Message(["failed to set vnc info."])
                    return set_result
            if args.pwd is None:
                # 只设置其他项
                res = IpmiFunc.setM5VncByIpmi(client, enabled, interface, nsp_hex, sp_hex, timeout)
                if res == {}:
                    set_result.State("Failure")
                    set_result.Message(["set vnc setting failed."])
                elif res.get('code') == 0:
                    set_result.State('Success')
                    set_result.Message(['set vnc setting success.'])
                else:
                    set_result.State("Failure")
                    set_result.Message(["set vnc setting failed. " + res.get('code', '')])
            else:
                # 需要设置其他项和密码
                res = IpmiFunc.setM5VncByIpmi(client, enabled, interface, nsp_hex, sp_hex, timeout)
                res_pwd = IpmiFunc.setM5VncPwdByIpmi(client, args.pwd)
                if res == {} or res_pwd == {}:
                    set_result.State("Failure")
                    set_result.Message(["set vnc setting failed."])
                elif res.get('code') == 0 and res_pwd.get('code') == 0:
                    set_result.State('Success')
                    set_result.Message(['set vnc password and setting success.'])
                elif res.get('code') == 0 and res_pwd.get('code') != 0:
                    set_result.State("Failure")
                    set_result.Message(["set vnc setting success,but failed to set password."])
                elif res.get('code') != 0 and res_pwd.get('code') == 0:
                    set_result.State("Failure")
                    set_result.Message(["set vnc password success,but failed to set setting."])
                else:
                    set_result.State("Failure")
                    set_result.Message(["failed to set setting and password."])
        elif args.pwd is not None and (
                args.timeout is None and args.secureport is None and args.nonsecureport is None and args.enabled is None):
            # 只设置密码
            # 需要获取当前状态
            Info_all = IpmiFunc.getM5VncByIpmi(client)
            if Info_all:
                if Info_all.get('code') == 0 and Info_all.get('data') is not None:
                    Info = Info_all.get('data')
                    if Info['Status'] == 'Disabled':
                        set_result.State("Failure")
                        set_result.Message(["please set status to Enabled firstly."])
                        return set_result
                else:
                    set_result.State("Failure")
                    set_result.Message(["get current vnc status failed. " + Info_all.get('data')])
                    return set_result
            else:
                set_result.State("Failure")
                set_result.Message(["get current vnc status failed."])
                return set_result
            res_pwd = IpmiFunc.setM5VncPwdByIpmi(client, args.pwd)
            if res_pwd == {}:
                set_result.State("Failure")
                set_result.Message(["set vnc password failed."])
            elif res_pwd.get('code') == 0:
                set_result.State('Success')
                set_result.Message(['set vnc password success.'])
            else:
                set_result.State("Failure")
                # set_result.Message([str(res_pwd.get('data'))])
                set_result.Message(["set vnc password failed. " + res_pwd.get('data', '')])
        else:
            set_result.State("Failure")
            set_result.Message(["please input a subcommand."])

        return set_result

    def getvnc(self, client, args):
        '''
       get vnc setting
       :param client:
       :param args:
       :return: vnc info
       '''
        get_result = ResultBean()
        res = VncBean()
        try:
            Info_all = IpmiFunc.getM5VncByIpmi(client)
        except BaseException:
            get_result.State('Failure')
            get_result.Message(['this command is incompatible with current server.'])
            return get_result
        if Info_all:
            if Info_all.get('code') == 0 and Info_all.get('data') is not None:
                data = Info_all.get('data')
                res.KeyboardLayout(None)
                if data.get('Timeout', 0) == 'N/A':
                    res.SessionTimeoutMinutes(0)
                else:
                    res.SessionTimeoutMinutes(int(data.get('Timeout', 0)) / 60)
                # res.SSLEncryptionEnabled(True if data.get('Status') == 'Enabled' else False)
                res.SSLEncryptionEnabled(None)
                if data.get('MaximumSessions', 0) == 'N/A':
                    res.MaximumNumberOfSessions(0)
                else:
                    res.MaximumNumberOfSessions(int(data.get('MaximumSessions', 0)))
                if data.get('ActiveSessions', 0) == 'N/A':
                    res.NumberOfActivatedSessions(0)
                else:
                    res.NumberOfActivatedSessions(int(data.get('ActiveSessions', 0)))
                res.SessionMode(None)
                get_result.State('Success')
                get_result.Message([res.dict])
                return get_result
            else:
                get_result.State('Failure')
                get_result.Message(['Failed to get vnc info. ' + Info_all.get('data')])
                return get_result
        else:
            get_result.State('Failure')
            get_result.Message(['Failed to get vnc info.'])
            return get_result

    def getvncsession(self, client, args):

        priv_dict = {4: "Administrator", 3: "Operator", 2: "Commonuser", 15: "Noaccess"}
        result = ResultBean()
        headers = RestFunc.login(client)
        client.setHearder(headers)
        # get
        res = RestFunc.getM5VncSessionInfoByRest(client)
        if res.get('code') == 0 and res.get('data') is not None:
            num = len(res.get('data'))
            if num == 0:
                result.State('Success')
                result.Message(['session count is 0.'])
            else:
                list_Info = []
                for i in range(num):
                    vnc_info = VncSessionBean()
                    vnc_info.SessionId(res.get('data')[i].get('session_id', None))
                    vnc_info.Id(res.get('data')[i].get('id', None))
                    vnc_info.ClientIP(res.get('data')[i].get('client_ip', None))
                    vnc_info.SessionType(res.get('data')[i].get('session_type', None))
                    vnc_info.UserId(res.get('data')[i].get('user_id', None))
                    vnc_info.UserName(res.get('data')[i].get('user_name', None))
                    vnc_info.UserPrivilege(priv_dict.get(res.get('data')[i].get('user_privilege', None), None))
                    list_Info.append(vnc_info.dict)
                result.State('Success')
                result.Message([list_Info])
        else:
            result.State('Failure')
            result.Message(['failed to get vnc session info， ' + str(res.get('data'))])
        # logout
        RestFunc.logout(client)
        return result

    def delvncsession(self, client, args):
        result = ResultBean()
        # login
        headers = RestFunc.login(client)
        client.setHearder(headers)
        # 先get
        id_list = []
        res = RestFunc.getM5VncSessionInfoByRest(client)
        if res.get('code') == 0 and res.get('data') is not None and len(res.get('data')) != 0:
            num = len(res.get('data'))
            for i in range(num):
                id_list.append(str(res.get('data')[i].get('session_id')))

            # 如果输入参数，检查参数范围，如果正确，进行删除
            if args.id is not None:
                if str(args.id) in id_list:
                    res1 = RestFunc.deleteM5VncSessionByRest(client, args.id)
                    if res1.get('code') == 0 and res1.get('data') is not None and res1.get('data').get('cc', 1) == 0:
                        result.State('Success')
                        result.Message(['delete session id {0} success, please wait a few seconds.'.format(args.id)])
                    elif res1.get('code') == 0 and res1.get('data') is not None and res1.get('data').get('cc', 1) != 0:
                        result.State('Failure')
                        result.Message(['delete vnc session request parsing failed.'])
                    else:
                        result.State('Failure')
                        result.Message(['delete session id {0} failed， '.format(args.id) + res1.get('data')])
                else:
                    result.State('Failure')
                    result.Message(['wrong session id, please input right id, id list is {0}.'.format(','.join(id_list) if len(id_list) > 1 else id_list)])
            else:
                # 如果不输入，循环调用，全部删除
                flag = []
                for i in range(num):
                    res1 = RestFunc.deleteM5VncSessionByRest(client, id_list[i])
                    if res1.get('code') == 0 and res1.get('data') is not None and res1.get('data').get('cc', 1) == 0:
                        continue
                    else:
                        flag.append(str(id_list[i]))
                        continue
                if len(flag) != 0:
                    result.State('Failure')
                    result.Message(['delete session id {0} failed.'.format(','.join(flag) if len(flag) > 1 else flag)])
                else:
                    result.State('Success')
                    result.Message(['delete session id {0} success, please wait a few seconds.'.format(','.join(id_list) if len(id_list) > 1 else id_list)])
        elif res.get('code') == 0 and res.get('data') is not None and len(res.get('data')) == 0:
            result.State('Failure')
            result.Message(['session count is 0.'])
        else:
            result.State('Failure')
            result.Message(['failed to get vnc session info， ' + str(res.get('data'))])
        # logout
        RestFunc.logout(client)
        return result

    def setbiospwd(self, client, args):
        '''
        set bios password
        :param client:
        :param args:
        :return:
        '''
        set_result = ResultBean()
        # if args.oldpassword is not None:
        #     set_result.State('Failure')
        #     set_result.Message(['not need old password input.'])
        #     return set_result
        if len(args.newpassword) < 8 or len(args.newpassword) > 20:
            set_result.State('Failure')
            set_result.Message(['length of password range from 8-20.'])
            return set_result
        # 判断BIOS版本号,版本号为4.0.11以上
        bios_version = IpmiFunc.getM5BiosVersionByIpmi(client)
        # print(bios_version)
        if bios_version and 'code' in bios_version and bios_version['code'] == 0:
            # bios_version['data']['Version'] = 'x.3.x'
            version = bios_version['data'].get('Version', 0).split('(')[0].split('.')
            if len(version) >= 3:
                if int(version[1]) != 3:
                    set_result.State('Failure')
                    set_result.Message(['current bios version is not support, please upgrade bios.'])
                    return set_result
            else:
                set_result.State('Failure')
                set_result.Message(['not support current bios version.'])
                return set_result
        else:
            set_result.State('Failure')
            set_result.Message(['can not get bios version.'])
            return set_result

        pwd = ascii2hex(args.newpassword, len(args.newpassword))
        if args.type == 'User':
            type = '0x01'
        else:
            type = '0x00'
        Info_all = IpmiFunc.setM5BiosPwdByIpmi(client, type, pwd)
        if Info_all:
            if Info_all.get('code') == 0:
                set_result.State('Success')
                set_result.Message([])
                return set_result
            else:
                set_result.State('Failure')
                set_result.Message(['Do not be in bios or in the process of switching on or off, and input right password format.' + Info_all.get("code", "")])
                return set_result
        else:
            set_result.State('Failure')
            set_result.Message(['Do not be in bios or in the process of switching on or off, and input right password format.'])
            return set_result

    def clearbiospwd(self, client, args):
        '''
        clear bios password
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        if args.type == 'User':
            type = '0x01'
        else:
            type = '0x00'
        Info_all = IpmiFunc.clearBiospwdM5ByIpmi(client, type)
        if Info_all:
            if Info_all.get('code') == 0:
                result.State('Success')
                result.Message([])
                return result
            else:
                result.State('Failure')
                result.Message(['Failed to clear bios password. ' + Info_all.get('data', '')])
                return result
        else:
            result.State('Failure')
            result.Message(['Failed to clear bios password.'])
            return result

    def restorebios(self, client, args):
        '''
        restore BIOS setup factory configuration
        :param client:
        :param args:
        :return:
        '''
        result = ResultBean()
        Info_all = IpmiFunc.restoreBiosM5ByIpmi(client)
        if Info_all:
            if Info_all.get('code') == 0:
                result.State('Success')
                result.Message([])
                return result
            else:
                result.State('Failure')
                result.Message(['Failed to restore bios. ' + Info_all.get('data', '')])
                return result
        else:
            result.State('Failure')
            result.Message(['Failed to restore bios.'])
            return result

    def getfirewall(self, client, args):
        '''
        get firewall configuration
        :param client:
        :return:
        '''
        # get
        get_res = ResultBean()
        res = IpmiFunc.getFirewallByIpmi(client)

        if res == {}:
            get_res.State("Failure")
            get_res.Message(["get firewall state failed"])
        elif res.get('code') == 0:
            get_res.State('Success')
            if res.get('data') == "00":
                get_res.Message(['closed'])
            elif res.get('data') == "01":
                get_res.Message(['black list mode(not enable)'])
            elif res.get('data') == "02":
                get_res.Message(['white list mode'])
        else:
            get_res.State("Failure")
            get_res.Message("cannot get firewall state: " + res.get('data'))
        return get_res

    def setfirewall(self, client, args):
        '''
        get firewall configuration
        :param client:
        :return:
        '''
        # get
        set_res = ResultBean()
        res = IpmiFunc.setFirewallByIpmi(client, args.state)

        if res == {}:
            set_res.State("Failure")
            set_res.Message(["set firewall state failed"])
        elif res.get('code') == 0:
            set_res.State('Success')
            set_res.Message([res.get('data')])
        else:
            set_res.State("Failure")
            set_res.Message([res.get('data')])
        return set_res

    # 白名单添加删除

    def Opwhitelist(client, args):
        # 检查参数必须为0x的16进制
        param_p = '^0(x|X)[0-9a-fA-F]{2}$'
        if not re.search(param_p, args.channel, re.I):
            res = ResultBean()
            res.State('Failure')
            res.Message(["channel should be 0x00-0x0f"])
            return res
        if not re.search(param_p, args.lun, re.I):
            res = ResultBean()
            res.State('Failure')
            res.Message(["lun should be 0x00, 0x01, 0x10, 0x11"])
            return res
        if not re.search(param_p, args.netfn, re.I):
            res = ResultBean()
            res.State('Failure')
            res.Message(["netfn should be even,and between 0x00-0x3e"])
            return res
        if not re.search(param_p, args.command, re.I):
            res = ResultBean()
            res.State('Failure')
            res.Message(["command should be 0x00-0xff"])
            return res
        # 检查是否为白名单模式
        get_res = ResultBean()
        res = IpmiFunc.getFirewallByIpmi(client)
        if res == {}:
            get_res.State("Failure")
            get_res.Message(["get firewall state failed"])
        elif res.get('code') == 0:
            if res.get('data') != "02":
                get_res.State("Failure")
                get_res.Message(["firewall is not whitelist mode"])
        else:
            get_res.State("Failure")
            get_res.Message(["cannot get firewall state: " + res.get('data')])
        if get_res.State == "Failure":
            return get_res
        # 操作白名单
        add_res = ResultBean()
        try:
            channel10 = int(args.channel, 16)
            if channel10 > 15:
                add_res.State('Failure')
                add_res.Message(["channel should be 0x00-0x0f"])
                return add_res
        except BaseException:
            add_res.State('Failure')
            add_res.Message(["channel should be hex"])
            return add_res
        try:
            lun10 = int(args.lun, 16)
            if lun10 != 0 and lun10 != 1 and lun10 != 16 and lun10 != 17:
                add_res.State('Failure')
                add_res.Message(["lun should be 0x00, 0x01, 0x10, 0x11"])
                return add_res
        except BaseException:
            add_res.State('Failure')
            add_res.Message(["lun should be hex"])
            return add_res
        try:
            netfn10 = int(args.netfn, 16)
            if netfn10 > 63 or netfn10 % 2 == 1:
                add_res.State('Failure')
                add_res.Message(["netfn should be even,and between 0x00-0x3e"])
                return add_res
        except BaseException:
            add_res.State('Failure')
            add_res.Message(["netfn should be like 0x00"])
            return add_res

        try:
            command10 = int(args.command, 16)
            if command10 > 255:
                add_res.State('Failure')
                add_res.Message(["command should be 0x00-0xff"])
                return add_res
        except BaseException:
            add_res.State('Failure')
            add_res.Message(["command should be hex"])
            return add_res
        res = IpmiFunc.opWhiteListByIpmi4(client, args.op, args.channel, args.lun, args.netfn, args.command)
        if res == 0:
            add_res.State('Success')
            if args.op == "add":
                add_res.Message(["add cmd to white list success"])
            else:
                add_res.Message(["del cmd from white list success"])
        else:
            add_res.State("Failure")
            if args.op == "add":
                add_res.Message(["add cmd to white list error"])
            else:
                add_res.Message(["del cmd from white list error"])
        return add_res

    def addwhitelist(self, client, args):
        add_res = ResultBean()
        args.op = "add"
        add_res = NF5280M5_435.Opwhitelist(client, args)
        return add_res

    def delwhitelist(self, client, args):
        add_res = ResultBean()
        args.op = "del"
        add_res = NF5280M5_435.Opwhitelist(client, args)
        return add_res

    def collect(self, client, args):
        if args.component is not None:
            res = ResultBean()
            res.State("Not Support")
            res.Message(["param(-t) component is not support"])
            return res
        checkparam_res = ResultBean()
        if args.fileurl == ".":
            file_name = ""
            file_path = os.path.abspath(".")
            args.fileurl = os.path.join(file_path, file_name)
        elif args.fileurl == "..":
            file_name = ""
            file_path = os.path.abspath("..")
            args.fileurl = os.path.join(file_path, file_name)
        elif re.search(r"^[C-Zc-z]\:$", args.fileurl, re.I):
            file_name = ""
            file_path = os.path.abspath(args.fileurl + "\\")
            args.fileurl = os.path.join(file_path, file_name)
        else:
            file_name = os.path.basename(args.fileurl)
            file_path = os.path.dirname(args.fileurl)
        # 只输入文件名字，则默认为当前路径
        if file_path == "":
            file_path = os.path.abspath(".")
            args.fileurl = os.path.join(file_path, file_name)

        # 用户输入路径，则默认文件名dump_psn_time.tar
        if file_name == "":
            psn = "UNKNOWN"
            res = Base.getfru(self, client, args)
            if res.State == "Success":
                frulist = res.Message[0].get("FRU", [])
                if frulist != []:
                    psn = frulist[0].get('ProductSerial', 'UNKNOWN')
            else:
                return res
            import time
            struct_time = time.localtime()
            logtime = time.strftime("%Y%m%d-%H%M", struct_time)
            file_name = "dump_" + psn + "_" + logtime + ".tar"
            args.fileurl = os.path.join(file_path, file_name)
        else:
            p = r'\.tar$'
            if not re.search(p, file_name, re.I):
                checkparam_res.State("Failure")
                checkparam_res.Message(["Filename should be xxx.tar"])
                return checkparam_res
            file_name = file_name[0:-4] + ".tar"
        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
            except BaseException:
                checkparam_res.State("Failure")
                checkparam_res.Message(["can not create path."])
                return checkparam_res
        else:
            if os.path.exists(args.fileurl):
                name_id = 1
                name_new = file_name[:-4] + "(1).tar"
                file_new = os.path.join(file_path, name_new)
                while os.path.exists(file_new):
                    name_id = name_id + 1
                    name_new = file_name[:-4] + "(" + str(name_id) + ")" + ".tar"
                    file_new = os.path.join(file_path, name_new)
                args.fileurl = file_new

        # check param end
        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)

        bmcres = ResultBean()
        # 因为无法通过FileExistFlag=0判断是否1正在生成2刚刚刷了系统
        # 所以每次都要重新生成文件
        generate_res = RestFunc.triggeronekeylog(client)
        if generate_res == {}:
            bmcres.State("Failure")
            bmcres.Message(["cannot generate log"])
        elif generate_res.get('code') == 0:
            bmcres = NF5280M5_435.getProgressAndDown(client, args)
        else:
            bmcres.State("Failure")
            bmcres.Message([generate_res.get('data')])

        # logout
        RestFunc.logout(client)
        return bmcres

    # 检查日志是否存在，确定存在后，下载文件
    def getProgressAndDown(client, args):
        bmcres = ResultBean()
        count = 0
        error_info = ""
        while True:
            if count > 40:
                bmcres.State("Failure")
                bmcres.Message(["collect log time out. Last response is " + error_info])
                break
            count = count + 1
            import time
            time.sleep(15)
            # 循环查找直到完成
            process_res = RestFunc.checkonekeylogexist(client)
            if process_res == {}:
                bmcres.State("Failure")
                bmcres.Message(["cannot generate log"])
                break
            elif process_res.get('code') == 0 and process_res.get('data') is not None:
                data = process_res.get('data')
                error_info = data
                if "FileExistFlag" in data and "FileName" in data:
                    # log收集成功
                    if data["FileExistFlag"] == 1 and data["FileName"] != "":
                        # get folder
                        folder = data['FileName']
                        # download
                        download_res = RestFunc.downloadonekeylogByRest(client, args.fileurl, folder)
                        if download_res == {}:
                            bmcres.State("Failure")
                            bmcres.Message(["download log error"])
                        elif download_res.get('code') == 0 and download_res.get('data') is not None:
                            bmcres.State("Success")
                            bmcres.Message([download_res.get('data')])
                        elif download_res.get('code') != 0 and download_res.get('data') is not None:
                            bmcres.State("Failure")
                            bmcres.Message([download_res.get('data')])
                        else:
                            bmcres.State("Failure")
                            bmcres.Message(["cannot download log"])
                        break
                    elif data["FileExistFlag"] == 0 and data["FileName"] == "":
                        continue
                    else:
                        bmcres.State("Failure")
                        bmcres.Message(["cannot find log file"])
                        break
                else:
                    bmcres.State("Failure")
                    bmcres.Message(["can not find log file"])
                    break
            elif process_res.get('code') != 0 and process_res.get('data') is not None:
                bmcres.State("Failure")
                bmcres.Message([process_res.get('data')])
                break
            else:
                bmcres.State("Failure")
                bmcres.Message(["generate log error"])
                break
        return bmcres
