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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---

module: ce_ntp_auth
version_added: "2.4"
short_description: Manages NTP authentication configuration on HUAWEI CloudEngine switches.
description:
    - Manages NTP authentication configuration on HUAWEI CloudEngine switches.
author:
    - Zhijin Zhou (@CloudEngine-Ansible)
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
            - Plain text with length of 1 to 255, encrypted text with length of 20 to 392.
        required: false
        default: null
    auth_mode:
        description:
            - Specify authentication algorithm.
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
        default: 'disable'
        choices: ['enable', 'disable']
    authentication:
        description:
            - Configure ntp authentication enable or unconfigure ntp authentication enable.
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
- name: NTP AUTH test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: "Configure ntp authentication key-id"
    ce_ntp_auth:
      key_id: 32
      auth_mode: md5
      auth_pwd: 11111111111111111111111
      provider: "{{ cli }}"

  - name: "Configure ntp authentication key-id and trusted authentication keyid"
    ce_ntp_auth:
      key_id: 32
      auth_mode: md5
      auth_pwd: 11111111111111111111111
      trusted_key: enable
      provider: "{{ cli }}"

  - name: "Configure ntp authentication key-id and authentication enable"
    ce_ntp_auth:
      key_id: 32
      auth_mode: md5
      auth_pwd: 11111111111111111111111
      authentication: enable
      provider: "{{ cli }}"

  - name: "Unconfigure ntp authentication key-id and trusted authentication keyid"
    ce_ntp_auth:
      key_id: 32
      state: absent
      provider: "{{ cli }}"

  - name: "Unconfigure ntp authentication key-id and authentication enable"
    ce_ntp_auth:
      key_id: 32
      authentication: enable
      state: absent
      provider: "{{ cli }}"
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
                "auth_mode": "md5",
                "trusted_key": "enable",
                "state": "present"
            }
existing:
    description: k/v pairs of existing ntp authentication
    returned: always
    type: dict
    sample: {
                "authentication": "off",
                "authentication-keyid": [
                    {
                        "auth_mode": "md5",
                        "key_id": "1",
                        "trusted_key": "disable"
                    }
                ]
            }
