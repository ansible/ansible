# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: base Class
#
#   @author: zhang
#   @Date:
#=========================================================================
'''
from ansible.plugins.inspur_sdk.interface.NF5280M5_435 import NF5280M5_435
from ansible.plugins.inspur_sdk.command import RestFunc
from ansible.plugins.inspur_sdk.interface.ResEntity import *
import os
import re


class NF5280M5_436(NF5280M5_435):
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
        res = RestFunc.exportTwoBios_436_CfgByRest(client, args.fileurl, file_name)

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
