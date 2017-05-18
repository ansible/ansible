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

module: ce_dldp_interface
version_added: "2.3"
short_description: Manages interface DLDP configuration.
description:
    - Manages interface DLDP configuration.
extends_documentation_fragment: cloudengine
author:
    - Zhou Zhijin (@CloudEngine-Ansible)
notes:
    - If C(state=present, enable=false), interface DLDP enable will be turned off and
      related interface DLDP confuration will be cleared.
    - If C(state=absent), only local_mac is supported to configure.
options:
    interface:
        description:
            - Must be fully qualified interface name, i.e. GE1/0/1, 10GE1/0/1, 40GE1/0/22, 100GE1/0/1.
        required: true
    enable:
        description:
            - Set interface DLDP enable state.
        required: false
        default: null
        choices: ['true', 'false']
    mode_enable:
        description:
            - Set DLDP compatible-mode enable state.
        required: false
        default: null
        choices: ['true', 'false']
    local_mac:
        description:
            - Set the source MAC address for DLDP packets sent in the DLDP-compatible mode.
              The value of MAC address is in H-H-H format. H contains 1 to 4 hexadecimal digits.
        required: false
        default: null
    reset:
        description:
            - Specify whether reseting interface DLDP state.
        required: false
        default: null
        choices: ['true', 'false']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Configure interface DLDP enable state and ensure global dldp enable is turned on
- ce_dldp_interface: enable=true host=68.170.147.165 username=huawei password=huawei

# Configuire interface DLDP compatible-mode enable state  and ensure interface DLDP state is already enabled
- ce_dldp_interface: enable=true mode_enable=true host=68.170.147.165 username=huawei password=huawei

# Configuire the source MAC address for DLDP packets sent in the DLDP-compatible mode  and
  ensure interface DLDP state and compatible-mode enable state  is already enabled
- ce_dldp_interface: enable=true mode_enable=true local_mac=aa-aa-aa host=68.170.147.165 username=huawei password=huawei

# Reset DLDP state of specified interface and ensure interface DLDP state is already enabled
- ce_dldp_interface: enable=true reset=true host=68.170.147.165 username=huawei password=huawei

# Unconfigure interface DLDP local mac addreess when C(state=absent)
- ce_dldp_interface: state=absent local_mac=aa-aa-aa host=68.170.147.165 username=huawei password=huawei
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
                "enable": "true",
                "interface": "40GE2/0/22",
                "local_mac": "aa-aa-aa",
                "mode_enable": "true",
                "reset": "true"
            }
existing:
    description:
        - k/v pairs of existing interface DLDP configration
    type: dict
    sample: {
                "enable": "false",
                "interface": "40GE2/0/22",
                "local_mac": null,
                "mode_enable": null,
                "reset": "false"
            }
