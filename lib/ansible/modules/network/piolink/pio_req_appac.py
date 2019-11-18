#!/usr/bin/python
# -*- coding:utf-8 -*-

# Copyright: (c) 2019, Piolink Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: pio_req_appac
short_description: Configuring Application Access Control
description:
   - You can manage Application Access Control of the WEBFRONT-K.
version_added: '2.10'
requirements:
   - requests
options:
   host:
     description:
       - Enter the IPv4 address of the WEBFRONT-K.
     required: True
     type: str
   port:
     description:
       - Enter the port number of the WEBFRONT-K.
     required: True
     type: str
   username:
     description:
       - Enter the User ID of the WEBFRONT-K. The ID must have permissions for the WEBFRONT-K.
     required: True
     type: str
   password:
     description:
       - Enter the user's password.
     required: True
     type: str
   app_name:
     description:
       - Enter the application name. "Application" means the applications provided by the WEBFRONT-K.
     required: True
     type: str
   status:
     description:
       - Enter one of the following numbers to configure the state of Application Access Control.
       - 0: Disable
       - 1: Enable
     required: True
     default: 0
     choices: [0, 1]
     type: int
   block:
     description:
       - Enter one of the following numbers to allow or drop packets matching the Application Access Control policies.
       - 0: Allow
       - 1: Drop
     required: True
     default: 0
     choices: [0, 1]
     type: int
   log:
     description:
       - Enter one of the following numbers to collect log files or not for packets matching the Application Access Control policies.
       - 0: Disable
       - 1: Enable
     required: True
     default: 0
     choices: [0, 1]
     type: int
author: Seonil Kim(@sikim-piolink)
'''

EXAMPLES = r'''
- name: Set Req Appac Config
  pio_req_appac:
     host: 10.10.10.10
     port: 80
     username: admin
     password: secret
     app_name: pio_https
     status: 1
     block: 1
     log: 1
'''

RETURN = r'''
#
'''

import syslog

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.piolink.prest_utils import PrestUtils
from ansible.module_utils.network.piolink.prest_module import CMD_APP_TYPE

module_args = dict(
    host=dict(type='str', required=True),
    port=dict(type='str', required=True),
    username=dict(type='str', required=True),
    password=dict(type='str', required=True, no_log=True),
    app_name=dict(type='str', required=True),
    status=dict(type='int', required=True, choices=[0, 1]),
    block=dict(type='int', required=True, choices=[0, 1]),
    log=dict(type='int', required=True, choices=[0, 1]),
)


class PioReqAppac(PrestUtils):
    def __init__(self, module):
        super(PioReqAppac, self).__init__(module)

    def set_req_appac_status(self, app_id):
        url = self.set_url(CMD_APP_TYPE, 'req-appac', 'status', app_id, None)
        status = self.module.params['status']
        block = self.module.params['block']
        log = self.module.params['log']
        body = {'enable': status, 'block': block, 'log': log}
        self.resp = self.put(url, body)

    def run(self):
        if self.module.check_mode:
            return self.result

        app_id = self.get_app_id()
        self.set_req_appac_status(app_id)


def main():
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    req_appac = PioReqAppac(module)
    req_appac.init_args()
    req_appac.run()
    req_appac.set_result()


if __name__ == '__main__':
    main()
