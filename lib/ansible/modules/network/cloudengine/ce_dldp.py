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
                    'version': '1.0'}

DOCUMENTATION = '''
---

module: ce_dldp
version_added: "2.3"
short_description: Manages global DLDP configuration.
description:
    - Manages global DLDP configuration.
extends_documentation_fragment: cloudengine
author:
    - Zhijin Zhou (@CloudEngine-Ansible)
notes:
    - The relevant configurations will be deleted if DLDP is disabled using enable=false.
    - When using auth_mode=none, it will restore the default DLDP authentication mode(By default,
      DLDP packets are not authenticated.).
    - By default, the working mode of DLDP is enhance, so you are advised to use work_mode=enhance to restore defualt
      DLDP working mode.
    - The default interval for sending Advertisement packets is 5 seconds, so you are advised to use time_interval=5 to
      restore defualt DLDP interval.
options:
    enable:
        description:
            - Set global DLDP enable state.
        required: false
        default: null
        choices: ['true', 'false']
    work_mode:
        description:
            - Set global DLDP work-mode
        required: false
        default: null
        choices: ['enhance', 'normal']
    time_internal:
        description:
            - Specifies the interval for sending Advertisement packets.
              The value is an integer ranging from 1 to 100, in seconds.
              The default interval for sending Advertisement packets is 5 seconds.
        required: false
        default: null
    auth_mode:
        description:
            - Specifies authentication algorithm of DLDP.
        required: false
        default: null
        choices: ['md5', 'simple', 'sha', 'hmac-sha256', 'none']
    auth_pwd:
        description:
            - Specifies authentication password.
              The value is a string of 1 to 16 case-sensitive plaintexts or 24/32/48/108/128 case-sensitive encrypted
              characters. The string excludes a question mark (?).
        required: false
        default: null
    reset:
        description:
            - Specify whether reset DLDP state of disabled interfaces.
        required: false
        default: null
        choices: ['true', 'false']
'''

