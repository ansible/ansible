#!/usr/bin/python
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
# GNU General Public License for more detai++++++++ls.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'aaa'}

DOCUMENTATION = '''
---
module: ne_aaa_user
version_added: "2.6"
short_description: Manages local account configuration on HUAWEI router.
description:
    - The local account management functions.
author:

options:
    operation:
        description:
            - Ansible operation.
        required: true
        default: null
        choices: ['create', 'delete']
    localuser_username:
        description:
            - Name of a local user, it is not case sensitive.
        required: true
        default: null
    localuser_password:
        description:
            - Login password of a user, which is a string ranging from 1 to 128 characters for a plaintext password\
and 32 to 268 characters for a ciphertext password. The password can contain letters, numbers,\
and special characters. Chinese characters are not supported.
        required: true
        default: null
    passwordType:
        description:
            - Set a password type, which can be cipher or irreversible-cipher. Cipher passwords are encrypted\
and generated using the reversible algorithm, while irreversible-cipher passwords are encrypted\
and generated using the irreversible algorithm.
        required: false
        default: irreversible-cipher
        choices: ['cipher', 'irreversible-cipher']
    serviceTerminal:
        description:
            Login through a terminal.
        required: false
        default: false
    serviceTelnet:
        description:
            Login through TELNET.
        required: false
        default: false
    serviceFtp:
        description:
            Login through FTP.
        required: false
        default: false
    serviceSsh:
        description:
            Login through SSH.
        required: false
        default: false
    serviceSnmp:
        description:
            Login through SNMP.
        required: false
        default: false
    serviceQx:
        description:
            Login through QX.
        required: false
        default: false
    serviceMml:
        description:
            Login through MML.
        required: false
        default: false
    servicePpp:
        description:
            Login through PPP.
        required: false
        default: false
    userLevel:
        description:
            - Login level of a local user.
        required: false
        default: null
    userGroupName:
        description:
            - Name of a user group, it is not case sensitive.
        required: false
        default: null
    ftpDir:
        description:
            - FTP user directory.
        required: false
        default: null
    userState:
        description:
            - Activated state of a user.
        required: false
        default: active
        choices: ['block', 'active']
    failedTimes:
        description:
            - When user continuous authen failed times reach the limit, the user is locked.
        required: false
        default: 3
    interval:
        description:
            - Set a user lockout period (in minutes). If a user is locked due to consecutive authentication failures,\
the user is automatically unlocked after the set period expires.
        required: false
        default: 5
     maxAccessNum:
        description:
            - The local user max access number.
        required: false
        default: null
    passwordExpireInDays:
        description:
            - The passowrd will expire in the special days.
        required: false
        default: null
    agingInDays:
        description:
            -The user will age if not online in the special days.
        required: false
        default: null
'''

EXAMPLES = '''

- name: aaa local user test
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    yang:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      operation: create or delete

  tasks:

  - name: "Create a local user with ssh access type"
    aaa_user:
      operation: create
      localuser_username: root123
      localuser_password: Root@123
      serviceSsh: true
      userLevel: 3
      ftpDir: cfcard:


  - name: "delete a local user"
    snmp_trap:
      operation: delete
      localuser_username: root123

  - name: "Create a local user with ppp access type"
    aaa_user:
      operation: create
      localuser_username: root123
      localuser_password: Root@123
      passwordType: cipher
      servicePpp: true
'''

RETURN = '''
response:
    description: check to see config result
    returned: always
    type: result string
    sample: ok
'''


AAA_LOCAL_USER_CFG_HEAD = """
<config>
  <aaa xmlns="http://www.huawei.com/netconf/vrp/huawei-aaa">
    <lam>
      <users>
        <user>
"""

AAA_LOCAL_USER_CONF_TAIL = """
        </user>
      </users>
    </lam>
  </aaa>
</config>
"""

