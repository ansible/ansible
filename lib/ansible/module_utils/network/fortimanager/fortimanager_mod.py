# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Benjamin Jolivot <bjolivot@gmail.com>, 2014
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import os
import time
import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import env_fallback

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False

fortios_argument_spec = dict(
    file_mode=dict(type='bool', default=False),
    config_file=dict(type='path'),
    host=dict(),
    username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    password=dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    timeout=dict(type='int', default=60),
    vdom=dict(type='str'),
    backup=dict(type='bool', default=False),
    backup_path=dict(type='path'),
    backup_filename=dict(type='str'),
)

fortios_required_if = [
    ['file_mode', False, ['host', 'username', 'password']],
    ['file_mode', True, ['config_file']],
    ['backup', True, ['backup_path']],
]

fortios_mutually_exclusive = [
    ['config_file', 'host'],
    ['config_file', 'username'],
    ['config_file', 'password']
]

fortios_error_codes = {
    '-3': "Object not found",
    '-61': "Command error"
}



class AnsibleFortiManager(object):
    def __init__(self, module, ip, username, passwd):
        self.ip = ip
        self.username = username
        self.passwd = passwd
        if not HAS_PYFMGR:
            module.fail_json(msg='Could not import the python library pyFMG required by this module')

        self.result = {
            'changed': False,
        }
        self.module = module



    def get(self, url, data):
        with FortiManager(self.ip, self.username, self.passwd, debug=True, disable_request_warnings=True) as fmgr_instance:
            response = fmgr_instance.get(url, **data)
            return response

    def set(self, url, data):
        with FortiManager(self.ip, self.username, self.passwd, debug=False, disable_request_warnings=True) as fmgr_instance:
            response = fmgr_instance.set(url, **data)
            return response

    def update(self, url, data):
        with FortiManager(self.ip, self.username, self.passwd, debug=True, disable_request_warnings=True) as fmgr_instance:
            response = fmgr_instance.update(url, **data)
            return response

    def delete(self, url, data):
        with FortiManager(self.ip, self.username, self.passwd, debug=False, disable_request_warnings=True) as fmgr_instance:
            response = fmgr_instance.delete(url, **data)
            return response

    def add(self, url, data):
        with FortiManager(self.ip, self.username, self.passwd, debug=True, disable_request_warnings=True) as fmgr_instance:
            response = fmgr_instance.add(url, **data)
            return response

    def execute(self, url, data):
        with FortiManager(self.ip, self.username, self.passwd, debug=False, disable_request_warnings=True) as fmgr_instance:
            response = fmgr_instance.execute(url, **data)
            return response

'''
    def _connect(self):
        if self.module.params['file_mode']:
            self.forti_device = FortiOS('')
        else:
            host = self.module.params['host']
            username = self.module.params['username']
            password = self.module.params['password']
            timeout = self.module.params['timeout']
            vdom = self.module.params['vdom']

            self.forti_device = FortiOS(host, username=username, password=password, timeout=timeout, vdom=vdom)

            try:
                self.forti_device.open()
            except Exception as e:
                self.module.fail_json(msg='Error connecting device. %s' % to_native(e),
                                      exception=traceback.format_exc())
'''