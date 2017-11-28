#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2017 Lenovo, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License

# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
# Module to run  CNOS restapi  to Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cnos_restapi

short_description:  Access to  RESTAPI's on switches running Lenovo CNOS.

version_added: "2.4"

description:
  - "Provides access to the RESTAPI's on the Lenovo CNOS switches.
     RESTAPI interface on CNOS fetches data and configures the
     Lenovo CNOS switches. "

options:

transport:
        description:
            - Transport layer used by the RESTAPI
               - http  plaintext communication over port 8090
               - https secured encrypted comminication
        required: true
        default: Null
    urlpath:
        description:
            - URL Path of the RESTAPI
        required:true
        default: Null
    method:
        description:
            - The HTTP method of the request
                 - GET is typically used for querying objects
                 - DELETE is typically used for deleting objects
                 - POST is typically used for creating/querying objects
                 - PUT is typically used for modifying objects
        required: true
        default: Null
    jsoninp:
        description:
            - input json dictionary
                 - Used by POST, PUT method to input request paramters
        required: false
        default: Null
author:
    - Arun Kumar (@arunktele)
'''

EXAMPLES = '''

- name: Configure BST feature using a JSON string
  cnos_restapi:
    host: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    outputfile: "./results/test_restapi_{{ inventory_hostname }}_output.txt"
    transport: https
    urlpath: /nos/api/cfg/telemetry/bst/feature
    method: PUT
    jsoninp: '{"collection-interval": 20, "send-async-reports": 1,
             "send-snapshot-on-trigger": 1, "trigger-rate-limit": 1,
              "async-full-report": 0, "trigger-rate-limit-interval": 11,
              "bst-enable": 1}'

- name: Fetch BST feature using a JSON string
  cnos_restapi:
    host: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    outputfile: "./results/test_restapi_{{ inventory_hostname }}_output.txt"
    transport: https
    urlpath: /nos/api/cfg/telemetry/bst/feature
    method: GET

- name: Fetch BST feature using a JSON string
  cnos_restapi:
    host: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    outputfile: "./results/test_restapi_{{ inventory_hostname }}_output.txt"
    transport: https
    urlpath: /nos/api/info/telemetry/bst/congestion-drop-counters
    method: POST
    jsoninp: '{"req-id" : 1, "request-type" : "port-drops", "request-params": {"interface-list": ["Ethernet1/1", "Ethernet1/2", "Ethernet1/3"]}}'

'''

RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: string
  sample: "RESTAPI PUT /nos/api/cfg/telemetry/bst/feature is successful"
'''

import json
import ast
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url


class RestModule(object):
    def __init__(self, params):
        self.transport = params['transport']
        self.ip = params['host']
        self.user = params['username']
        self.password = params['password']
        self.cookie = ''

        if (self.transport == 'http'):
            self.url = self.transport + '://' + self.ip + ':8090'
        elif (self.transport == 'https'):
            self.url = self.transport + '://' + self.ip

    def loginurl(self):
        # Step 1 - Login and get the auth cookie
        login_cookie = 0
        try:
            ret = open_url(self.url + '/nos/api/login/', method='GET',
                           use_proxy=False, timeout=10, validate_certs=False)
        except IOError as e:
            if hasattr(e, 'code'):
                if e.code == 401:
                    cookie = e.headers['Set-Cookie']
                    if 'auth_cookie' in cookie:
                        outp = cookie.split(" ")
                        login_cookie = 1

        if (login_cookie == 0):
            return 0
        # Step 2 - Login with valid cookie
        tmp_ckie = outp[0] + 'user=' + self.user + '; Max-Age=3600; Path=/'
        self.hdr = dict()
        self.hdr['Cookie'] = tmp_ckie
        ret = open_url(self.url + '/nos/api/login/', method='GET',
                       url_username=self.user, url_password=self.password,
                       use_proxy=False, timeout=10, validate_certs=False,
                       headers=self.hdr)
        if (ret.getcode() != 200):
            return 0
        mydict = ret.info()
        cookie = mydict['Set-Cookie']
        if 'auth_cookie' in cookie:
            outp = cookie.split(" ")
        self.hdr['Cookie'] = outp[0] + 'user=' + self.user
        self.hdr['Cookie'] = self.hdr['Cookie'] + '; Max-Age=3600; Path=/'
        self.hdr['Content-Type'] = 'application/json'
        return 1

    def logouturl(self):
        ret = open_url(self.url + '/nos/api/logout', method='GET',
                       headers=self.hdr, url_username=self.user,
                       url_password=self.password, use_proxy=False, timeout=10,
                       validate_certs=False)
        if (ret.getcode() == 200):
            return 1
        else:
            return 0

    def cb_method(self, url, method, jsoninp=None):
        data = " "
        if ((method == 'GET') or (method == 'DELETE')):
            ret = open_url((self.url + url), method='GET', headers=self.hdr,
                           url_username=self.user, url_password=self.password,
                           use_proxy=False, timeout=10, validate_certs=False)
        elif (method == 'PUT' or method == 'POST'):
            if jsoninp and isinstance(jsoninp, dict):
                ret = open_url((self.url + url), method=method,
                               data=json.dumps(jsoninp), headers=self.hdr,
                               url_username=self.user,
                               url_password=self.password, use_proxy=False,
                               timeout=10, validate_certs=False)
            else:
                return 0, "json input is not dictionary"
        else:
            return 0, "invalid data"
        if (ret.getcode() == 200):
            retn = 1
            if ((method == 'GET') or (method == 'POST')):
                data = ret.read()
        else:
            data = str(ret.getcode())
            retn = 0

        return retn, data


def main():
    #
    # Define parameters for restapi
    #
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            transport=dict(required=True),
            urlpath=dict(required=True),
            method=dict(required=False),
            jsoninp=dict(required=False),),
        supports_check_mode=False)

    json_data = None
    params = dict()
    params['transport'] = module.params['transport']
    if (params['transport'] not in ['http', 'https']):
        msg = " incorrect transport type"
        module.fail_json(msg=msg)
    params['host'] = module.params['host']
    params['username'] = module.params['username']
    params['password'] = module.params['password']
    output = ""
    outputfile = module.params['outputfile']
    file = open(outputfile, "a")
    cnos_rest = RestModule(params)
    ret_code = cnos_rest.loginurl()
    if (ret_code == 0):
        msg = "RESTAPI : Login Failed, RESTAPI server might be down"
        output = msg
    else:
        urlpath = module.params['urlpath']
        method = module.params['method']
        if (method not in ['GET', 'POST', 'PUT', 'DELETE']):
            msg = " incorrect method"
            module.fail_json(msg=msg)
        dictstr = module.params['jsoninp']
        if (dictstr):
            json_data = ast.literal_eval(dictstr)
        ret_code, data = cnos_rest.cb_method(urlpath, method=method,
                                             jsoninp=json_data)
        ret = cnos_rest.logouturl()
        msg = "RESTAPI " + method + " " + urlpath
        if (ret_code == 1):
            msg = msg + " is successful"
            output = msg
            if (data):
                output = "data = " + data
            file.write(output)
            file.close()
            module.exit_json(changed=True, msg=msg)
        else:
            msg = msg + " failed"
    output = msg
    file.write(output)
    file.close()
    module.fail_json(msg=msg)

if __name__ == '__main__':
    main()