end_state:
    description: k/v pairs of interface DLDP configration after module execution
    returned: always
    type: dict
    sample: {
                "enable": "true",
                "interface": "40GE2/0/22",
                "local_mac": "00aa-00aa-00aa",
                "mode_enable": "true",
                "reset": "true"
            }
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: [
                "dldp enable",
                "dldp compatible-mode enable",
                "dldp compatible-mode local-mac aa-aa-aa",
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
import re
from xml.etree import ElementTree
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


CE_NC_ACTION_RESET_INTF_DLDP = """
<action>
  <dldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <resetIfDldp>
      <ifName>%s</ifName>
    </resetIfDldp>
  </dldp>
</action>
"""

CE_NC_GET_INTF_DLDP_CONFIG = """
<filter type="subtree">
  <dldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <dldpInterfaces>
      <dldpInterface>
        <ifName>%s</ifName>
        <dldpEnable></dldpEnable>
        <dldpCompatibleEnable></dldpCompatibleEnable>
        <dldpLocalMac></dldpLocalMac>
      </dldpInterface>
    </dldpInterfaces>
  </dldp>
</filter>
"""

CE_NC_MERGE_DLDP_INTF_CONFIG = """
<config>
  <dldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <dldpInterfaces>
      <dldpInterface operation="merge">
        <ifName>%s</ifName>
        <dldpEnable>%s</dldpEnable>
        <dldpCompatibleEnable>%s</dldpCompatibleEnable>
        <dldpLocalMac>%s</dldpLocalMac>
      </dldpInterface>
    </dldpInterfaces>
  </dldp>
</config>
"""

CE_NC_CREATE_DLDP_INTF_CONFIG = """
<config>
  <dldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <dldpInterfaces>
      <dldpInterface operation="create">
        <ifName>%s</ifName>
        <dldpEnable>%s</dldpEnable>
        <dldpCompatibleEnable>%s</dldpCompatibleEnable>
        <dldpLocalMac>%s</dldpLocalMac>
      </dldpInterface>
    </dldpInterfaces>
  </dldp>
</config>
"""

CE_NC_DELETE_DLDP_INTF_CONFIG = """
<config>
  <dldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <dldpInterfaces>
      <dldpInterface operation="delete">
        <ifName>%s</ifName>
      </dldpInterface>
    </dldpInterfaces>
  </dldp>
</config>
"""


def judge_is_mac_same(mac1, mac2):
    """judge whether two macs are the same"""

    if mac1 == mac2:
        return True

    list1 = re.findall(r'([0-9A-Fa-f]+)', mac1)
    list2 = re.findall(r'([0-9A-Fa-f]+)', mac2)
    if len(list1) != len(list2):
        return False

    for index, value in enumerate(list1, start=0):
        if value.lstrip('0').lower() != list2[index].lstrip('0').lower():
            return False

    return True


def get_interface_type(interface):
    """Gets the type of interface, such as 10GE, ETH-TRUNK, VLANIF..."""

    if interface is None:
        return None

    iftype = None

    if interface.upper().startswith('GE'):
        iftype = 'ge'
    elif interface.upper().startswith('10GE'):
        iftype = '10ge'
    elif interface.upper().startswith('25GE'):
        iftype = '25ge'
    elif interface.upper().startswith('4X10GE'):
        iftype = '4x10ge'
    elif interface.upper().startswith('40GE'):
        iftype = '40ge'
    elif interface.upper().startswith('100GE'):
        iftype = '100ge'
    elif interface.upper().startswith('VLANIF'):
        iftype = 'vlanif'
    elif interface.upper().startswith('LOOPBACK'):
        iftype = 'loopback'
    elif interface.upper().startswith('METH'):
        iftype = 'meth'
    elif interface.upper().startswith('ETH-TRUNK'):
        iftype = 'eth-trunk'
    elif interface.upper().startswith('VBDIF'):
        iftype = 'vbdif'
    elif interface.upper().startswith('NVE'):
        iftype = 'nve'
    elif interface.upper().startswith('TUNNEL'):
        iftype = 'tunnel'
    elif interface.upper().startswith('ETHERNET'):
        iftype = 'ethernet'
    elif interface.upper().startswith('FCOE-PORT'):
        iftype = 'fcoe-port'
    elif interface.upper().startswith('FABRIC-PORT'):
        iftype = 'fabric-port'
    elif interface.upper().startswith('STACK-PORT'):
        iftype = 'stack-Port'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    else:
        return None

    return iftype.lower()


class DldpInterface(object):
    """Manage interface dldp configration"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.netconf = None
        self.init_module()

        # dldp interface configration info
        self.interface = self.module.params['interface']
        self.enable = self.module.params['enable'] or None
        self.reset = self.module.params['reset'] or None
        self.mode_enable = self.module.params['mode_enable'] or None
        self.local_mac = self.module.params['local_mac'] or None
        self.state = self.module.params['state']

        self.dldp_intf_conf = dict()
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

        if self.state == 'absent':
            return False
        else:
            if self.enable and self.enable != self.dldp_intf_conf['dldpEnable']:
                return False

            if self.mode_enable and self.mode_enable != self.dldp_intf_conf['dldpCompatibleEnable']:
                return False

            if self.local_mac:
                flag = judge_is_mac_same(
                    self.local_mac, self.dldp_intf_conf['dldpLocalMac'])
                if not flag:
                    return False

            if self.reset and self.reset == 'true':
                return False
        return True

    def check_macaddr(self):
        """check mac-address whether valid"""

        valid_char = '0123456789abcdef-'
        mac = self.local_mac

        if len(mac) > 16:
            return False

        mac_list = re.findall(r'([0-9a-fA-F]+)', mac)
        if len(mac_list) != 3:
            return False

        if mac.count('-') != 2:
            return False

        for _, value in enumerate(mac, start=0):
            if value.lower() not in valid_char:
                return False

        return True

    def check_params(self):
        """Check all input params"""

        if not self.interface:
            self.module.fail_json(msg='Error: Interface name cannot be empty.')

        if self.interface:
            intf_type = get_interface_type(self.interface)
            if not intf_type:
                self.module.fail_json(
                    msg='Error: Interface name of %s '
                        'is error.' % self.interface)

        if (self.state == 'absent') and (self.reset or self.mode_enable or self.enable):
            self.module.fail_json(msg="Error: It's better to use state=present when "
                                  "configuring or unconfiguring enable, mode_enable "
                                  "or using reset flag. state=absent is just for "
                                  "when using local_mac param.")

        if self.state == 'absent' and not self.local_mac:
            self.module.fail_json(
                msg="Error: Please specify local_mac parameter.")

        if self.state == 'present':
            if (self.dldp_intf_conf['dldpEnable'] == 'false' and not self.enable and
                    (self.mode_enable or self.local_mac or self.reset)):
                self.module.fail_json(msg="Error: when DLDP is already disabled on this port, "
                                      "mode_enable, local_mac and reset parameters are not "
                                      "expected to configure.")

            if self.enable == 'false' and (self.mode_enable or self.local_mac or self.reset):
                self.module.fail_json(msg="Error: when using enable=false, "
                                      "mode_enable, local_mac and reset parameters "
                                      "are not expected to configure.")

        if self.local_mac and (self.mode_enable == 'false' or
                               (self.dldp_intf_conf['dldpCompatibleEnable'] == 'false'
                                and self.mode_enable != 'true')):
            self.module.fail_json(msg="Error: when DLDP compatible-mode is disabled on this port, "
                                      "Configuring local_mac is not allowed.")

        if self.local_mac:
            if not self.check_macaddr():
                self.module.fail_json(
                    msg="Error: local_mac has invalid value %s." % self.local_mac)

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
            self.module.fail_json(msg='Error: %s' % err.message.replace("\r\n", ""))

        return con_obj

    def netconf_set_config(self, xml_str, xml_name):
        """netconf set config"""

        try:
            con_obj = self.netconf.set_config(config=xml_str)
            self.check_response(con_obj, xml_name)
        except RPCError:
            err = sys.exc_info()[1]
            self.module.fail_json(msg='Error: %s' % err.message.replace("\r\n", ""))

        return con_obj

    def netconf_set_action(self, xml_str, xml_name):
        """netconf set action"""

        try:
            con_obj = self.netconf.execute_action(action=xml_str)
            self.check_response(con_obj, xml_name)
        except RPCError:
            err = sys.exc_info()[1]
            self.module.fail_json(msg='Error: %s' % err.message.replace("\r\n", ""))

        return con_obj

    def get_dldp_intf_exist_config(self):
        """get current dldp existed config"""

        dldp_conf = dict()
        xml_str = CE_NC_GET_INTF_DLDP_CONFIG % self.interface
        con_obj = self.netconf_get_config(xml_str)
        if "<data/>" in con_obj.xml:
            dldp_conf['dldpEnable'] = 'false'
            dldp_conf['dldpCompatibleEnable'] = ""
            dldp_conf['dldpLocalMac'] = ""
            return dldp_conf

        xml_str = con_obj.xml.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get global dldp info
        root = ElementTree.fromstring(xml_str)
        topo = root.find("data/dldp/dldpInterfaces/dldpInterface")
        if topo is None:
            self.module.fail_json(
                msg="Error: Get current DLDP configration failed.")
        for eles in topo:
            if eles.tag in ["dldpEnable", "dldpCompatibleEnable", "dldpLocalMac"]:
                if not eles.text:
                    dldp_conf[eles.tag] = ""
                else:
                    dldp_conf[eles.tag] = eles.text

        return dldp_conf

    def config_intf_dldp(self):
        """config global dldp"""

        if self.same_conf:
            return

        if self.state == "present":
            enable = self.enable
            if not self.enable:
                enable = self.dldp_intf_conf['dldpEnable']

            mode_enable = self.mode_enable
            if not self.mode_enable:
                mode_enable = self.dldp_intf_conf['dldpCompatibleEnable']

            local_mac = self.local_mac
            if not self.local_mac:
                local_mac = self.dldp_intf_conf['dldpLocalMac']

            if self.enable == 'false' and self.enable != self.dldp_intf_conf['dldpEnable']:
                xml_str = CE_NC_DELETE_DLDP_INTF_CONFIG % self.interface
                self.netconf_set_config(xml_str, "DELETE_DLDP_INTF_CONFIG")
            elif self.dldp_intf_conf['dldpEnable'] == 'false' and self.enable == 'true':
                xml_str = CE_NC_CREATE_DLDP_INTF_CONFIG % (
                    self.interface, self.enable, mode_enable, local_mac)
                self.netconf_set_config(xml_str, "CREATE_DLDP_INTF_CONFIG")
            elif self.dldp_intf_conf['dldpEnable'] == 'true':
                if mode_enable == 'false':
                    local_mac = ''
                xml_str = CE_NC_MERGE_DLDP_INTF_CONFIG % (
                    self.interface, enable, mode_enable, local_mac)
                self.netconf_set_config(xml_str, "MERGE_DLDP_INTF_CONFIG")

            if self.reset == 'true':
                xml_str = CE_NC_ACTION_RESET_INTF_DLDP % self.interface
                self.netconf_set_action(xml_str, "ACTION_RESET_INTF_DLDP")

            self.changed = True
        else:
            if self.local_mac and judge_is_mac_same(self.local_mac, self.dldp_intf_conf['dldpLocalMac']):
                xml_str = CE_NC_MERGE_DLDP_INTF_CONFIG % (self.interface, self.dldp_intf_conf[
                    'dldpEnable'], self.dldp_intf_conf['dldpCompatibleEnable'], '')
                self.netconf_set_config(
                    xml_str, "UNDO_DLDP_INTF_LOCAL_MAC_CONFIG")
                self.changed = True

    def get_existing(self):
        """get existing info"""

        dldp_conf = dict()

        dldp_conf['interface'] = self.interface
        dldp_conf['enable'] = self.dldp_intf_conf.get('dldpEnable', None)
        dldp_conf['mode_enable'] = self.dldp_intf_conf.get(
            'dldpCompatibleEnable', None)
        dldp_conf['local_mac'] = self.dldp_intf_conf.get('dldpLocalMac', None)
        dldp_conf['reset'] = 'false'

        self.existing = copy.deepcopy(dldp_conf)

    def get_proposed(self):
        """get proposed result """

        self.proposed = dict(interface=self.interface, enable=self.enable,
                             mode_enable=self.mode_enable, local_mac=self.local_mac,
                             reset=self.reset, state=self.state)

    def get_update_cmd(self):
        """get updatede commands"""

        if self.same_conf:
            return

        if self.state == "present":
            if self.enable and self.enable != self.dldp_intf_conf['dldpEnable']:
                if self.enable == 'true':
                    self.updates_cmd.append("dldp enable")
                elif self.enable == 'false':
                    self.updates_cmd.append("undo dldp enable")

            if self.mode_enable and self.mode_enable != self.dldp_intf_conf['dldpCompatibleEnable']:
                if self.mode_enable == 'true':
                    self.updates_cmd.append("dldp compatible-mode enable")
                else:
                    self.updates_cmd.append("undo dldp compatible-mode enable")

            if self.local_mac:
                flag = judge_is_mac_same(
                    self.local_mac, self.dldp_intf_conf['dldpLocalMac'])
                if not flag:
                    self.updates_cmd.append(
                        "dldp compatible-mode local-mac %s" % self.local_mac)

            if self.reset and self.reset == 'true':
                self.updates_cmd.append('dldp reset')
        else:
            if self.changed:
                self.updates_cmd.append("undo dldp compatible-mode local-mac")

    def get_end_state(self):
        """get end state info"""

        dldp_conf = dict()
        self.dldp_intf_conf = self.get_dldp_intf_exist_config()

        dldp_conf['interface'] = self.interface
        dldp_conf['enable'] = self.dldp_intf_conf.get('dldpEnable', None)
        dldp_conf['mode_enable'] = self.dldp_intf_conf.get(
            'dldpCompatibleEnable', None)
        dldp_conf['local_mac'] = self.dldp_intf_conf.get('dldpLocalMac', None)
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
        """excute task"""

        self.dldp_intf_conf = self.get_dldp_intf_exist_config()
        self.check_params()
        self.same_conf = self.check_config_if_same()
        self.get_existing()
        self.get_proposed()
        self.config_intf_dldp()
        self.get_update_cmd()
        self.get_end_state()
        self.show_result()


def main():
    """main function entry"""

    argument_spec = dict(
        interface=dict(required=True, type='str'),
        enable=dict(choices=['true', 'false'], type='str'),
        reset=dict(choices=['true', 'false'], type='str'),
        mode_enable=dict(choices=['true', 'false'], type='str'),
        local_mac=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    dldp_intf_obj = DldpInterface(argument_spec)
    dldp_intf_obj.work()

if __name__ == '__main__':
    main()
