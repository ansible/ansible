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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = '''
---

module: ce_ntp_auth
version_added: "2.2"
short_description: Manages NTP authentication.
description:
    - Manages NTP authentication.
extends_documentation_fragment: CloudEngine
author:
    - Zhou Zhijin (@CloudEngine-Ansible)
notes:
    - If C(state=absent), the module will attempt to remove the given key configuration.
      If a matching key configuration isn't found on the device, the module will fail.
    - If C(state=absent) and C(authentication=on), authentication will be turned on.
    - If C(state=absent) and C(authentication=off), authentication will be turned off.
options:
    key_id:
        description:
            - Authentication key identifier (numeric).
        required: true
    auth_pwd:
        description:
            - Plain text with length of 1 to 255, encrypted text with length of 20 to 392
        required: false
        default: null
    auth_mode:
        description:
            - Specify authentication algorithm md5 or hmac-sha256
        required: false
        default: null
        choices: ['hmac-sha256', 'md5']
    auth_type:
        description:
            - Whether the given password is in cleartext or
              has been encrypted. If in cleartext, the device
              will encrypt it before storing it.
        required: false
        default: encrypt
        choices: ['text', 'encrypt']
    trusted_key:
        description:
            - Whether the given key is required to be supplied by a time source
              for the device to synchronize to the time source.
        required: false
        default: false
        choices: ['true', 'false']
    authentication:
        description:
            - config ntp authentication enable
            - unconfig ntp authentication enable
        required: false
        default: null
        choices: ['enable', 'disable']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ntp authentication-keyid
- ce_ntp_auth:
    key_id: 32
    auth_mode: md5
    auth_pwd: 1111
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

# ntp authentication-keyid and ntp trusted authentication-keyid
- ce_ntp_auth:
    key_id: 32
    auth_mode: md5
    auth_pwd: 1111
    trusted_key:true
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

# ntp authentication-keyid and ntp authentication enable
- ce_ntp_auth:
    key_id: 32
    auth_mode: md5
    auth_pwd: 1111
    authentication:enable
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

# undo ntp authentication-keyid and undo ntp trusted authentication-keyid
- ce_ntp_auth:
    key_id: 32
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

# undo ntp authentication-keyid and undo ntp authentication enable
- ce_ntp_auth:
    key_id: 32
    authentication:enable
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
                "auth_type": "text",
                "authentication": "enable",
                "key_id": "32",
                "auth_pwd": "1111",
                "auth_mode": "md5"
                "trusted_key": "true",
                "state": "present"
            }
existing:
    description:
        - k/v pairs of existing ntp authentication
    type: dict
    sample: {
                "authentication": "off"
                "authentication-keyid": [
                    {
                        "auth_mode": "md5",
                        "key_id": "1",
                        "trusted_key": "false"
                    }
                ]
            }
end_state:
    description: k/v pairs of ntp authentication after module execution
    returned: always
    type: dict
    sample: {
                "authentication": "off"
                "authentication-keyid": [
                    {
                        "auth_mode": "md5",
                        "key_id": "1",
                        "trusted_key": "false"
                    },
                    {
                        "auth_mode": "md5",
                        "key_id": "32",
                        "trusted_key": "true"
                    }
                ]
            }
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: [
                "ntp authentication-key 32 md5 1111",
                "ntp trusted-key 32",
                "ntp authentication enable"
            ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import re
import datetime
import copy
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf
from ansible.module_utils.netcli import CommandRunner

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

CE_NC_GET_NTP_AUTH_CONFIG = """
<filter type="subtree">
  <ntp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ntpAuthKeyCfgs>
      <ntpAuthKeyCfg>
        <keyId>%s</keyId>
        <mode></mode>
        <keyVal></keyVal>
        <isReliable></isReliable>
      </ntpAuthKeyCfg>
    </ntpAuthKeyCfgs>
  </ntp>
</filter>
"""

CE_NC_GET_ALL_NTP_AUTH_CONFIG = """
<filter type="subtree">
  <ntp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ntpAuthKeyCfgs>
      <ntpAuthKeyCfg>
        <keyId></keyId>
        <mode></mode>
        <keyVal></keyVal>
        <isReliable></isReliable>
      </ntpAuthKeyCfg>
    </ntpAuthKeyCfgs>
  </ntp>
</filter>
"""

CE_NC_GET_NTP_AUTH_ENABLE = """
<filter type="subtree">
  <ntp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ntpSystemCfg>
      <isAuthEnable></isAuthEnable>
    </ntpSystemCfg>
  </ntp>
</filter>
"""

CE_NC_MERGE_NTP_AUTH_CONFIG = """
<config>
  <ntp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ntpAuthKeyCfgs>
      <ntpAuthKeyCfg operation="merge">
        <keyId>%s</keyId>
        <mode>%s</mode>
        <keyVal>%s</keyVal>
        <isReliable>%s</isReliable>
      </ntpAuthKeyCfg>
    </ntpAuthKeyCfgs>
  </ntp>
</config>
"""

CE_NC_MERGE_NTP_AUTH_ENABLE = """
<config>
  <ntp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ntpSystemCfg operation="merge">
      <isAuthEnable>%s</isAuthEnable>
    </ntpSystemCfg>
  </ntp>
</config>
"""

CE_NC_DELETE_NTP_AUTH_CONFIG = """
<config>
  <ntp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ntpAuthKeyCfgs>
      <ntpAuthKeyCfg operation="delete">
        <keyId>%s</keyId>
      </ntpAuthKeyCfg>
    </ntpAuthKeyCfgs>
  </ntp>
</config>
"""


class NtpAuth(object):
    """Manage ntp authentication"""

    def __init__(self, argument_spec):
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.spec = argument_spec
        self.module = None
        self.netconf = None
        self.init_module()

        # ntp_auth configration info
        self.key_id = self.module.params['key_id']
        self.password = self.module.params['auth_pwd'] or None
        self.auth_mode = self.module.params['auth_mode'] or None
        self.auth_type = self.module.params['auth_type']
        self.trusted_key = self.module.params['trusted_key']
        self.authentication = self.module.params['authentication'] or None
        self.state = self.module.params['state']
        self.check_params()

        self.ntp_auth_conf = dict()
        self.key_id_exist = False
        self.cur_trusted_key = 'false'

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.port = self.module.params['port']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = list()
        self.end_state = list()

        # init netconf connect
        self.init_netconf()

        self.get_ntp_auth_exist_config()

    def check_params(self):
        """Check all input params"""
        if not self.key_id.isdigit():
            self.module.fail_json(
                msg='Error: key_id is not digit.')

        if (long(self.key_id) < 1) or (long(self.key_id) > 4294967295):
            self.module.fail_json(
                msg='Error: The length of key_id is between 1 and 4294967295.')

        if self.state == "present":
            if (not self.password) or (not self.auth_mode):
                self.module.fail_json(
                    msg='Error: Please input password and auth_mode.')

            if (self.auth_type == 'encrypt') and\
                    ((len(self.password) < 20) or (len(self.password) > 392)):
                self.module.fail_json(
                    msg='Error: The length of encrypted password is between 20 and 392.')
            elif (self.auth_type == 'text') and\
                    ((len(self.password) < 1) or (len(self.password) > 255)):
                self.module.fail_json(
                    msg='Error: The length of text password is between 1 and 255.')

    def init_module(self):
        """ init module object"""
        self.module = NetworkModule(
            argument_spec=self.spec, supports_check_mode=True)

    def init_netconf(self):
        """ init netconf interface"""

        if HAS_NCCLIENT:
            self.netconf = get_netconf(host=self.host, port=self.port,
                                       username=self.username,
                                       password=self.module.params['password'])
            if not self.netconf:
                self.module.fail_json(msg='Error: netconf init failed')
        else:
            self.module.fail_json(
                msg='Error: No ncclient package, please install it.')

    def check_response(self, con_obj, xml_name):
        """Check if response message is already succeed."""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def netconf_get_config(self, xml_str):
        """ netconf get config """

        try:
            con_obj = self.netconf.get_config(filter=xml_str)
        except RPCError as err:
            self.module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def netconf_set_config(self, xml_str, xml_name):
        """ netconf set config """

        try:
            con_obj = self.netconf.set_config(config=xml_str)
            self.check_response(con_obj, xml_name)
        except RPCError as err:
            self.module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def get_ntp_auth_enable(self):
        """ get ntp authentication enable state"""
        xml_str = CE_NC_GET_NTP_AUTH_ENABLE
        con_obj = self.netconf_get_config(xml_str)

        # get ntp authentication enable
        auth_en = re.findall(
            r'.*<isAuthEnable>(.*)</isAuthEnable>.*', con_obj.xml)
        if auth_en:
            if auth_en[0] == 'true':
                self.ntp_auth_conf['authentication'] = 'enable'
            else:
                self.ntp_auth_conf['authentication'] = 'disable'

    def get_ntp_all_auth_keyid(self):
        """ get all authentication keyid info"""
        ntp_auth_conf = list()

        xml_str = CE_NC_GET_ALL_NTP_AUTH_CONFIG
        con_obj = self.netconf_get_config(xml_str)
        if "<data/>" in con_obj.xml:
            self.ntp_auth_conf["authentication-keyid"] = "None"
            return ntp_auth_conf

        # get ntp authentication config
        ntp_auth = re.findall(
            r'.*<keyId>(.*)</keyId>.*\s*<mode>(.*)</mode>.*\s*'
            r'<keyVal>(.*)</keyVal>.*\s*<isReliable>(.*)</isReliable>.*', con_obj.xml)

        for ntp_auth_num in ntp_auth:
            if ntp_auth_num[0] == self.key_id:
                self.key_id_exist = True
                self.cur_trusted_key = ntp_auth_num[3]

            ntp_auth_conf.append(dict(key_id=ntp_auth_num[0],
                                      auth_mode=ntp_auth_num[1].lower(),
                                      trusted_key=ntp_auth_num[3]))
        self.ntp_auth_conf["authentication-keyid"] = ntp_auth_conf

        return ntp_auth_conf

    def get_ntp_auth_exist_config(self):
        """get ntp authentication existed config"""
        self.get_ntp_auth_enable()
        self.get_ntp_all_auth_keyid()

    def config_ntp_auth_keyid(self):
        """config ntp authentication keyid """

        xml_str = CE_NC_MERGE_NTP_AUTH_CONFIG % (
            self.key_id, self.auth_mode.upper(), self.password, self.trusted_key)
        self.netconf_set_config(xml_str, "NTP_AUTH_KEYID_CONFIG")

    def config_ntp_auth_enable(self):
        """ config ntp authentication enable """

        if self.ntp_auth_conf['authentication'] != self.authentication:
            if self.authentication == 'enable':
                state = 'true'
            else:
                state = 'false'
            xml_str = CE_NC_MERGE_NTP_AUTH_ENABLE % state
            self.netconf_set_config(xml_str, "NTP_AUTH_ENABLE")

    def undo_config_ntp_auth_keyid(self):
        """undo ntp authentication key-id"""
        xml_str = CE_NC_DELETE_NTP_AUTH_CONFIG % self.key_id
        self.netconf_set_config(xml_str, "UNDO_NTP_AUTH_KEYID_CONFIG")

    def config_ntp_auth_keyid_by_cli(self):
        """ config ntp authentication keyid bye the way of CLI"""
        commands = list()
        cmd1 = {'output': None, 'command': 'system-view'}
        commands.append(cmd1)

        config_cli = "ntp authentication-keyid %s authentication-mode %s %s" % (
            self.key_id, self.auth_mode, self.password)
        cmd2 = {'output': None, 'command': ""}
        cmd2['command'] = config_cli
        commands.append(cmd2)

        cmd3 = {'output': None, 'command': ''}
        cmd3['command'] = 'commit'
        commands.append(cmd3)

        self.excute_command(commands)

    def config_ntp_auth(self):
        """config ntp authentication"""

        if self.state == "present":
            if self.auth_type == 'encrypt':
                self.config_ntp_auth_keyid()
            else:
                self.config_ntp_auth_keyid_by_cli()
        else:
            if not self.key_id_exist:
                self.module.fail_json(
                    msg='The Authentication-keyid does not exist.')
            self.undo_config_ntp_auth_keyid()

        if self.authentication:
            self.config_ntp_auth_enable()

        self.changed = True

    def get_existing(self):
        """get existing info"""
        self.existing = copy.deepcopy(self.ntp_auth_conf)

    def get_proposed(self):
        """get proposed result """
        auth_type = self.auth_type
        trusted_key = self.trusted_key
        if self.state == 'absent':
            auth_type = None
            trusted_key = None
        self.proposed = dict(key_id=self.key_id, auth_pwd=self.password,
                             auth_mode=self.auth_mode, auth_type=auth_type,
                             trusted_key=trusted_key, authentication=self.authentication,
                             state=self.state)

    def get_update_cmd(self):
        """get updatede commands"""
        cli_str = ""
        if self.state == "present":
            cli_str = "ntp authentication-keyid %s authentication-mode %s " % (
                self.key_id, self.auth_mode)
            if self.auth_type == 'encrypt':
                cli_str = "%s cipher %s" % (cli_str, self.password)
            else:
                cli_str = "%s %s" % (cli_str, self.password)
        else:
            cli_str = "undo ntp authentication-keyid %s" % self.key_id

        self.updates_cmd.append(cli_str)

        if self.authentication:
            cli_str = ""

            if self.ntp_auth_conf['authentication'] != self.authentication:
                if self.authentication == 'enable':
                    cli_str = "ntp authentication enable"
                else:
                    cli_str = "undo ntp authentication enable"

            if cli_str != "":
                self.updates_cmd.append(cli_str)

        cli_str = ""
        if self.state == "present":
            if self.trusted_key != self.cur_trusted_key:
                if self.trusted_key == 'true':
                    cli_str = "ntp trusted authentication-keyid %s" % self.key_id
                else:
                    cli_str = "undo ntp trusted authentication-keyid %s" % self.key_id
        else:
            cli_str = "undo ntp trusted authentication-keyid %s" % self.key_id

        if cli_str != "":
            self.updates_cmd.append(cli_str)

    def get_end_state(self):
        """get end state info"""
        self.ntp_auth_conf = dict()
        self.get_ntp_auth_exist_config()
        self.end_state = copy.deepcopy(self.ntp_auth_conf)

    def excute_command(self, commands):
        """ excute CLI commands"""

        runner = CommandRunner(self.module)
        for cmd in commands:
            try:
                runner.add_command(**cmd)
            except AddCommandError:
                exc = get_exception()
                self.module.fail_json(
                    msg='duplicate command detected: %s' % cmd)
        runner.retries = self.module.params['retries']
        runner.interval = self.module.params['interval']
        runner.match = self.module.params['match']

        try:
            runner.run()
        except FailedConditionsError:
            exc = get_exception()
            self.module.fail_json(
                msg=str(exc), failed_conditions=exc.failed_conditions)
        except FailedConditionalError:
            exc = get_exception()
            self.module.fail_json(
                msg=str(exc), failed_conditional=exc.failed_conditional)
        except NetworkError:
            exc = get_exception()
            self.module.fail_json(msg=str(exc), **exc.kwargs)

        for cmd in commands:
            try:
                output = runner.get_command(cmd['command'], cmd.get('output'))
            except ValueError:
                self.module.fail_json(
                    msg='command not executed due to check_mode, see warnings')
        return output

    def show_result(self):
        """show result"""
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.end_time = datetime.datetime.now()
        self.results['execute_time'] = str(self.end_time - self.start_time)

        self.module.exit_json(**self.results)

    def work(self):
        """excute task"""
        self.get_existing()
        self.get_proposed()
        self.get_update_cmd()

        self.config_ntp_auth()

        self.get_end_state()
        self.show_result()


def main():
    """  main function entry"""
    argument_spec = dict(
        key_id=dict(required=True, type='str'),
        auth_pwd=dict(type='str', no_log=True),
        auth_mode=dict(choices=['md5', 'hmac-sha256'], type='str'),
        auth_type=dict(choices=['text', 'encrypt'], default='encrypt'),
        trusted_key=dict(choices=['true', 'false'], default='false'),
        authentication=dict(choices=['enable', 'disable']),
        state=dict(choices=['absent', 'present'], default='present'),
        commands=dict(type='list', required=False),
        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['any', 'all']),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int'),
    )

    ntp_auth_obj = NtpAuth(argument_spec)
    ntp_auth_obj.work()

if __name__ == '__main__':
    main()
