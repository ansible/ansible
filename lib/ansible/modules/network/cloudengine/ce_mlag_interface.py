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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_mlag_interface
version_added: "2.4"
short_description: Manages MLAG interfaces on HUAWEI CloudEngine switches.
description:
    - Manages MLAG interface attributes on HUAWEI CloudEngine switches.
author:
    - Li Yanfeng (@CloudEngine-Ansible)
options:
    eth_trunk_id:
        description:
            - Name of the local M-LAG interface. The value is ranging from 0 to 511.
    dfs_group_id:
        description:
            - ID of a DFS group.The value is 1.
        default: present
    mlag_id:
        description:
            - ID of the M-LAG. The value is an integer that ranges from 1 to 2048.
    mlag_system_id:
        description:
            - M-LAG global LACP system MAC address. The value is a string of 0 to 255 characters. The default value
              is the MAC address of the Ethernet port of MPU.
    mlag_priority_id:
        description:
            - M-LAG global LACP system priority. The value is an integer ranging from 0 to 65535.
              The default value is 32768.
    interface:
        description:
            - Name of the interface that enters the Error-Down state when the peer-link fails.
              The value is a string of 1 to 63 characters.
    mlag_error_down:
        description:
            - Configure the interface on the slave device to enter the Error-Down state.
        choices: ['enable','disable']
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present','absent']

'''

EXAMPLES = '''
- name: mlag interface module test
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

  - name: Set interface mlag error down
    ce_mlag_interface:
      interface: 10GE2/0/1
      mlag_error_down: enable
      provider: "{{ cli }}"
  - name: Create mlag
    ce_mlag_interface:
      eth_trunk_id: 1
      dfs_group_id: 1
      mlag_id: 4
      provider: "{{ cli }}"
  - name: Set mlag global attribute
    ce_mlag_interface:
      mlag_system_id: 0020-1409-0407
      mlag_priority_id: 5
      provider: "{{ cli }}"
  - name: Set mlag interface attribute
    ce_mlag_interface:
      eth_trunk_id: 1
      mlag_system_id: 0020-1409-0400
      mlag_priority_id: 3
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: { "interface": "eth-trunk1",
              "mlag_error_down": "disable",
              "state": "present"
            }
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {   "mlagErrorDownInfos": [
                {
                    "dfsgroupId": "1",
                    "portName": "Eth-Trunk1"
                }
              ]
            }
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: { "interface eth-trunk1",
              "undo m-lag unpaired-port suspend"}