AAA_LOCAL_USER_DELCFG_HEAD = """
<config>
  <aaa xmlns="http://www.huawei.com/netconf/vrp/huawei-aaa">
    <lam>
      <users>
        <user nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

LOCAL_USER_NAME = """
    <userName>%s</userName>"""

LOCAL_USER_STATE = """
    <userState>%s</userState>"""

LOCAL_USER_SERVICE_TERMINAL = """
    <serviceTerminal>%s</serviceTerminal>"""

LOCAL_USER_SERVICE_TELNET = """
    <serviceTelnet>%s</serviceTelnet>"""

LOCAL_USER_SERVICE_FTP = """
    <serviceFtp>%s</serviceFtp>"""

LOCAL_USER_SERVICE_PPP = """
    <servicePpp>%s</servicePpp>"""

LOCAL_USER_SERVICE_SSH = """
    <serviceSsh>%s</serviceSsh>"""

LOCAL_USER_SERVICE_QX = """
    <serviceQx>%s</serviceQx>"""

LOCAL_USER_SERVICE_SNMP = """
    <serviceSnmp>%s</serviceSnmp>"""

LOCAL_USER_SERVICE_MML = """
    <serviceMml>%s</serviceMml>"""

LOCAL_USER_LEVEL = """
    <userLevel>%d</userLevel>"""

LOCAL_USER_PWD = """
    <password>%s</password>"""

LOCAL_USER_FAILED_TIMES = """
    <failedTimes>%d</failedTimes>"""

LOCAL_USER_INTERVAL = """
    <interval>%d</interval>"""

LOCAL_USER_PWD_TYPE = """
    <passwordType>%s</passwordType>"""

LOCAL_USER_UG_NAME = """
    <userGroupName>%s</userGroupName>"""

LOCAL_USER_MAX_ACCESS_NUM = """
    <maxAccessNum>%s</maxAccessNum>"""

LOCAL_USER_PWD_EXPIRE_IN_DAYS = """
    <passwordExpireInDays>%s</passwordExpireInDays>"""

LOCAL_USER_AGING_IN_DAYS = """
    <agingInDays>%s</agingInDays>"""

LOCAL_USER_FTP_DIR = """
    <ftpDir>%s</ftpDir>"""


def config_params_func(arg):
    if arg or arg == '':
        return True
    return False


aaa_local_user_argument_spec = {
    'localuser_username': dict(type='str'),
    'localuser_password': dict(type='str', no_log=True),
    'passwordType': dict(choices=['cipher', 'irreversible-cipher']),
    'serviceTerminal': dict(choices=['true', 'false']),
    'serviceTelnet': dict(choices=['true', 'false']),
    'serviceFtp': dict(choices=['true', 'false']),
    'serviceSsh': dict(choices=['true', 'false']),
    'serviceSnmp': dict(choices=['true', 'false']),
    'serviceQx': dict(choices=['true', 'false']),
    'serviceMml': dict(choices=['true', 'false']),
    'servicePpp': dict(choices=['true', 'false']),
    'userLevel': dict(type='int'),
    'userGroupName': dict(type='str'),
    'ftpDir': dict(type='str'),
    'userState': dict(choices=['block', 'active']),
    'failedTimes': dict(type='int'),
    'interval': dict(type='int'),
    'maxAccessNum': dict(type='int'),
    'passwordExpireInDays': dict(type='int'),
    'agingInDays': dict(type='int')
}


class LocalUser(object):
    """
     local user management
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.localuser_username = self.module.params['localuser_username']
        self.localuser_password = self.module.params['localuser_password']
        self.passwordType = self.module.params['passwordType']
        self.serviceTerminal = self.module.params['serviceTerminal']
        self.serviceTelnet = self.module.params['serviceTelnet']
        self.serviceFtp = self.module.params['serviceFtp']
        self.serviceSsh = self.module.params['serviceSsh']
        self.serviceSnmp = self.module.params['serviceSnmp']
        self.serviceQx = self.module.params['serviceQx']
        self.serviceMml = self.module.params['serviceMml']
        self.servicePpp = self.module.params['servicePpp']
        self.userLevel = self.module.params['userLevel']
        self.userGroupName = self.module.params['userGroupName']
        self.ftpDir = self.module.params['ftpDir']
        self.userState = self.module.params['userState']
        self.failedTimes = self.module.params['failedTimes']
        self.interval = self.module.params['interval']
        self.maxAccessNum = self.module.params['maxAccessNum']
        self.passwordExpireInDays = self.module.params['passwordExpireInDays']
        self.agingInDays = self.module.params['agingInDays']
        self.results = dict()
        self.results['response'] = []

    def local_user_config_str(self):
        local_user_cfg_str = ''

        if self.operation == 'create':
            local_user_cfg_str += AAA_LOCAL_USER_CFG_HEAD
            if config_params_func(self.localuser_username):
                local_user_cfg_str += LOCAL_USER_NAME % self.localuser_username

            if config_params_func(self.localuser_password):
                local_user_cfg_str += LOCAL_USER_PWD % self.localuser_password

            if config_params_func(self.serviceTerminal):
                local_user_cfg_str += LOCAL_USER_SERVICE_TERMINAL % self.serviceTerminal

            if config_params_func(self.serviceTelnet):
                local_user_cfg_str += LOCAL_USER_SERVICE_TELNET % self.serviceTelnet

            if config_params_func(self.serviceFtp):
                local_user_cfg_str += LOCAL_USER_SERVICE_FTP % self.serviceFtp

            if config_params_func(self.serviceSnmp):
                local_user_cfg_str += LOCAL_USER_SERVICE_SNMP % self.serviceSnmp

            if config_params_func(self.serviceQx):
                local_user_cfg_str += LOCAL_USER_SERVICE_QX % self.serviceQx

            if config_params_func(self.serviceMml):
                local_user_cfg_str += LOCAL_USER_SERVICE_MML % self.serviceMml

            if config_params_func(self.servicePpp):
                local_user_cfg_str += LOCAL_USER_SERVICE_PPP % self.servicePpp

            if config_params_func(self.userLevel):
                local_user_cfg_str += LOCAL_USER_LEVEL % self.userLevel

            if config_params_func(self.ftpDir):
                local_user_cfg_str += LOCAL_USER_FTP_DIR % self.ftpDir

            if config_params_func(self.failedTimes):
                local_user_cfg_str += LOCAL_USER_FAILED_TIMES % self.failedTimes

            if config_params_func(self.interval):
                local_user_cfg_str += LOCAL_USER_INTERVAL % self.interval

            if config_params_func(self.passwordType):
                local_user_cfg_str += LOCAL_USER_PWD_TYPE % self.passwordType

            if config_params_func(self.userGroupName):
                local_user_cfg_str += LOCAL_USER_UG_NAME % self.userGroupName

            if config_params_func(self.maxAccessNum):
                local_user_cfg_str += LOCAL_USER_MAX_ACCESS_NUM % self.maxAccessNum

            if config_params_func(self.passwordExpireInDays):
                local_user_cfg_str += LOCAL_USER_PWD_EXPIRE_IN_DAYS % self.passwordExpireInDays

            if config_params_func(self.agingInDays):
                local_user_cfg_str += LOCAL_USER_AGING_IN_DAYS % self.agingInDays

        if self.operation == 'delete':
            local_user_cfg_str += AAA_LOCAL_USER_DELCFG_HEAD
            if config_params_func(self.localuser_username):
                local_user_cfg_str += LOCAL_USER_NAME % self.localuser_username

        local_user_cfg_str += AAA_LOCAL_USER_CONF_TAIL
        return local_user_cfg_str

    def set_local_user(self):
        if config_params_func(self.localuser_username):
            return set_nc_config(self.module, self.local_user_config_str())
        else:
            return "<ok/>"


def local_user_config(argument_spec):
    """ local user config """

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    local_user_obj = LocalUser(argument_spec)
    if not local_user_obj:
        module.fail_json(msg='Error: Init AAA local user module failed.')

    return local_user_obj.set_local_user()


def main():
    """ main function """

    argument_spec = dict(
        operation=dict(choices=['create', 'delete'], default='create')
    )
    argument_spec.update(ne_argument_spec)
    argument_spec.update(aaa_local_user_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    results = dict()
    result = local_user_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    results['response'] = "ok"
    results['changed'] = True
    module.exit_json(**results)


if __name__ == '__main__':
    main()
