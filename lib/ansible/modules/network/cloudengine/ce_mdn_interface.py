#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---

module: ce_mdn_interface
version_added: "2.10"
short_description: Manages MDN configuration on HUAWEI CloudEngine switches.
description:
    - Manages MDN configuration on HUAWEI CloudEngine switches.
author: xuxiaowei0512 (@CloudEngine-Ansible)
options:
  lldpenable:
    description:
      - Set global LLDP enable state.
    type: str
    choices: ['enabled', 'disabled']
  mdnstatus:
    description:
      - Set interface MDN enable state.
    type: str
    choices: ['rxOnly', 'disabled']
  ifname:
    description:
      - Interface name.
    type: str
  state:
    description:
      - Manage the state of the resource.
    default: present
    type: str
    choices: ['present','absent']
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - This module works with connection C(netconf).
'''

EXAMPLES = '''
  - name: "Configure global LLDP enable state"
    ce_mdn_interface:
      lldpenable: enabled

  - name: "Configure interface MDN enable state"
    ce_mdn_interface:
      ifname: 10GE1/0/1
      mdnstatus: rxOnly
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
                "lldpenable": "enabled",
                "ifname": "10GE1/0/1",
                "mdnstatus": "rxOnly",
                "state":"present"
            }
existing:
    description: k/v pairs of existing global LLDP configration
    returned: always
    type: dict
    sample: {
                "lldpenable": "enabled",
                "ifname": "10GE1/0/1",
                "mdnstatus": "disabled"
            }