'''

import re
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import load_config
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec

CE_NC_GET_MLAG_INFO = """
<filter type="subtree">
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <mlagInstances>
    <mlagInstance>
    </mlagInstance>
  </mlagInstances>
</mlag>
</filter>
"""

CE_NC_CREATE_MLAG_INFO = """
<config>
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <mlagInstances>
    <mlagInstance operation="create">
      <dfsgroupId>%s</dfsgroupId>
      <mlagId>%s</mlagId>
      <localMlagPort>%s</localMlagPort>
    </mlagInstance>
  </mlagInstances>
</mlag>
</config>
"""

CE_NC_DELETE_MLAG_INFO = """
<config>
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <mlagInstances>
    <mlagInstance operation="delete">
      <dfsgroupId>%s</dfsgroupId>
      <mlagId>%s</mlagId>
      <localMlagPort>%s</localMlagPort>
    </mlagInstance>
  </mlagInstances>
</mlag>
</config>
"""

CE_NC_GET_LACP_MLAG_INFO = """
<filter type="subtree">
  <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <TrunkIfs>
      <TrunkIf>
        <ifName>%s</ifName>
        <lacpMlagIf>
          <lacpMlagSysId></lacpMlagSysId>
          <lacpMlagPriority></lacpMlagPriority>
        </lacpMlagIf>
      </TrunkIf>
    </TrunkIfs>
  </ifmtrunk>
</filter>
"""

CE_NC_SET_LACP_MLAG_INFO_HEAD = """
<config>
  <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <TrunkIfs>
      <TrunkIf>
        <ifName>%s</ifName>
        <lacpMlagIf operation="merge">
"""

CE_NC_SET_LACP_MLAG_INFO_TAIL = """
        </lacpMlagIf>
      </TrunkIf>
    </TrunkIfs>
  </ifmtrunk>
</config>
"""

CE_NC_GET_GLOBAL_LACP_MLAG_INFO = """
<filter type="subtree">
  <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lacpSysInfo>
      <lacpMlagGlobal>
        <lacpMlagSysId></lacpMlagSysId>
        <lacpMlagPriority></lacpMlagPriority>
      </lacpMlagGlobal>
    </lacpSysInfo>
  </ifmtrunk>
</filter>
"""

CE_NC_SET_GLOBAL_LACP_MLAG_INFO_HEAD = """
<config>
  <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lacpSysInfo>
      <lacpMlagGlobal operation="merge">
"""

CE_NC_SET_GLOBAL_LACP_MLAG_INFO_TAIL = """
      </lacpMlagGlobal>
    </lacpSysInfo>
  </ifmtrunk>
</config>
"""

CE_NC_GET_MLAG_ERROR_DOWN_INFO = """
<filter type="subtree">
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <errordowns>
    <errordown>
      <dfsgroupId></dfsgroupId>
      <portName></portName>
      <portState></portState>
    </errordown>
  </errordowns>
</mlag>
</filter>

"""

CE_NC_CREATE_MLAG_ERROR_DOWN_INFO = """
<config>
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <errordowns>
    <errordown operation="create">
      <dfsgroupId>1</dfsgroupId>
      <portName>%s</portName>
    </errordown>
  </errordowns>
</mlag>
</config>
"""

CE_NC_DELETE_MLAG_ERROR_DOWN_INFO = """
<config>
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <errordowns>
    <errordown operation="delete">
      <dfsgroupId>1</dfsgroupId>
      <portName>%s</portName>
    </errordown>
  </errordowns>
</mlag>
</config>

"""


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
    elif interface.upper().startswith('40GE'):
        iftype = '40ge'
    elif interface.upper().startswith('100GE'):
        iftype = '100ge'
    elif interface.upper().startswith('ETH-TRUNK'):
        iftype = 'eth-trunk'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    else:
        return None

    return iftype.lower()


class MlagInterface(object):
    """
    Manages Manages MLAG interface information.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.eth_trunk_id = self.module.params['eth_trunk_id']
        self.dfs_group_id = self.module.params['dfs_group_id']
        self.mlag_id = self.module.params['mlag_id']
        self.mlag_system_id = self.module.params['mlag_system_id']
        self.mlag_priority_id = self.module.params['mlag_priority_id']
        self.interface = self.module.params['interface']
        self.mlag_error_down = self.module.params['mlag_error_down']
        self.state = self.module.params['state']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.existing = dict()
        self.proposed = dict()
        self.end_state = dict()

        # mlag info
        self.commands = list()
        self.mlag_info = None
        self.mlag_global_info = None
        self.mlag_error_down_info = None
        self.mlag_trunk_attribute_info = None

    def init_module(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def cli_add_command(self, command, undo=False):
        """add command to self.update_cmd and self.commands"""

        if undo and command.lower() not in ["quit", "return"]:
            cmd = "undo " + command
        else:
            cmd = command

        self.commands.append(cmd)          # set to device
        if command.lower() not in ["quit", "return"]:
            self.updates_cmd.append(cmd)   # show updates result

    def cli_load_config(self, commands):
        """load config by cli"""

        if not self.module.check_mode:
            load_config(self.module, commands)

    def get_mlag_info(self):
        """ get mlag info."""

        mlag_info = dict()
        conf_str = CE_NC_GET_MLAG_INFO
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return mlag_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            mlag_info["mlagInfos"] = list()
            root = ElementTree.fromstring(xml_str)
            dfs_mlag_infos = root.findall(
                "data/mlag/mlagInstances/mlagInstance")

            if dfs_mlag_infos:
                for dfs_mlag_info in dfs_mlag_infos:
                    mlag_dict = dict()
                    for ele in dfs_mlag_info:
                        if ele.tag in ["dfsgroupId", "mlagId", "localMlagPort"]:
                            mlag_dict[ele.tag] = ele.text
                    mlag_info["mlagInfos"].append(mlag_dict)
            return mlag_info

    def get_mlag_global_info(self):
        """ get mlag global info."""

        mlag_global_info = dict()
        conf_str = CE_NC_GET_GLOBAL_LACP_MLAG_INFO
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return mlag_global_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            global_info = root.findall(
                "data/ifmtrunk/lacpSysInfo/lacpMlagGlobal")

            if global_info:
                for tmp in global_info:
                    for site in tmp:
                        if site.tag in ["lacpMlagSysId", "lacpMlagPriority"]:
                            mlag_global_info[site.tag] = site.text
            return mlag_global_info

    def get_mlag_trunk_attribute_info(self):
        """ get mlag global info."""

        mlag_trunk_attribute_info = dict()
        eth_trunk = "Eth-Trunk"
        eth_trunk += self.eth_trunk_id
        conf_str = CE_NC_GET_LACP_MLAG_INFO % eth_trunk
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return mlag_trunk_attribute_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            global_info = root.findall(
                "data/ifmtrunk/TrunkIfs/TrunkIf/lacpMlagIf")

            if global_info:
                for tmp in global_info:
                    for site in tmp:
                        if site.tag in ["lacpMlagSysId", "lacpMlagPriority"]:
                            mlag_trunk_attribute_info[site.tag] = site.text
            return mlag_trunk_attribute_info

    def get_mlag_error_down_info(self):
        """ get error down info."""

        mlag_error_down_info = dict()
        conf_str = CE_NC_GET_MLAG_ERROR_DOWN_INFO
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return mlag_error_down_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            mlag_error_down_info["mlagErrorDownInfos"] = list()
            root = ElementTree.fromstring(xml_str)
            mlag_error_infos = root.findall(
                "data/mlag/errordowns/errordown")

            if mlag_error_infos:
                for mlag_error_info in mlag_error_infos:
                    mlag_error_dict = dict()
                    for ele in mlag_error_info:
                        if ele.tag in ["dfsgroupId", "portName"]:
                            mlag_error_dict[ele.tag] = ele.text
                    mlag_error_down_info[
                        "mlagErrorDownInfos"].append(mlag_error_dict)
            return mlag_error_down_info

    def check_macaddr(self):
        """check mac-address whether valid"""

        valid_char = '0123456789abcdef-'
        mac = self.mlag_system_id

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

        # eth_trunk_id check
        if self.eth_trunk_id:
            if not self.eth_trunk_id.isdigit():
                self.module.fail_json(
                    msg='Error: The value of eth_trunk_id is an integer.')
            if int(self.eth_trunk_id) < 0 or int(self.eth_trunk_id) > 511:
                self.module.fail_json(
                    msg='Error: The value of eth_trunk_id is not in the range from 0 to 511.')

        # dfs_group_id check
        if self.dfs_group_id:
            if self.dfs_group_id != "1":
                self.module.fail_json(
                    msg='Error: The value of dfs_group_id must be 1.')

        # mlag_id check
        if self.mlag_id:
            if not self.mlag_id.isdigit():
                self.module.fail_json(
                    msg='Error: The value of mlag_id is an integer.')
            if int(self.mlag_id) < 1 or int(self.mlag_id) > 2048:
                self.module.fail_json(
                    msg='Error: The value of mlag_id is not in the range from 1 to 2048.')

        # mlag_system_id check
        if self.mlag_system_id:
            if not self.check_macaddr():
                self.module.fail_json(
                    msg="Error: mlag_system_id has invalid value %s." % self.mlag_system_id)

        # mlag_priority_id check
        if self.mlag_priority_id:
            if not self.mlag_priority_id.isdigit():
                self.module.fail_json(
                    msg='Error: The value of mlag_priority_id is an integer.')
            if int(self.mlag_priority_id) < 0 or int(self.mlag_priority_id) > 254:
                self.module.fail_json(
                    msg='Error: The value of mlag_priority_id is not in the range from 0 to 254.')

        # interface check
        if self.interface:
            intf_type = get_interface_type(self.interface)
            if not intf_type:
                self.module.fail_json(
                    msg='Error: Interface name of %s '
                        'is error.' % self.interface)

    def is_mlag_info_change(self):
        """whether mlag info change"""

        if not self.mlag_info:
            return True

        eth_trunk = "Eth-Trunk"
        eth_trunk += self.eth_trunk_id
        for info in self.mlag_info["mlagInfos"]:
            if info["mlagId"] == self.mlag_id and info["localMlagPort"] == eth_trunk:
                return False
        return True

    def is_mlag_info_exist(self):
        """whether mlag info exist"""

        if not self.mlag_info:
            return False

        eth_trunk = "Eth-Trunk"
        eth_trunk += self.eth_trunk_id

        for info in self.mlag_info["mlagInfos"]:
            if info["mlagId"] == self.mlag_id and info["localMlagPort"] == eth_trunk:
                return True
        return False

    def is_mlag_error_down_info_change(self):
        """whether mlag error down info change"""

        if not self.mlag_error_down_info:
            return True

        for info in self.mlag_error_down_info["mlagErrorDownInfos"]:
            if info["portName"].upper() == self.interface.upper():
                return False
        return True

    def is_mlag_error_down_info_exist(self):
        """whether mlag error down info exist"""

        if not self.mlag_error_down_info:
            return False

        for info in self.mlag_error_down_info["mlagErrorDownInfos"]:
            if info["portName"].upper() == self.interface.upper():
                return True
        return False

    def is_mlag_interface_info_change(self):
        """whether mlag interface attribute info change"""

        if not self.mlag_trunk_attribute_info:
            return True

        if self.mlag_system_id:
            if self.mlag_trunk_attribute_info["lacpMlagSysId"] != self.mlag_system_id:
                return True
        if self.mlag_priority_id:
            if self.mlag_trunk_attribute_info["lacpMlagPriority"] != self.mlag_priority_id:
                return True
        return False

    def is_mlag_interface_info_exist(self):
        """whether mlag interface attribute info exist"""

        if not self.mlag_trunk_attribute_info:
            return False

        if self.mlag_system_id:
            if self.mlag_priority_id:
                if self.mlag_trunk_attribute_info["lacpMlagSysId"] == self.mlag_system_id \
                        and self.mlag_trunk_attribute_info["lacpMlagPriority"] == self.mlag_priority_id:
                    return True
            else:
                if self.mlag_trunk_attribute_info["lacpMlagSysId"] == self.mlag_system_id:
                    return True

        if self.mlag_priority_id:
            if self.mlag_system_id:
                if self.mlag_trunk_attribute_info["lacpMlagSysId"] == self.mlag_system_id \
                        and self.mlag_trunk_attribute_info["lacpMlagPriority"] == self.mlag_priority_id:
                    return True
            else:
                if self.mlag_trunk_attribute_info["lacpMlagPriority"] == self.mlag_priority_id:
                    return True

        return False

    def is_mlag_global_info_change(self):
        """whether mlag global attribute info change"""

        if not self.mlag_global_info:
            return True

        if self.mlag_system_id:
            if self.mlag_global_info["lacpMlagSysId"] != self.mlag_system_id:
                return True
        if self.mlag_priority_id:
            if self.mlag_global_info["lacpMlagPriority"] != self.mlag_priority_id:
                return True
        return False

    def is_mlag_global_info_exist(self):
        """whether mlag global attribute info exist"""

        if not self.mlag_global_info:
            return False

        if self.mlag_system_id:
            if self.mlag_priority_id:
                if self.mlag_global_info["lacpMlagSysId"] == self.mlag_system_id \
                        and self.mlag_global_info["lacpMlagPriority"] == self.mlag_priority_id:
                    return True
            else:
                if self.mlag_global_info["lacpMlagSysId"] == self.mlag_system_id:
                    return True

        if self.mlag_priority_id:
            if self.mlag_system_id:
                if self.mlag_global_info["lacpMlagSysId"] == self.mlag_system_id \
                        and self.mlag_global_info["lacpMlagPriority"] == self.mlag_priority_id:
                    return True
            else:
                if self.mlag_global_info["lacpMlagPriority"] == self.mlag_priority_id:
                    return True

        return False

    def create_mlag(self):
        """create mlag info"""

        if self.is_mlag_info_change():
            mlag_port = "Eth-Trunk"
            mlag_port += self.eth_trunk_id
            conf_str = CE_NC_CREATE_MLAG_INFO % (
                self.dfs_group_id, self.mlag_id, mlag_port)
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: create mlag info failed.')

            self.updates_cmd.append("interface %s" % mlag_port)
            self.updates_cmd.append("dfs-group %s m-lag %s" %
                                    (self.dfs_group_id, self.mlag_id))
            self.changed = True

    def delete_mlag(self):
        """delete mlag info"""

        if self.is_mlag_info_exist():
            mlag_port = "Eth-Trunk"
            mlag_port += self.eth_trunk_id
            conf_str = CE_NC_DELETE_MLAG_INFO % (
                self.dfs_group_id, self.mlag_id, mlag_port)
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: delete mlag info failed.')

            self.updates_cmd.append("interface %s" % mlag_port)
            self.updates_cmd.append(
                "undo dfs-group %s m-lag %s" % (self.dfs_group_id, self.mlag_id))
            self.changed = True

    def create_mlag_error_down(self):
        """create mlag error down info"""

        if self.is_mlag_error_down_info_change():
            conf_str = CE_NC_CREATE_MLAG_ERROR_DOWN_INFO % self.interface
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: create mlag error down info failed.')

            self.updates_cmd.append("interface %s" % self.interface)
            self.updates_cmd.append("m-lag unpaired-port suspend")
            self.changed = True

    def delete_mlag_error_down(self):
        """delete mlag error down info"""

        if self.is_mlag_error_down_info_exist():

            conf_str = CE_NC_DELETE_MLAG_ERROR_DOWN_INFO % self.interface
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: delete mlag error down info failed.')

            self.updates_cmd.append("interface %s" % self.interface)
            self.updates_cmd.append("undo m-lag unpaired-port suspend")
            self.changed = True

    def set_mlag_interface(self):
        """set mlag interface atrribute info"""

        if self.is_mlag_interface_info_change():
            mlag_port = "Eth-Trunk"
            mlag_port += self.eth_trunk_id
            conf_str = CE_NC_SET_LACP_MLAG_INFO_HEAD % mlag_port
            if self.mlag_priority_id:
                conf_str += "<lacpMlagPriority>%s</lacpMlagPriority>" % self.mlag_priority_id
            if self.mlag_system_id:
                conf_str += "<lacpMlagSysId>%s</lacpMlagSysId>" % self.mlag_system_id
            conf_str += CE_NC_SET_LACP_MLAG_INFO_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: set mlag interface atrribute info failed.')

            self.updates_cmd.append("interface %s" % mlag_port)
            if self.mlag_priority_id:
                self.updates_cmd.append(
                    "lacp m-lag priority %s" % self.mlag_priority_id)

            if self.mlag_system_id:
                self.updates_cmd.append(
                    "lacp m-lag system-id %s" % self.mlag_system_id)
            self.changed = True

    def delete_mlag_interface(self):
        """delete mlag interface attribute info"""

        if self.is_mlag_interface_info_exist():
            mlag_port = "Eth-Trunk"
            mlag_port += self.eth_trunk_id

            cmd = "interface %s" % mlag_port
            self.cli_add_command(cmd)

            if self.mlag_priority_id:
                cmd = "lacp m-lag priority %s" % self.mlag_priority_id
                self.cli_add_command(cmd, True)

            if self.mlag_system_id:
                cmd = "lacp m-lag system-id %s" % self.mlag_system_id
                self.cli_add_command(cmd, True)

            if self.commands:
                self.cli_load_config(self.commands)
                self.changed = True

    def set_mlag_global(self):
        """set mlag global attribute info"""

        if self.is_mlag_global_info_change():
            conf_str = CE_NC_SET_GLOBAL_LACP_MLAG_INFO_HEAD
            if self.mlag_priority_id:
                conf_str += "<lacpMlagPriority>%s</lacpMlagPriority>" % self.mlag_priority_id
            if self.mlag_system_id:
                conf_str += "<lacpMlagSysId>%s</lacpMlagSysId>" % self.mlag_system_id
            conf_str += CE_NC_SET_GLOBAL_LACP_MLAG_INFO_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: set mlag interface atrribute info failed.')

            if self.mlag_priority_id:
                self.updates_cmd.append(
                    "lacp m-lag priority %s" % self.mlag_priority_id)

            if self.mlag_system_id:
                self.updates_cmd.append(
                    "lacp m-lag system-id %s" % self.mlag_system_id)
            self.changed = True

    def delete_mlag_global(self):
        """delete mlag global attribute info"""

        if self.is_mlag_global_info_exist():
            if self.mlag_priority_id:
                cmd = "lacp m-lag priority %s" % self.mlag_priority_id
                self.cli_add_command(cmd, True)

            if self.mlag_system_id:
                cmd = "lacp m-lag system-id %s" % self.mlag_system_id
                self.cli_add_command(cmd, True)

            if self.commands:
                self.cli_load_config(self.commands)
                self.changed = True

    def get_proposed(self):
        """get proposed info"""

        if self.eth_trunk_id:
            self.proposed["eth_trunk_id"] = self.eth_trunk_id
        if self.dfs_group_id:
            self.proposed["dfs_group_id"] = self.dfs_group_id
        if self.mlag_id:
            self.proposed["mlag_id"] = self.mlag_id
        if self.mlag_system_id:
            self.proposed["mlag_system_id"] = self.mlag_system_id
        if self.mlag_priority_id:
            self.proposed["mlag_priority_id"] = self.mlag_priority_id
        if self.interface:
            self.proposed["interface"] = self.interface
        if self.mlag_error_down:
            self.proposed["mlag_error_down"] = self.mlag_error_down
        if self.state:
            self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        self.mlag_info = self.get_mlag_info()
        self.mlag_global_info = self.get_mlag_global_info()
        self.mlag_error_down_info = self.get_mlag_error_down_info()

        if self.eth_trunk_id or self.dfs_group_id or self.mlag_id:
            if not self.mlag_system_id and not self.mlag_priority_id:
                if self.mlag_info:
                    self.existing["mlagInfos"] = self.mlag_info["mlagInfos"]

        if self.mlag_system_id or self.mlag_priority_id:
            if self.eth_trunk_id:
                if self.mlag_trunk_attribute_info:
                    if self.mlag_system_id:
                        self.end_state["lacpMlagSysId"] = self.mlag_trunk_attribute_info[
                            "lacpMlagSysId"]
                    if self.mlag_priority_id:
                        self.end_state["lacpMlagPriority"] = self.mlag_trunk_attribute_info[
                            "lacpMlagPriority"]
            else:
                if self.mlag_global_info:
                    if self.mlag_system_id:
                        self.end_state["lacpMlagSysId"] = self.mlag_global_info[
                            "lacpMlagSysId"]
                    if self.mlag_priority_id:
                        self.end_state["lacpMlagPriority"] = self.mlag_global_info[
                            "lacpMlagPriority"]

        if self.interface or self.mlag_error_down:
            if self.mlag_error_down_info:
                self.existing["mlagErrorDownInfos"] = self.mlag_error_down_info[
                    "mlagErrorDownInfos"]

    def get_end_state(self):
        """get end state info"""

        if self.eth_trunk_id or self.dfs_group_id or self.mlag_id:
            self.mlag_info = self.get_mlag_info()
            if not self.mlag_system_id and not self.mlag_priority_id:
                if self.mlag_info:
                    self.end_state["mlagInfos"] = self.mlag_info["mlagInfos"]

        if self.mlag_system_id or self.mlag_priority_id:
            if self.eth_trunk_id:
                self.mlag_trunk_attribute_info = self.get_mlag_trunk_attribute_info()
                if self.mlag_trunk_attribute_info:
                    if self.mlag_system_id:
                        self.end_state["lacpMlagSysId"] = self.mlag_trunk_attribute_info[
                            "lacpMlagSysId"]
                    if self.mlag_priority_id:
                        self.end_state["lacpMlagPriority"] = self.mlag_trunk_attribute_info[
                            "lacpMlagPriority"]
            else:
                self.mlag_global_info = self.get_mlag_global_info()
                if self.mlag_global_info:
                    if self.mlag_system_id:
                        self.end_state["lacpMlagSysId"] = self.mlag_global_info[
                            "lacpMlagSysId"]
                    if self.mlag_priority_id:
                        self.end_state["lacpMlagPriority"] = self.mlag_global_info[
                            "lacpMlagPriority"]

        if self.interface or self.mlag_error_down:
            self.mlag_error_down_info = self.get_mlag_error_down_info()
            if self.mlag_error_down_info:
                self.end_state["mlagErrorDownInfos"] = self.mlag_error_down_info[
                    "mlagErrorDownInfos"]

    def work(self):
        """worker"""

        self.check_params()
        self.get_proposed()
        self.get_existing()

        if self.eth_trunk_id or self.dfs_group_id or self.mlag_id:
            self.mlag_info = self.get_mlag_info()
            if self.eth_trunk_id and self.dfs_group_id and self.mlag_id:
                if self.state == "present":
                    self.create_mlag()
                else:
                    self.delete_mlag()
            else:
                if not self.mlag_system_id and not self.mlag_priority_id:
                    self.module.fail_json(
                        msg='Error: eth_trunk_id, dfs_group_id, mlag_id must be config at the same time.')

        if self.mlag_system_id or self.mlag_priority_id:

            if self.eth_trunk_id:
                self.mlag_trunk_attribute_info = self.get_mlag_trunk_attribute_info()
                if self.mlag_system_id or self.mlag_priority_id:
                    if self.state == "present":
                        self.set_mlag_interface()
                    else:
                        self.delete_mlag_interface()
            else:
                self.mlag_global_info = self.get_mlag_global_info()
                if self.mlag_system_id or self.mlag_priority_id:
                    if self.state == "present":
                        self.set_mlag_global()
                    else:
                        self.delete_mlag_global()

        if self.interface or self.mlag_error_down:
            self.mlag_error_down_info = self.get_mlag_error_down_info()
            if self.interface and self.mlag_error_down:
                if self.mlag_error_down == "enable":
                    self.create_mlag_error_down()
                else:
                    self.delete_mlag_error_down()
            else:
                self.module.fail_json(
                    msg='Error: interface, mlag_error_down must be config at the same time.')

        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """ Module main """

    argument_spec = dict(
        eth_trunk_id=dict(type='str'),
        dfs_group_id=dict(type='str'),
        mlag_id=dict(type='str'),
        mlag_system_id=dict(type='str'),
        mlag_priority_id=dict(type='str'),
        interface=dict(type='str'),
        mlag_error_down=dict(type='str', choices=['enable', 'disable']),
        state=dict(type='str', default='present',
                   choices=['present', 'absent'])
    )
    argument_spec.update(ce_argument_spec)
    module = MlagInterface(argument_spec=argument_spec)
    module.work()


if __name__ == '__main__':
    main()