EXAMPLES = '''
# Configure global DLDP enable state
- ce_dldp:
    enable: true
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"

# Configure DLDP work-mode and ensure global DLDP state is already enabled
- ce_dldp:
    enable: true
    work_mode: normal
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"

# Configure advertisement message time interval in seconds and ensure global DLDP state is already enabled
- ce_dldp:
    enable: true
    time_interval: 6
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"

# Configure a DLDP authentication mode and ensure global DLDP state is already enabled
- ce_dldp:
    enable: true
    auth_mode: md5
    auth_pwd: abc
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"

# Reset DLDP state of disabled interfaces and ensure global DLDP state is already enabled
- ce_dldp:
    enable: true
    reset: true
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
                "enable": "true",
                "reset": "true",
                "time_internal": "12",
                "work_mode": "normal"
            }
existing:
    description:
        - k/v pairs of existing global DLDP configration
    type: dict
    sample: {
                "enable": "false",
                "reset": "false",
                "time_internal": "5",
                "work_mode": "enhance"
            }
end_state:
    description: k/v pairs of global DLDP configration after module execution
    returned: always
    type: dict
    sample: {
                "enable": "true",
                "reset": "true",
                "time_internal": "12",
                "work_mode": "normal"
            }
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: [
                "dldp enable",
                "dldp work-mode normal",
                "dldp interval 12",
                "dldp reset"
            ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import sys
import copy
from xml.etree import ElementTree
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

CE_NC_ACTION_RESET_DLDP = """
<action>
  <dldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <resetDldp></resetDldp>
  </dldp>
</action>
"""

CE_NC_GET_GLOBAL_DLDP_CONFIG = """
<filter type="subtree">
  <dldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <dldpSys>
      <dldpEnable></dldpEnable>
      <dldpInterval></dldpInterval>
      <dldpWorkMode></dldpWorkMode>
      <dldpAuthMode></dldpAuthMode>
    </dldpSys>
  </dldp>
</filter>
"""

CE_NC_MERGE_DLDP_GLOBAL_CONFIG_HEAD = """
<config>
  <dldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <dldpSys operation="merge">
      <dldpEnable>%s</dldpEnable>
      <dldpInterval>%s</dldpInterval>
      <dldpWorkMode>%s</dldpWorkMode>
"""

CE_NC_MERGE_DLDP_GLOBAL_CONFIG_TAIL = """
    </dldpSys>
  </dldp>
</config>
"""


class Dldp(object):
    """Manage global dldp configration"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.netconf = None
        self.init_module()

        # dldp global configration info
        self.enable = self.module.params['enable'] or None
        self.work_mode = self.module.params['work_mode'] or None
        self.internal = self.module.params['time_interval'] or None
        self.reset = self.module.params['reset'] or None
        self.auth_mode = self.module.params['auth_mode']
        self.auth_pwd = self.module.params['auth_pwd']

        self.dldp_conf = dict()
        self.same_conf = False

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

    def check_config_if_same(self):
        """judge whether current config is the same as what we excepted"""

        if self.enable and self.enable != self.dldp_conf['dldpEnable']:
            return False

        if self.internal and self.internal != self.dldp_conf['dldpInterval']:
            return False

        work_mode = 'normal'
        if self.dldp_conf['dldpWorkMode'] == 'dldpEnhance':
            work_mode = 'enhance'
        if self.work_mode and self.work_mode != work_mode:
            return False

        if self.auth_mode:
            if self.auth_mode != 'none':
                return False

            if self.auth_mode == 'none' and self.dldp_conf['dldpAuthMode'] != 'dldpAuthNone':
                return False

        if self.reset and self.reset == 'true':
            return False

        return True

    def check_params(self):
        """Check all input params"""

        if (self.auth_mode and self.auth_mode != 'none' and not self.auth_pwd) \
                or (self.auth_pwd and not self.auth_mode):
            self.module.fail_json(msg="Error: auth_mode and auth_pwd must both exist or not exist.")

        if self.dldp_conf['dldpEnable'] == 'false' and not self.enable:
            if self.work_mode or self.reset or self.internal or self.auth_mode:
                self.module.fail_json(msg="Error: when DLDP is already disabled globally, "
                                      "work_mode, time_internal auth_mode and reset parameters are not "
                                      "expected to configure.")

        if self.enable == 'false' and (self.work_mode or self.internal or self.reset or self.auth_mode):
            self.module.fail_json(msg="Error: when using enable=false, work_mode, "
                                  "time_internal auth_mode and reset parameters are not expected "
                                  "to configure.")

        if self.internal:
            if not self.internal.isdigit():
                self.module.fail_json(
                    msg='Error: time_interval must be digit.')

            if int(self.internal) < 1 or int(self.internal) > 100:
                self.module.fail_json(
                    msg='Error: The value of time_internal should be between 1 and 100.')

        if self.auth_pwd:
            if '?' in self.auth_pwd:
                self.module.fail_json(
                    msg='Error: The auth_pwd string excludes a question mark (?).')
            if (len(self.auth_pwd) != 24) and (len(self.auth_pwd) != 32) and (len(self.auth_pwd) != 48) and \
                    (len(self.auth_pwd) != 108) and (len(self.auth_pwd) != 128):
                if (len(self.auth_pwd) < 1) or (len(self.auth_pwd) > 16):
                    self.module.fail_json(
                        msg='Error: The value is a string of 1 to 16 case-sensitive plaintexts or 24/32/48/108/128 '
                            'case-sensitive encrypted characters.')

    def init_module(self):
        """init module object"""
        self.module = NetworkModule(
            argument_spec=self.spec, supports_check_mode=True)

    def init_netconf(self):
        """init netconf interface"""

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
        """Check if response message is already succeed"""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def netconf_get_config(self, xml_str):
        """netconf get config"""

        try:
            con_obj = self.netconf.get_config(filter=xml_str)
        except RPCError:
            err = sys.exc_info()[1]
            self.module.fail_json(msg='Error: %s' %
                                  err.message.replace("\r\n", ""))

        return con_obj

    def netconf_set_config(self, xml_str, xml_name):
        """netconf set config"""

        try:
            con_obj = self.netconf.set_config(config=xml_str)
            self.check_response(con_obj, xml_name)
        except RPCError:
            err = sys.exc_info()[1]
            self.module.fail_json(msg='Error: %s' %
                                  err.message.replace("\r\n", ""))

        return con_obj

    def netconf_set_action(self, xml_str, xml_name):
        """netconf set action"""

        try:
            con_obj = self.netconf.execute_action(action=xml_str)
            self.check_response(con_obj, xml_name)
        except RPCError:
            err = sys.exc_info()[1]
            self.module.fail_json(msg='Error: %s' %
                                  err.message.replace("\r\n", ""))

        return con_obj

    def get_dldp_exist_config(self):
        """get current dldp existed configuration"""
        dldp_conf = dict()
        xml_str = CE_NC_GET_GLOBAL_DLDP_CONFIG
        con_obj = self.netconf_get_config(xml_str)
        if "<data/>" in con_obj.xml:
            return dldp_conf

        xml_str = con_obj.xml.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get global dldp info
        root = ElementTree.fromstring(xml_str)
        topo = root.find("data/dldp/dldpSys")
        if not topo:
            self.module.fail_json(
                msg="Error: Get current DLDP configration failed.")

        for eles in topo:
            if eles.tag in ["dldpEnable", "dldpInterval", "dldpWorkMode", "dldpAuthMode"]:
                dldp_conf[eles.tag] = eles.text

        return dldp_conf

    def config_global_dldp(self):
        """config global dldp"""
        if self.same_conf:
            return

        enable = self.enable
        if not self.enable:
            enable = self.dldp_conf['dldpEnable']

        internal = self.internal
        if not self.internal:
            internal = self.dldp_conf['dldpInterval']

        work_mode = self.work_mode
        if not self.work_mode:
            work_mode = self.dldp_conf['dldpWorkMode']

        if work_mode == 'enhance' or work_mode == 'dldpEnhance':
            work_mode = 'dldpEnhance'
        else:
            work_mode = 'dldpNormal'

        auth_mode = self.auth_mode
        if not self.auth_mode:
            auth_mode = self.dldp_conf['dldpAuthMode']
        if auth_mode == 'md5':
            auth_mode = 'dldpAuthMD5'
        elif auth_mode == 'simple':
            auth_mode = 'dldpAuthSimple'
        elif auth_mode == 'sha':
            auth_mode = 'dldpAuthSHA'
        elif auth_mode == 'hmac-sha256':
            auth_mode = 'dldpAuthHMAC-SHA256'
        elif auth_mode == 'none':
            auth_mode = 'dldpAuthNone'

        xml_str = CE_NC_MERGE_DLDP_GLOBAL_CONFIG_HEAD % (
            enable, internal, work_mode)
        if self.auth_mode:
            if self.auth_mode == 'none':
                xml_str += "<dldpAuthMode>dldpAuthNone</dldpAuthMode>"
            else:
                xml_str += "<dldpAuthMode>%s</dldpAuthMode>" % auth_mode
                xml_str += "<dldpPasswords>%s</dldpPasswords>" % self.auth_pwd

        xml_str += CE_NC_MERGE_DLDP_GLOBAL_CONFIG_TAIL
        self.netconf_set_config(xml_str, "MERGE_DLDP_GLOBAL_CONFIG")

        if self.reset == 'true':
            xml_str = CE_NC_ACTION_RESET_DLDP
            self.netconf_set_action(xml_str, "ACTION_RESET_DLDP")

        self.changed = True

    def get_existing(self):
        """get existing info"""
        dldp_conf = dict()

        dldp_conf['enable'] = self.dldp_conf.get('dldpEnable', None)
        dldp_conf['time_interval'] = self.dldp_conf.get('dldpInterval', None)
        work_mode = self.dldp_conf.get('dldpWorkMode', None)
        if work_mode == 'dldpEnhance':
            dldp_conf['work_mode'] = 'enhance'
        else:
            dldp_conf['work_mode'] = 'normal'

        auth_mode = self.dldp_conf.get('dldpAuthMode', None)
        if auth_mode == 'dldpAuthNone':
            dldp_conf['auth_mode'] = 'none'
        elif auth_mode == 'dldpAuthSimple':
            dldp_conf['auth_mode'] = 'simple'
        elif auth_mode == '?dldpAuthMD5':
            dldp_conf['auth_mode'] = 'md5'
        elif auth_mode == 'dldpAuthSHA':
            dldp_conf['auth_mode'] = 'sha'
        else:
            dldp_conf['auth_mode'] = 'hmac-sha256'

        dldp_conf['reset'] = 'false'

        self.existing = copy.deepcopy(dldp_conf)

    def get_proposed(self):
        """get proposed result"""

        self.proposed = dict(enable=self.enable, work_mode=self.work_mode,
                             time_interval=self.internal, reset=self.reset,
                             auth_mode=self.auth_mode, auth_pwd=self.auth_pwd)

    def get_update_cmd(self):
        """get update commands"""
        if self.same_conf:
            return

        if self.enable and self.enable != self.dldp_conf['dldpEnable']:
            if self.enable == 'true':
                self.updates_cmd.append("dldp enable")
            elif self.enable == 'false':
                self.updates_cmd.append("undo dldp enable")
                return

        work_mode = 'normal'
        if self.dldp_conf['dldpWorkMode'] == 'dldpEnhance':
            work_mode = 'enhance'
        if self.work_mode and self.work_mode != work_mode:
            if self.work_mode == 'enhance':
                self.updates_cmd.append("dldp work-mode enhance")
            else:
                self.updates_cmd.append("dldp work-mode normal")

        if self.internal and self.internal != self.dldp_conf['dldpInterval']:
            self.updates_cmd.append("dldp interval %s" % self.internal)

        if self.auth_mode:
            if self.auth_mode == 'none':
                self.updates_cmd.append("undo dldp authentication-mode")
            else:
                self.updates_cmd.append("dldp authentication-mode %s %s" % (self.auth_mode, self.auth_pwd))

        if self.reset and self.reset == 'true':
            self.updates_cmd.append('dldp reset')

    def get_end_state(self):
        """get end state info"""
        dldp_conf = dict()
        self.dldp_conf = self.get_dldp_exist_config()

        dldp_conf['enable'] = self.dldp_conf.get('dldpEnable', None)
        dldp_conf['time_interval'] = self.dldp_conf.get('dldpInterval', None)
        work_mode = self.dldp_conf.get('dldpWorkMode', None)
        if work_mode == 'dldpEnhance':
            dldp_conf['work_mode'] = 'enhance'
        else:
            dldp_conf['work_mode'] = 'normal'

        auth_mode = self.dldp_conf.get('dldpAuthMode', None)
        if auth_mode == 'dldpAuthNone':
            dldp_conf['auth_mode'] = 'none'
        elif auth_mode == 'dldpAuthSimple':
            dldp_conf['auth_mode'] = 'simple'
        elif auth_mode == '?dldpAuthMD5':
            dldp_conf['auth_mode'] = 'md5'
        elif auth_mode == 'dldpAuthSHA':
            dldp_conf['auth_mode'] = 'sha'
        else:
            dldp_conf['auth_mode'] = 'hmac-sha256'

        dldp_conf['reset'] = 'false'
        if self.reset == 'true':
            dldp_conf['reset'] = 'true'
        self.end_state = copy.deepcopy(dldp_conf)

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

        self.module.exit_json(**self.results)

    def work(self):
        """worker"""
        self.dldp_conf = self.get_dldp_exist_config()
        self.check_params()
        self.same_conf = self.check_config_if_same()
        self.get_existing()
        self.get_proposed()
        self.config_global_dldp()
        self.get_update_cmd()
        self.get_end_state()
        self.show_result()


def main():
    """main function entry"""
    argument_spec = dict(
        enable=dict(choices=['true', 'false'], type='str'),
        work_mode=dict(choices=['enhance', 'normal'], type='str'),
        time_interval=dict(type='str'),
        reset=dict(choices=['true', 'false'], type='str'),
        auth_mode=dict(choices=['md5', 'simple', 'sha', 'hmac-sha256', 'none'], type='str'),
        auth_pwd=dict(type='str', no_log=True),
    )

    dldp_obj = Dldp(argument_spec)
    dldp_obj.work()

if __name__ == '__main__':
    main()