end_state:
    description: k/v pairs of ntp authentication after module execution
    returned: always
    type: dict
    sample: {
                "authentication": "off",
                "authentication-keyid": [
                    {
                        "auth_mode": "md5",
                        "key_id": "1",
                        "trusted_key": "disable"
                    },
                    {
                        "auth_mode": "md5",
                        "key_id": "32",
                        "trusted_key": "enable"
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

import copy
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ce import ce_argument_spec, load_config, get_nc_config, set_nc_config

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
        self.spec = argument_spec
        self.module = None
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
        self.cur_trusted_key = 'disable'

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = list()
        self.end_state = list()

        self.get_ntp_auth_exist_config()

    def check_params(self):
        """Check all input params"""

        if not self.key_id.isdigit():
            self.module.fail_json(
                msg='Error: key_id is not digit.')

        if (int(self.key_id) < 1) or (int(self.key_id) > 4294967295):
            self.module.fail_json(
                msg='Error: The length of key_id is between 1 and 4294967295.')

        if self.state == "present":
            if (self.auth_type == 'encrypt') and\
                    ((len(self.password) < 20) or (len(self.password) > 392)):
                self.module.fail_json(
                    msg='Error: The length of encrypted password is between 20 and 392.')
            elif (self.auth_type == 'text') and\
                    ((len(self.password) < 1) or (len(self.password) > 255)):
                self.module.fail_json(
                    msg='Error: The length of text password is between 1 and 255.')

    def init_module(self):
        """Init module object"""

        required_if = [("state", "present", ("password", "auth_mode"))]
        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_if=required_if,
            supports_check_mode=True
        )

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ntp_auth_enable(self):
        """Get ntp authentication enable state"""

        xml_str = CE_NC_GET_NTP_AUTH_ENABLE
        con_obj = get_nc_config(self.module, xml_str)
        if "<data/>" in con_obj:
            return

        # get ntp authentication enable
        auth_en = re.findall(
            r'.*<isAuthEnable>(.*)</isAuthEnable>.*', con_obj)
        if auth_en:
            if auth_en[0] == 'true':
                self.ntp_auth_conf['authentication'] = 'enable'
            else:
                self.ntp_auth_conf['authentication'] = 'disable'

    def get_ntp_all_auth_keyid(self):
        """Get all authentication keyid info"""

        ntp_auth_conf = list()

        xml_str = CE_NC_GET_ALL_NTP_AUTH_CONFIG
        con_obj = get_nc_config(self.module, xml_str)
        if "<data/>" in con_obj:
            self.ntp_auth_conf["authentication-keyid"] = "None"
            return ntp_auth_conf

        # get ntp authentication config
        ntp_auth = re.findall(
            r'.*<keyId>(.*)</keyId>.*\s*<mode>(.*)</mode>.*\s*'
            r'<keyVal>(.*)</keyVal>.*\s*<isReliable>(.*)</isReliable>.*', con_obj)

        for ntp_auth_num in ntp_auth:
            if ntp_auth_num[0] == self.key_id:
                self.key_id_exist = True
                if ntp_auth_num[3] == 'true':
                    self.cur_trusted_key = 'enable'
                else:
                    self.cur_trusted_key = 'disable'

            if ntp_auth_num[3] == 'true':
                trusted_key = 'enable'
            else:
                trusted_key = 'disable'
            ntp_auth_conf.append(dict(key_id=ntp_auth_num[0],
                                      auth_mode=ntp_auth_num[1].lower(),
                                      trusted_key=trusted_key))
        self.ntp_auth_conf["authentication-keyid"] = ntp_auth_conf

        return ntp_auth_conf

    def get_ntp_auth_exist_config(self):
        """Get ntp authentication existed configure"""

        self.get_ntp_auth_enable()
        self.get_ntp_all_auth_keyid()

    def config_ntp_auth_keyid(self):
        """Config ntp authentication keyid"""

        if self.trusted_key == 'enable':
            trusted_key = 'true'
        else:
            trusted_key = 'false'
        xml_str = CE_NC_MERGE_NTP_AUTH_CONFIG % (
            self.key_id, self.auth_mode.upper(), self.password, trusted_key)
        ret_xml = set_nc_config(self.module, xml_str)
        self.check_response(ret_xml, "NTP_AUTH_KEYID_CONFIG")

    def config_ntp_auth_enable(self):
        """Config ntp authentication enable"""

        if self.ntp_auth_conf['authentication'] != self.authentication:
            if self.authentication == 'enable':
                state = 'true'
            else:
                state = 'false'
            xml_str = CE_NC_MERGE_NTP_AUTH_ENABLE % state
            ret_xml = set_nc_config(self.module, xml_str)
            self.check_response(ret_xml, "NTP_AUTH_ENABLE")

    def undo_config_ntp_auth_keyid(self):
        """Undo ntp authentication key-id"""

        xml_str = CE_NC_DELETE_NTP_AUTH_CONFIG % self.key_id
        ret_xml = set_nc_config(self.module, xml_str)
        self.check_response(ret_xml, "UNDO_NTP_AUTH_KEYID_CONFIG")

    def cli_load_config(self, commands):
        """Load config by cli"""

        if not self.module.check_mode:
            load_config(self.module, commands)

    def config_ntp_auth_keyid_by_cli(self):
        """Config ntp authentication keyid bye the way of CLI"""

        commands = list()
        config_cli = "ntp authentication-keyid %s authentication-mode %s %s" % (
            self.key_id, self.auth_mode, self.password)
        commands.append(config_cli)
        self.cli_load_config(commands)

    def config_ntp_auth(self):
        """Config ntp authentication"""

        if self.state == "present":
            if self.auth_type == 'encrypt':
                self.config_ntp_auth_keyid()
            else:
                self.config_ntp_auth_keyid_by_cli()
        else:
            if not self.key_id_exist:
                self.module.fail_json(
                    msg='Error: The Authentication-keyid does not exist.')
            self.undo_config_ntp_auth_keyid()

        if self.authentication:
            self.config_ntp_auth_enable()

        self.changed = True

    def get_existing(self):
        """Get existing info"""

        self.existing = copy.deepcopy(self.ntp_auth_conf)

    def get_proposed(self):
        """Get proposed result"""

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
        """Get updated commands"""

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
                if self.trusted_key == 'enable':
                    cli_str = "ntp trusted authentication-keyid %s" % self.key_id
                else:
                    cli_str = "undo ntp trusted authentication-keyid %s" % self.key_id
        else:
            cli_str = "undo ntp trusted authentication-keyid %s" % self.key_id

        if cli_str != "":
            self.updates_cmd.append(cli_str)

    def get_end_state(self):
        """Get end state info"""

        self.ntp_auth_conf = dict()
        self.get_ntp_auth_exist_config()
        self.end_state = copy.deepcopy(self.ntp_auth_conf)

    def show_result(self):
        """Show result"""

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)

    def work(self):
        """Excute task"""

        self.get_existing()
        self.get_proposed()
        self.get_update_cmd()

        self.config_ntp_auth()

        self.get_end_state()
        self.show_result()


def main():
    """Main function entry"""

    argument_spec = dict(
        key_id=dict(required=True, type='str'),
        auth_pwd=dict(type='str', no_log=True),
        auth_mode=dict(choices=['md5', 'hmac-sha256'], type='str'),
        auth_type=dict(choices=['text', 'encrypt'], default='encrypt'),
        trusted_key=dict(choices=['enable', 'disable'], default='disable'),
        authentication=dict(choices=['enable', 'disable']),
        state=dict(choices=['absent', 'present'], default='present'),
    )
    argument_spec.update(ce_argument_spec)
    ntp_auth_obj = NtpAuth(argument_spec)
    ntp_auth_obj.work()


if __name__ == '__main__':
    main()