end_state:
    description: k/v pairs of global LLDP configration after module execution
    returned: always
    type: dict
    sample: {
                "lldpenable": "enabled",
                "ifname": "10GE1/0/1",
                "mdnstatus": "rxOnly"
            }
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: [
                "interface 10ge 1/0/1",
                "lldp mdn enable",
            ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import copy
import re
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import set_nc_config, get_nc_config, execute_nc_action

CE_NC_GET_GLOBAL_LLDPENABLE_CONFIG = """
<filter type="subtree">
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpSys>
      <lldpEnable></lldpEnable>
    </lldpSys>
  </lldp>
</filter>
"""

CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG = """
<config>
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpSys operation="merge">
      <lldpEnable>%s</lldpEnable>
    </lldpSys>
  </lldp>
</config>
"""

CE_NC_GET_INTERFACE_MDNENABLE_CONFIG = """
<filter type="subtree">
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <mdnInterfaces>
      <mdnInterface>
        <ifName></ifName>
        <mdnStatus></mdnStatus>
      </mdnInterface>
    </mdnInterfaces>
  </lldp>
</filter>
"""

CE_NC_MERGE_INTERFACE_MDNENABLE_CONFIG = """
<config>
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <mdnInterfaces>
      <mdnInterface operation="merge">
        <ifName>%s</ifName>
        <mdnStatus>%s</mdnStatus>
      </mdnInterface>
    </mdnInterfaces>
  </lldp>
</config>
"""


def get_interface_type(interface):
    """Gets the type of interface, such as 10GE, ..."""

    if interface is None:
        return None

    iftype = None

    if interface.upper().startswith('GE'):
        iftype = 'ge'
    elif interface.upper().startswith('10GE'):
        iftype = '10ge'
    elif interface.upper().startswith('25GE'):
        iftype = '25ge'
    elif interface.upper().startswith('40GE'):
        iftype = '40ge'
    elif interface.upper().startswith('100GE'):
        iftype = '100ge'
    elif interface.upper().startswith('PORT-GROUP'):
        iftype = 'stack-Port'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    else:
        return None
    return iftype.lower()


class Interface_mdn(object):
    """Manage global lldp enable configration"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # LLDP global configration info
        self.lldpenable = self.module.params['lldpenable'] or None
        self.ifname = self.module.params['ifname']
        self.mdnstatus = self.module.params['mdnstatus'] or None
        self.state = self.module.params['state']
        self.lldp_conf = dict()
        self.conf_exsit = False
        self.enable_flag = 0
        self.check_params()

        # state
        self.changed = False
        self.proposed_changed = dict()
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def check_params(self):
        """Check all input params"""

        if self.ifname:
            intf_type = get_interface_type(self.ifname)
            if not intf_type:
                self.module.fail_json(
                    msg='Error: ifname name of %s '
                        'is error.' % self.ifname)
            if (len(self.ifname) < 1) or (len(self.ifname) > 63):
                self.module.fail_json(
                    msg='Error: Ifname length is beetween 1 and 63.')

    def init_module(self):
        """Init module object"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def config_interface_mdn(self):
        """Configure lldp enabled and interface mdn enabled parameters"""

        if self.state == 'present':
            if self.enable_flag == 0 and self.lldpenable == 'enabled':
                xml_str = CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG % self.lldpenable
                ret_xml = set_nc_config(self.module, xml_str)
                self.check_response(ret_xml, "LLDP_ENABLE_CONFIG")
                self.changed = True
            elif self.enable_flag == 1 and self.lldpenable == 'disabled':
                xml_str = CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG % self.lldpenable
                ret_xml = set_nc_config(self.module, xml_str)
                self.check_response(ret_xml, "LLDP_ENABLE_CONFIG")
                self.changed = True
            elif self.enable_flag == 1 and self.conf_exsit:
                xml_str = CE_NC_MERGE_INTERFACE_MDNENABLE_CONFIG % (self.ifname, self.mdnstatus)
                ret_xml = set_nc_config(self.module, xml_str)
                self.check_response(ret_xml, "INTERFACE_MDN_ENABLE_CONFIG")
                self.changed = True

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

    def get_interface_mdn_exist_config(self):
        """Get lldp existed configure"""

        lldp_config = list()
        lldp_dict = dict()
        conf_enable_str = CE_NC_GET_GLOBAL_LLDPENABLE_CONFIG
        conf_enable_obj = get_nc_config(self.module, conf_enable_str)
        xml_enable_str = conf_enable_obj.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get lldp enable config info
        root_enable = ElementTree.fromstring(xml_enable_str)
        ntpsite_enable = root_enable.findall("lldp/lldpSys")
        for nexthop_enable in ntpsite_enable:
            for ele_enable in nexthop_enable:
                if ele_enable.tag in ["lldpEnable"]:
                    lldp_dict[ele_enable.tag] = ele_enable.text

            if self.state == "present":
                if lldp_dict['lldpEnable'] == 'enabled':
                    self.enable_flag = 1
            lldp_config.append(dict(lldpenable=lldp_dict['lldpEnable']))

        if self.enable_flag == 1:
            conf_str = CE_NC_GET_INTERFACE_MDNENABLE_CONFIG
            conf_obj = get_nc_config(self.module, conf_str)
            if "<data/>" in conf_obj:
                return lldp_config
            xml_str = conf_obj.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
            # get all ntp config info
            root = ElementTree.fromstring(xml_str)
            ntpsite = root.findall("lldp/mdnInterfaces/mdnInterface")
            for nexthop in ntpsite:
                for ele in nexthop:
                    if ele.tag in ["ifName", "mdnStatus"]:
                        lldp_dict[ele.tag] = ele.text
                if self.state == "present":
                    cur_interface_mdn_cfg = dict(ifname=lldp_dict['ifName'], mdnstatus=lldp_dict['mdnStatus'])
                    exp_interface_mdn_cfg = dict(ifname=self.ifname, mdnstatus=self.mdnstatus)
                    if self.ifname == lldp_dict['ifName']:
                        if cur_interface_mdn_cfg != exp_interface_mdn_cfg:
                            self.conf_exsit = True
                            lldp_config.append(dict(ifname=lldp_dict['ifName'], mdnstatus=lldp_dict['mdnStatus']))
                            return lldp_config
                        lldp_config.append(dict(ifname=lldp_dict['ifName'], mdnstatus=lldp_dict['mdnStatus']))
        return lldp_config

    def get_existing(self):
        """Get existing info"""

        self.existing = self.get_interface_mdn_exist_config()

    def get_proposed(self):
        """Get proposed info"""

        if self.lldpenable:
            self.proposed = dict(lldpenable=self.lldpenable)
        if self.enable_flag == 1:
            if self.ifname:
                self.proposed = dict(ifname=self.ifname, mdnstatus=self.mdnstatus)

    def get_end_state(self):
        """Get end state info"""

        self.end_state = self.get_interface_mdn_exist_config()

    def get_update_cmd(self):
        """Get updated commands"""

        update_list = list()
        if self.state == "present":
            if self.lldpenable == "enabled":
                cli_str = "lldp enable"
                update_list.append(cli_str)
                if self.ifname:
                    cli_str = "%s %s" % ("interface", self.ifname)
                    update_list.append(cli_str)
                if self.mdnstatus:
                    if self.mdnstatus == "rxOnly":
                        cli_str = "lldp mdn enable"
                        update_list.append(cli_str)
                    else:
                        cli_str = "undo lldp mdn enable"
                        update_list.append(cli_str)

            elif self.lldpenable == "disabled":
                cli_str = "undo lldp enable"
                update_list.append(cli_str)
            else:
                if self.enable_flag == 1:
                    if self.ifname:
                        cli_str = "%s %s" % ("interface", self.ifname)
                        update_list.append(cli_str)
                    if self.mdnstatus:
                        if self.mdnstatus == "rxOnly":
                            cli_str = "lldp mdn enable"
                            update_list.append(cli_str)
                        else:
                            cli_str = "undo lldp mdn enable"
                            update_list.append(cli_str)

        self.updates_cmd.append(update_list)

    def work(self):
        """Excute task"""
        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.config_interface_mdn()
        self.get_update_cmd()
        self.get_end_state()
        self.show_result()


def main():
    """Main function entry"""

    argument_spec = dict(
        lldpenable=dict(type='str', choices=['enabled', 'disabled']),
        mdnstatus=dict(type='str', choices=['rxOnly', 'disabled']),
        ifname=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )
    lldp_obj = Interface_mdn(argument_spec)
    lldp_obj.work()


if __name__ == '__main__':
    main()
