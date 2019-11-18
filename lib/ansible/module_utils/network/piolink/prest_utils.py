#!/usr/bin/python
# -*- coding:utf-8 -*-

# Copyright (c) 2019, Piolink Inc.
# GNU General Pubilc License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import re
import ast
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from ansible.module_utils.network.piolink.prest_module import PrestModule,\
    CMD_SITE_TYPE, CMD_APP_TYPE, CMD_AMSS_TYPE
from ansible.module_utils.basic import missing_required_lib


class PrestUtils(PrestModule):
    def __init__(self, module):
        super(PrestUtils, self).__init__()
        
        if not HAS_REQUESTS:
            module.fail_json(msg=missing_required_lib('requests'))

        self.module = module
        self.resp = None
        self.p = re.compile('(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
                            '\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
                            '\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
                            '\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')

        self.init_module()

    def init_module(self):
        result = dict(
            original_message='',
            message='',
            debug=''
        )

        self.result = result

    def init_args(self):
        # set prefix url
        self.prefix_url = 'https://{0}:{1}/api/v2'.format(
            self.module.params['host'], self.module.params['port'])

        # set header
        self.set_headers(self.module.params['username'],
                         self.module.params['password'])

    def get_entry(self, url, key, value, list_name, entry_name):
        self.resp = self.get(url)
        if self.resp is None:
            return None
        elif "no item" in self.resp.text or "null" in self.resp.text:
            return None

        resp_body = self.strdict_to_dict(self.resp.text)
        data = resp_body[list_name][entry_name]
        if isinstance(data, list):
            for idx in range(0, len(data)):
                if data[idx][key] == value:
                    return data[idx]
        else:
            if data[key] == value:
                return data

        return None

    def set_url(self, cmd_type, cate, func, app_id, key):
        if cmd_type == CMD_SITE_TYPE or cmd_type == CMD_AMSS_TYPE:
            if key is None:
                return os.path.join(self.prefix_url, cmd_type, cate, func)
            return os.path.join(self.prefix_url, cmd_type, cate, func, key)
        else:
            # CMD_APP_TYPE
            if key is None:
                return os.path.join(self.prefix_url, cmd_type,
                                    app_id, cate, func)
            return os.path.join(self.prefix_url, cmd_type,
                                app_id, cate, func, key)

    def strdict_to_dict(self, str_dic):
        _str_dic = str_dic.replace('false', 'False')
        _str_dic = _str_dic.replace('true', 'True')
        _str_dic = _str_dic.replace('null', 'None')

        return ast.literal_eval(_str_dic)

    def set_result(self):
        if self.resp is None or "no item" in self.resp.text:
            self.result['message'] = 'Prest request Failed'
        else:
            resp_body = self.strdict_to_dict(self.resp.text)
            if 'header' in resp_body.keys():
                self.result['message'] = resp_body['header']['resultMessage']
                if resp_body['header']['resultCode'] > 0:
                    self.result['changed'] = True
                if resp_body['header']['resultCode'] < 0:
                    self.result['failed'] = True
            else:
                self.result['message'] = str(resp_body)
        self.module.exit_json(**self.result)

    def get_app_id(self):
        app_id = ''

        if self.module.params['app_name'].lower() == 'all':
            app_id = '0'
        else:
            url = self.set_url(CMD_SITE_TYPE, 'site-app', 'app-list',
                               None, None)
            app = self.get_entry(url, 'name', self.module.params['app_name'],
                                 'app_list', 'app_entry')
            if app is None:
                body = {'name': self.module.params['app_name']}
                self.resp = self.post(url, body)
                app = self.get_entry(url, 'name',
                                     self.module.params['app_name'],
                                     'app_list', 'app_entry')
            app_id = app['app_id']

        return app_id

    def validate_ip(self, ip):
        match = self.p.match(ip)
        if match is None:
            return False

        return True

    def validate_port(self, port):
        if port.isdigit() is False:
            return False

        n_port = int(port)
        if n_port < 1 or n_port > 65535:
            return False

        return True
