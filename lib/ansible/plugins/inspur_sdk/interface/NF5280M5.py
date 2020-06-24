# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: base Class
#
#   @author: zhang
#   @Date:
#=========================================================================
'''
from ansible.plugins.inspur_sdk.interface.CommonM5 import CommonM5
import sys
import os
import re
from ansible.plugins.inspur_sdk.command import RestFunc
import random
import time
from ansible.plugins.inspur_sdk.interface import Base
from ansible.plugins.inspur_sdk.interface.ResEntity import *


# sys.path.append(os.path.abspath("../command"))
rootpath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(rootpath, "command"))
sys.path.append(os.path.join(rootpath, "util"))


class NF5280M5(CommonM5):

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

        # login
        headers = RestFunc.login(client)
        if headers == {}:
            login_res = ResultBean()
            login_res.State("Failure")
            login_res.Message(["login error, please check username/password/host/port"])
            return login_res
        client.setHearder(headers)
        # 生成log
        bmcres = ResultBean()
        generate_res = RestFunc.generateOnekeylogByRest(client)
        if generate_res['code'] == 404:
            # bmcres.State("Not Support")
            # bmcres.Message([""])
            generate_res = RestFunc.triggeronekeylog(client)
            if generate_res == {}:
                bmcres.State("Failure")
                bmcres.Message(["cannot generate log"])
            elif generate_res.get('code') == 0:
                bmcres = NF5280M5.getProgressAndDown(client, args)
            elif generate_res['code'] == 404:
                bmcres.State("Not Support")
                bmcres.Message([""])
            else:
                bmcres.State("Failure")
                bmcres.Message([generate_res.get('data')])
        else:
            if generate_res.get('code') != 0:
                bmcres.State("Failure")
                bmcres.Message([generate_res.get('data')])
            else:
                export_res = RestFunc.exportOnekeylogByRest(client)
                if export_res.get('code') == 0:

                    count = 0
                    while True:
                        if count > 60:
                            break
                        count = count + 1
                        import time
                        time.sleep(5)
                    # get
                    res = RestFunc.getOnekeylogByRest(client, args.fileurl)
                    if res == {}:
                        bmcres.State("Failure")
                        bmcres.Message(["cannot download onekeylog"])
                    elif res.get('code') == 0 and res.get('data') is not None:
                        bmcres.State("Success")
                        data = res.get('data')
                        bmcres.Message([data])
                    elif res.get('code') != 0 and res.get('data') is not None:
                        bmcres.State("Failure")
                        bmcres.Message([res.get('data')])
                    else:
                        bmcres.State("Failure")
                        bmcres.Message(["download onekeylog error"])
                elif export_res.get('code') == 404:
                    bmcres.State("Not Support")
                    bmcres.Message([""])
                else:
                    bmcres.State("Failure")
                    bmcres.Message(["download onekeylog error"])
        if bmcres.State == "Not Support":
            # 收集黑盒
            bmcres = NF5280M5.collectblackbox(client, args)

        # logout
        RestFunc.logout(client)
        return bmcres

    # 检查日志是否存在，确定存在后，下载文件

    def getProgressAndDown(self, client, args):
        bmcres = ResultBean()
        count = 0
        error_count = 0
        error_info = ""
        while True:
            if count > 40:
                bmcres.State("Failure")
                bmcres.Message(["collect log time out. Last response is " + error_info])
                break
            if error_count > 3:
                bmcres.State("Failure")
                bmcres.Message([error_info])
                break
            count = count + 1
            import time
            time.sleep(15)
            # 循环查找直到完成
            process_res = RestFunc.checkonekeylogexist(client)
            if process_res == {}:
                error_info = "Failed to call BMC interface api/checkonekeylogexist, response is none."
                error_count = error_count + 1
                continue
            elif "code" in process_res and "data" in process_res:
                if process_res.get('code') == 0:
                    data = process_res.get('data')
                    error_info = data
                    if "FileExistFlag" in data and "FileName" in data:
                        # log收集成功
                        # if data["FileExistFlag"] == 1 and data["FileName"] != "":
                        if data["FileName"] != "":
                            # get folder
                            folder = data['FileName']
                            # download
                            download_res = RestFunc.downloadonekeylogByRest(client, args.fileurl, folder)
                            if download_res == {}:
                                bmcres.State("Failure")
                                bmcres.Message(['Failed to call BMC interface ' + args.logpath + ', response is none'])
                            elif download_res.get('code') == 0:
                                bmcres.State("Success")
                                bmcres.Message([download_res.get('data')])
                            else:
                                bmcres.State("Failure")
                                bmcres.Message([download_res.get('data')])
                            break
                        # elif data["FileExistFlag"] == 0 and data["FileName"] == "":
                        elif data["FileName"] == "":
                            continue
                        else:
                            continue
                            # bmcres.State("Failure")
                            #bmcres.Message(["cannot find log file"])
                            # break
                    else:
                        error_info = data
                        error_count = error_count + 1
                        continue
                else:
                    bmcres.State("Failure")
                    bmcres.Message([process_res.get('data')])
                    continue
            else:
                error_info = "cannot check one key log status" + str(process_res)
                error_count = error_count + 1
                continue
        return bmcres

    def collectblackbox(self, client, args):
        bmcres = ResultBean()
        try:
            file_path = os.path.dirname(args.fileurl)
            randomID = str(random.randint(0, 1000))
            bbl_path = os.path.join(file_path, randomID)
            while os.path.exists(bbl_path):
                randomID = str(random.randint(0, 1000))
                bbl_path = os.path.join(file_path, randomID)
            if not os.path.exists(bbl_path):
                os.makedirs(bbl_path)
                time.sleep(5)

            NF5280M5.collectBlackboxlog(client, bbl_path, "blackbox")
            NF5280M5.collectBlackboxlog(client, bbl_path, "blackboxpeci")
            # 打包
            import tarfile
            tar = tarfile.open(args.fileurl, "w")
            for root, dir, files in os.walk(bbl_path):
                for file in files:
                    fullpath = os.path.join(root, file)
                    tar.add(fullpath, arcname=file)
            tar.close()

            for root, dir, files in os.walk(bbl_path):
                for file in files:
                    fullpath = os.path.join(root, file)
                    os.remove(fullpath)

            if os.path.exists(bbl_path):
                os.removedirs(bbl_path)

            bmcres.State("Success")
            bmcres.Message(["Download blackbox log success, the file path is " + os.path.abspath(args.fileurl)])
            return bmcres
        except Exception as e:
            bmcres.State("Failure")
            bmcres.Message(["Cannot collect blackbox log: " + str(e)])
            return bmcres

    # 收集日志到bbl_path
    def collectBlackboxlog(self, client, bbl_path, logtype):  # 查看黑盒日志是否存在
        bbl_file = os.path.join(bbl_path, logtype + ".log")
        log_exist_res = RestFunc.getblacklogfileexist(client, logtype)
        if log_exist_res.get("code") == 0:
            if log_exist_res.get("data").get('FileExistFlag') == 1:
                download_res = RestFunc.downloadBlackboxlogByRest(client, bbl_file, logtype)
                if download_res.get("code") == 0:
                    a = ""
                    with open(download_res.get("data"), 'rb') as f:
                        a = f.read()
                    try:
                        b = a.decode("utf-8")
                    except BaseException:
                        # 需要解码
                        import platform
                        if platform.system() == 'Linux':
                            cmd = '/tools//blackbox_decrypt/blackbox_decrypt '
                        else:
                            cmd = "\\tools\\blackbox_decrypt\\blackbox_decrypt.exe "
                        cmd = os.path.dirname(os.path.dirname(__file__)) + cmd + download_res.get("data") + " > " + os.path.join(bbl_path, "res")
                        try:
                            pathnow = os.getcwd()
                            os.chdir(os.path.dirname(download_res.get("data")))
                            result_cmd = os.popen(cmd)
                            result_cmd.close()
                            with open(os.path.join(bbl_path, "res")) as deres:
                                deresTxt = deres.read()
                            if deresTxt.find('Success') > -1:
                                logNameStart = deresTxt.find('Decrypt Success to')
                                logName = deresTxt[logNameStart + 18:].strip()
                                if logName[-1] == '.':
                                    logName = logName[:-1]
                                import shutil
                                shutil.move(logName, download_res.get("data"))
                            os.chdir(pathnow)
                            if os.path.exists(os.path.join(bbl_path, "res")):
                                os.remove(os.path.join(bbl_path, "res"))
                        except Exception as e:
                            return

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
