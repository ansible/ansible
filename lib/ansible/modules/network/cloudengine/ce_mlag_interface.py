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
    - Li Yanfeng (@QijunPan)
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
    type: bool
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
from ansible.module_utils.network.cloudengine.ce import load_config, ce_argument_spec
from ansible.module_utils.connection import exec_command

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

CE_NC_MERGE_MLAG_INFO = """
<config>
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <mlagInstances>
    <mlagInstance operation="merge">
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
      <errordownAction>Suspend</errordownAction>
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

CE_NC_GET_SYSTEM_MAC_INFO = """
<filter type="subtree">
  <system xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <systemInfo>
      <mac></mac>
    </systemInfo>
  </system>
</filter>
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

    def cli_add_command(self, command, undo=False):
        """add command to self.update_cmd and self.commands"""

        if undo and command.lower() not in ["quit", "return"]:
            cmd = "undo " + command
        else:
            cmd = command
        self.commands.append(cmd)
        if command.lower() not in ["quit", "return"]:
            self.updates_cmd.append(cmd)

    def cli_load_config(self, commands):
        """load config by cli"""

        if not self.module.check_mode:
            load_config(self.module, commands)

    def get_config(self, flags=None):
        """Retrieves the current config from the device or cache
        """
        flags = [] if flags is None else flags

        cmd = 'display current-configuration '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            self.module.fail_json(msg=err)
        cfg = str(out).strip()

        return cfg

    def get_mlag_info(self):
        """ get mlag info."""

        mlag_info = dict()

        flags = list()
        exp = "interface eth-trunk %s" % self.eth_trunk_id
        flags.append(exp)
        cfg = self.get_config(flags)
        if not cfg:
            return mlag_info

        else:
            mlag_info["mlagInfos"] = list()
            re_find = re.findall(r'.*dfs-group\s*(\d*)\s*m-lag\s*(\d*)\s*', cfg)
            if re_find:
                mlag_dict = dict(dfsgroupId=re_find[0][0], mlagId=re_find[0][1], localMlagPort=self.eth_trunk_id)
                mlag_info["mlagInfos"].append(mlag_dict)

            return mlag_info

    def get_mlag_global_info(self):
        """ get mlag global info."""

        mlag_global_info = dict()

        flags = list()
        exp = "| inc ^lacp"
        flags.append(exp)
        cfg = self.get_config(flags)
        if not cfg:
            return mlag_global_info

        else:
            re_find_mac = re.findall(r'.*lacp\s*m-lag\s*system-id\s*(\S*)\s*', cfg)
            re_find_priority = re.findall(r'.*lacp\s*m-lag\s*priority\s*(\d*)\s*', cfg)

            if re_find_priority:
                mlag_global_info["lacpMlagPriority"] = re_find_priority[0]
            if re_find_mac:
                mlag_global_info["lacpMlagSysId"] = re_find_mac[0]

            return mlag_global_info

    def get_mlag_trunk_attribute_info(self):
        """ get mlag global info."""

        mlag_trunk_attribute_info = dict()

        flags = list()
        exp = "interface eth-trunk %s" % self.eth_trunk_id
        flags.append(exp)
        cfg = self.get_config(flags)
        if not cfg:
            return mlag_trunk_attribute_info

        else:
            re_find_mac = re.findall(r'.*lacp\s*m-lag\s*system-id\s*(\S*)\s*', cfg)
            re_find_priority = re.findall(r'.*lacp\s*m-lag\s*priority\s*(\d*)\s*', cfg)

            if re_find_priority:
                mlag_trunk_attribute_info["lacpMlagPriority"] = re_find_priority[0]
            if re_find_mac:
                mlag_trunk_attribute_info["lacpMlagSysId"] = re_find_mac[0]

            return mlag_trunk_attribute_info

    def get_mlag_error_down_info(self):
        """ get error down info."""

        mlag_error_down_info = dict()

        flags = list()
        exp = "interface %s" % self.interface
        flags.append(exp)
        cfg = self.get_config(flags)
        if not cfg:
            return mlag_error_down_info

        else:
            re_find = re.findall(r'.*m-lag\s*unpaired-port\s*suspend\s*', cfg)
            if re_find:
                mlag_error_down_info = dict(dfsgroupId=1, portName=self.interface)

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

    def set_mlag(self):
        """create mlag info"""

        cmd = "interface eth-trunk %s" % self.eth_trunk_id
        self.cli_add_command(cmd)
        cmd = "dfs-group %s m-lag %s" % (self.dfs_group_id, self.mlag_id)
        self.cli_add_command(cmd)
        self.cli_load_config(self.commands)

    def delete_mlag(self):
        """delete mlag info"""

        cmd = "interface eth-trunk %s" % self.eth_trunk_id
        self.cli_add_command(cmd)

        cmd = "dfs-group %s m-lag %s" % (self.dfs_group_id, self.mlag_id)
        self.cli_add_command(cmd, undo=True)

        self.cli_load_config(self.commands)

    def set_mlag_error_down(self):
        """create mlag error down info"""

        cmd = "interface %s" % self.interface
        self.cli_add_command(cmd)
        cmd = "m-lag unpaired-port suspend"
        self.cli_add_command(cmd)
        self.cli_load_config(self.commands)

    def delete_mlag_error_down(self):
        """delete mlag error down info"""

        cmd = "interface %s" % self.interface
        self.cli_add_command(cmd)
        cmd = "m-lag unpaired-port suspend"
        self.cli_add_command(cmd, undo=True)
        self.cli_load_config(self.commands)

    def set_mlag_interface(self):
        """set mlag interface atrribute info"""

        if self.mlag_priority_id or self.mlag_system_id:
            cmd = "interface eth-trunk %s" % self.eth_trunk_id
            self.cli_add_command(cmd)
            if self.mlag_priority_id:
                cmd = "lacp m-lag priority %s" % self.mlag_priority_id
                self.cli_add_command(cmd)
            if self.mlag_system_id:
                cmd = "lacp m-lag system %s" % self.mlag_system_id
                self.cli_add_command(cmd)

            self.cli_load_config(self.commands)

    def delete_mlag_interface(self):
        """delete mlag interface attribute info"""

        if self.mlag_priority_id or self.mlag_system_id:
            cmd = "interface eth-trunk %s" % self.eth_trunk_id
            self.cli_add_command(cmd)
            if self.mlag_priority_id:
                cmd = "lacp m-lag priority %s" % self.mlag_priority_id
                self.cli_add_command(cmd, undo=True)
            if self.mlag_system_id:
                cmd = "lacp m-lag system %s" % self.mlag_system_id
                self.cli_add_command(cmd, undo=True)

            self.cli_load_config(self.commands)

    def set_mlag_global(self):
        """set mlag global attribute info"""

        if self.mlag_priority_id:
            cmd = "lacp m-lag priority %s" % self.mlag_priority_id
            self.cli_add_command(cmd)
        if self.mlag_system_id:
            cmd = "lacp m-lag system %s" % self.mlag_system_id
            self.cli_add_command(cmd)
            self.cli_load_config(self.commands)

    def delete_mlag_global(self):
        """delete mlag global attribute info"""

        if self.mlag_priority_id:
            cmd = "lacp m-lag priority %s" % self.mlag_priority_id
            self.cli_add_command(cmd, undo=True)
        if self.mlag_system_id:
            cmd = "lacp m-lag system %s" % self.mlag_system_id
            self.cli_add_command(cmd, undo=True)
            self.cli_load_config(self.commands)

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

        if self.eth_trunk_id or self.dfs_group_id or self.mlag_id:
            self.mlag_info = self.get_mlag_info()
            if not self.mlag_system_id and not self.mlag_priority_id:
                if self.mlag_info:
                    self.existing["mlagInfos"] = self.mlag_info["mlagInfos"]

        if self.mlag_system_id or self.mlag_priority_id:
            if self.eth_trunk_id:
                self.mlag_trunk_attribute_info = self.get_mlag_trunk_attribute_info()
                if self.mlag_trunk_attribute_info:
                    if self.mlag_system_id:
                        self.existing["lacpMlagSysId"] = self.mlag_trunk_attribute_info.get("lacpMlagSysId")
                    if self.mlag_priority_id:
                        self.existing["lacpMlagPriority"] = self.mlag_trunk_attribute_info.get("lacpMlagPriority")
            else:
                self.mlag_global_info = self.get_mlag_global_info()
                if self.mlag_global_info:
                    if self.mlag_system_id:
                        self.existing["lacpMlagSysId"] = self.mlag_global_info.get("lacpMlagSysId")
                    if self.mlag_priority_id:
                        self.existing["lacpMlagPriority"] = self.mlag_global_info.get("lacpMlagPriority")

        if self.interface or self.mlag_error_down:
            self.mlag_error_down_info = self.get_mlag_error_down_info()
            if self.mlag_error_down_info:
                self.existing["mlagErrorDownInfos"] = self.mlag_error_down_info

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
                        self.end_state["lacpMlagSysId"] = self.mlag_trunk_attribute_info.get("lacpMlagSysId")
                    if self.mlag_priority_id:
                        self.end_state["lacpMlagPriority"] = self.mlag_trunk_attribute_info.get("lacpMlagPriority")
            else:
                self.mlag_global_info = self.get_mlag_global_info()
                if self.mlag_global_info:
                    if self.mlag_system_id:
                        self.end_state["lacpMlagSysId"] = self.mlag_global_info.get("lacpMlagSysId")
                    if self.mlag_priority_id:
                        self.end_state["lacpMlagPriority"] = self.mlag_global_info.get("lacpMlagPriority")

        if self.interface or self.mlag_error_down:
            self.mlag_error_down_info = self.get_mlag_error_down_info()
            if self.mlag_error_down_info:
                self.end_state["mlagErrorDownInfos"] = self.mlag_error_down_info

    def work(self):
        """worker"""

        self.check_params()
        self.get_proposed()
        self.get_existing()

        if self.eth_trunk_id or self.dfs_group_id or self.mlag_id:
            self.mlag_info = self.get_mlag_info()

            if self.eth_trunk_id and self.dfs_group_id and self.mlag_id:
                mlag_cfg = self.mlag_info["mlagInfos"]
                port_cfg = None
                for cfg in mlag_cfg:
                    if cfg.get("localMlagPort") == self.eth_trunk_id:
                        port_cfg = cfg

                if port_cfg:
                    if self.state == "present":
                        if self.dfs_group_id != port_cfg.get("dfsgroupId") or self.mlag_id != port_cfg.get("mlagId"):
                            self.set_mlag()
                            self.changed = True

                    else:
                        if self.dfs_group_id == port_cfg.get("dfsgroupId") and self.mlag_id == port_cfg.get("mlagId"):
                            self.delete_mlag()
                            self.changed = True
                else:
                    if self.state == "present":
                        self.set_mlag()
                        self.changed = True

            else:
                if not self.mlag_system_id and not self.mlag_priority_id:
                    self.module.fail_json(
                        msg='Error: eth_trunk_id, dfs_group_id, mlag_id must be config at the same time.')

        if self.mlag_system_id or self.mlag_priority_id:

            if self.eth_trunk_id:
                mlag_trunk_attribute_info = self.get_mlag_trunk_attribute_info()
                if self.mlag_system_id != mlag_trunk_attribute_info.get("lacpMlagSysId") or \
                        self.mlag_priority_id != mlag_trunk_attribute_info.get("lacpMlagPriority"):
                    if self.state == "present":
                        self.set_mlag_interface()
                        self.changed = True

                if self.mlag_system_id == mlag_trunk_attribute_info.get("lacpMlagSysId") and \
                        self.mlag_priority_id == mlag_trunk_attribute_info.get("lacpMlagPriority"):

                    if self.state == "absent":
                        self.delete_mlag_interface()
                        self.changed = True
            else:
                mlag_global_info = self.get_mlag_global_info()
                if self.mlag_system_id != mlag_global_info.get("lacpMlagSysId") or \
                        self.mlag_priority_id != mlag_global_info.get("lacpMlagPriority"):
                    if self.state == "present":
                        self.set_mlag_global()
                        self.changed = True

                if self.mlag_system_id == mlag_global_info.get("lacpMlagSysId") and \
                        self.mlag_priority_id == mlag_global_info.get("lacpMlagPriority"):
                    if self.state == "absent":
                        self.delete_mlag_global()
                        self.changed = True

        if self.interface or self.mlag_error_down:
            mlag_error_down_info = self.get_mlag_error_down_info()
            if self.interface and self.mlag_error_down:
                if self.mlag_error_down == "enable" and not mlag_error_down_info:
                    self.set_mlag_error_down()
                    self.changed = True
                if self.mlag_error_down == "disable" and mlag_error_down_info:
                    self.delete_mlag_error_down()
                    self.changed = True
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
