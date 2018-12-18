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
module: ce_mlag_config
version_added: "2.4"
short_description: Manages MLAG configuration on HUAWEI CloudEngine switches.
description:
    - Manages MLAG configuration on HUAWEI CloudEngine switches.
author:
    - Li Yanfeng (@QijunPan)
options:
    dfs_group_id:
        description:
            - ID of a DFS group. The value is 1.
        default: present
    nickname:
        description:
            - The nickname bound to a DFS group. The value is an integer that ranges from 1 to 65471.
    pseudo_nickname:
        description:
            - A pseudo nickname of a DFS group. The value is an integer that ranges from 1 to 65471.
    pseudo_priority:
        description:
            - The priority of a pseudo nickname. The value is an integer that ranges from 128 to 255.
              The default value is 192. A larger value indicates a higher priority.
    ip_address:
        description:
            - IP address bound to the DFS group. The value is in dotted decimal notation.
    vpn_instance_name:
        description:
            - Name of the VPN instance bound to the DFS group. The value is a string of 1 to 31 case-sensitive
              characters without spaces. If the character string is quoted by double quotation marks, the character
              string can contain spaces. The value _public_ is reserved and cannot be used as the VPN instance name.
    priority_id:
        description:
            - Priority of a DFS group. The value is an integer that ranges from 1 to 254. The default value is 100.
    eth_trunk_id:
        description:
            - Name of the peer-link interface. The value is in the range from 0 to 511.
    peer_link_id:
        description:
            - Number of the peer-link interface. The value is 1.
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- name: mlag config module test
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

  - name: Create DFS Group id
    ce_mlag_config:
      dfs_group_id: 1
      provider: "{{ cli }}"
  - name: Set dfs-group priority
    ce_mlag_config:
      dfs_group_id: 1
      priority_id: 3
      state: present
      provider: "{{ cli }}"
  - name: Set pseudo nickname
    ce_mlag_config:
      dfs_group_id: 1
      pseudo_nickname: 3
      pseudo_priority: 130
      state: present
      provider: "{{ cli }}"
  - name: Set ip
    ce_mlag_config:
      dfs_group_id: 1
      ip_address: 11.1.1.2
      vpn_instance_name: 6
      provider: "{{ cli }}"
  - name: Set peer link
    ce_mlag_config:
      eth_trunk_id: 3
      peer_link_id: 2
      state: present
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
    sample: { "eth_trunk_id": "3",
              "peer_link_id": "1",
              "state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: { }
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: { "eth_trunk_id": "Eth-Trunk3",
              "peer_link_id": "1"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: {"peer-link 1"}
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import load_config
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec


CE_NC_GET_DFS_GROUP_INFO = """
<filter type="subtree">
<dfs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <groupInstances>
    <groupInstance>
      <groupId></groupId>
      <priority></priority>
      <ipAddress></ipAddress>
      <srcVpnName></srcVpnName>
      <trillType>
          <localNickname></localNickname>
          <pseudoNickname></pseudoNickname>
          <pseudoPriority></pseudoPriority>
      </trillType>
    </groupInstance>
  </groupInstances>
</dfs>
</filter>
"""
CE_NC_GET_PEER_LINK_INFO = """
<filter type="subtree">
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <peerlinks>
    <peerlink>
      <dfsgroupId></dfsgroupId>
      <linkId></linkId>
      <portName></portName>
    </peerlink>
  </peerlinks>
</mlag>
</filter>
"""

CE_NC_CREATE_DFS_GROUP_INFO_HEADER = """
<config>
<dfs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <groupInstances>
    <groupInstance operation="create">
      <groupId>%s</groupId>
"""

CE_NC_CREATE_DFS_GROUP_INFO_TAIL = """
    </groupInstance>
  </groupInstances>
</dfs>
</config>
"""

CE_NC_MERGE_DFS_GROUP_INFO_HEADER = """
<config>
<dfs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <groupInstances>
    <groupInstance operation="merge">
      <groupId>%s</groupId>
"""

CE_NC_MERGE_DFS_GROUP_INFO_TAIL = """
    </groupInstance>
  </groupInstances>
</dfs>
</config>
"""

CE_NC_DELETE_DFS_GROUP_INFO_HEADER = """
<config>
<dfs xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <groupInstances>
    <groupInstance operation="delete">
      <groupId>%s</groupId>

"""

CE_NC_DELETE_DFS_GROUP_INFO_TAIL = """
    </groupInstance>
  </groupInstances>
</dfs>
</config>

"""

CE_NC_CREATE_PEER_LINK_INFO = """
<config>
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <peerlinks>
    <peerlink operation="create">
      <dfsgroupId>1</dfsgroupId>
      <linkId>%s</linkId>
      <portName>%s</portName>
    </peerlink>
  </peerlinks>
</mlag>
</config>
"""

CE_NC_MERGE_PEER_LINK_INFO = """
<config>
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <peerlinks>
    <peerlink operation="merge">
      <dfsgroupId>1</dfsgroupId>
      <linkId>%s</linkId>
      <portName>%s</portName>
    </peerlink>
  </peerlinks>
</mlag>
</config>
"""
CE_NC_DELETE_PEER_LINK_INFO = """
<config>
<mlag xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <peerlinks>
    <peerlink operation="delete">
      <dfsgroupId>1</dfsgroupId>
      <linkId>%s</linkId>
      <portName>%s</portName>
    </peerlink>
  </peerlinks>
</mlag>
</config>
"""


def is_valid_address(address):
    """check ip-address is valid"""

    if address.find('.') != -1:
        addr_list = address.split('.')
        if len(addr_list) != 4:
            return False
        for each_num in addr_list:
            if not each_num.isdigit():
                return False
            if int(each_num) > 255:
                return False
        return True

    return False


class MlagConfig(object):
    """
    Manages Manages MLAG config information.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.dfs_group_id = self.module.params['dfs_group_id']
        self.nickname = self.module.params['nickname']
        self.pseudo_nickname = self.module.params['pseudo_nickname']
        self.pseudo_priority = self.module.params['pseudo_priority']
        self.ip_address = self.module.params['ip_address']
        self.vpn_instance_name = self.module.params['vpn_instance_name']
        self.priority_id = self.module.params['priority_id']
        self.eth_trunk_id = self.module.params['eth_trunk_id']
        self.peer_link_id = self.module.params['peer_link_id']
        self.state = self.module.params['state']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.existing = dict()
        self.proposed = dict()
        self.end_state = dict()

        self.commands = list()
        # DFS group info
        self.dfs_group_info = None
        # peer link info
        self.peer_link_info = None

    def init_module(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, con_obj, xml_name):
        """Check if response message is already succeed."""

        xml_str = con_obj.xml
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

    def get_dfs_group_info(self):
        """ get dfs group attributes info."""

        dfs_group_info = dict()
        conf_str = CE_NC_GET_DFS_GROUP_INFO
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return dfs_group_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
            root = ElementTree.fromstring(xml_str)
            dfs_info = root.findall(
                "data/dfs/groupInstances/groupInstance")
            if dfs_info:
                for tmp in dfs_info:
                    for site in tmp:
                        if site.tag in ["groupId", "priority", "ipAddress", "srcVpnName"]:
                            dfs_group_info[site.tag] = site.text

            dfs_nick_info = root.findall(
                "data/dfs/groupInstances/groupInstance/trillType")

            if dfs_nick_info:
                for tmp in dfs_nick_info:
                    for site in tmp:
                        if site.tag in ["localNickname", "pseudoNickname", "pseudoPriority"]:
                            dfs_group_info[site.tag] = site.text
            return dfs_group_info

    def get_peer_link_info(self):
        """ get peer link info."""

        peer_link_info = dict()
        conf_str = CE_NC_GET_PEER_LINK_INFO
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return peer_link_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            link_info = root.findall(
                "data/mlag/peerlinks/peerlink")

            if link_info:
                for tmp in link_info:
                    for site in tmp:
                        if site.tag in ["linkId", "portName"]:
                            peer_link_info[site.tag] = site.text
            return peer_link_info

    def is_dfs_group_info_change(self):
        """whether dfs group info"""
        if not self.dfs_group_info:
            return False

        if self.priority_id and self.dfs_group_info["priority"] != self.priority_id:
            return True
        if self.ip_address and self.dfs_group_info["ipAddress"] != self.ip_address:
            return True
        if self.vpn_instance_name and self.dfs_group_info["srcVpnName"] != self.vpn_instance_name:
            return True
        if self.nickname and self.dfs_group_info["localNickname"] != self.nickname:
            return True
        if self.pseudo_nickname and self.dfs_group_info["pseudoNickname"] != self.pseudo_nickname:
            return True
        if self.pseudo_priority and self.dfs_group_info["pseudoPriority"] != self.pseudo_priority:
            return True
        return False

    def check_dfs_group_info_change(self):
        """check dfs group info"""
        if not self.dfs_group_info:
            return True

        if self.priority_id and self.dfs_group_info["priority"] == self.priority_id:
            return True
        if self.ip_address and self.dfs_group_info["ipAddress"] == self.ip_address:
            return True
        if self.vpn_instance_name and self.dfs_group_info["srcVpnName"] == self.vpn_instance_name:
            return True
        if self.nickname and self.dfs_group_info["localNickname"] == self.nickname:
            return True
        if self.pseudo_nickname and self.dfs_group_info["pseudoNickname"] == self.pseudo_nickname:
            return True
        if self.pseudo_priority and self.dfs_group_info["pseudoPriority"] == self.pseudo_priority:
            return True
        return False

    def modify_dfs_group(self):
        """modify dfs group info"""

        if self.is_dfs_group_info_change():

            conf_str = CE_NC_MERGE_DFS_GROUP_INFO_HEADER % self.dfs_group_id
            if self.priority_id and self.dfs_group_info["priority"] != self.priority_id:
                conf_str += "<priority>%s</priority>" % self.priority_id
            if self.ip_address and self.dfs_group_info["ipAddress"] != self.ip_address:
                conf_str += "<ipAddress>%s</ipAddress>" % self.ip_address
            if self.vpn_instance_name and self.dfs_group_info["srcVpnName"] != self.vpn_instance_name:
                if not self.ip_address:
                    self.module.fail_json(
                        msg='Error: ip_address can not be null if vpn_instance_name is exist.')
                conf_str += "<srcVpnName>%s</srcVpnName>" % self.vpn_instance_name

            if self.nickname or self.pseudo_nickname or self.pseudo_priority:
                conf_str += "<trillType>"
                if self.nickname and self.dfs_group_info["localNickname"] != self.nickname:
                    conf_str += "<localNickname>%s</localNickname>" % self.nickname
                if self.pseudo_nickname and self.dfs_group_info["pseudoNickname"] != self.pseudo_nickname:
                    conf_str += "<pseudoNickname>%s</pseudoNickname>" % self.pseudo_nickname

                if self.pseudo_priority and self.dfs_group_info["pseudoPriority"] != self.pseudo_priority:
                    if not self.pseudo_nickname:
                        self.module.fail_json(
                            msg='Error: pseudo_nickname can not be null if pseudo_priority is exist.')
                    conf_str += "<pseudoPriority>%s</pseudoPriority>" % self.pseudo_priority
                conf_str += "</trillType>"

            conf_str += CE_NC_MERGE_DFS_GROUP_INFO_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: Merge DFS group info failed.')

            self.updates_cmd.append("dfs-group 1")
            if self.priority_id:
                self.updates_cmd.append("priority %s" % self.priority_id)
            if self.ip_address:
                if self.vpn_instance_name:
                    self.updates_cmd.append(
                        "source ip %s vpn-instance %s" % (self.ip_address, self.vpn_instance_name))
                else:
                    self.updates_cmd.append("source ip %s" % self.ip_address)
            if self.nickname:
                self.updates_cmd.append("source nickname %s" % self.nickname)
            if self.pseudo_nickname:
                if self.pseudo_priority:
                    self.updates_cmd.append(
                        "pseudo-nickname %s priority %s" % (self.pseudo_nickname, self.pseudo_priority))
                else:
                    self.updates_cmd.append(
                        "pseudo-nickname %s" % self.pseudo_nickname)

            self.changed = True

    def create_dfs_group(self):
        """create dfs group info"""

        conf_str = CE_NC_CREATE_DFS_GROUP_INFO_HEADER % self.dfs_group_id
        if self.priority_id and self.priority_id != 100:
            conf_str += "<priority>%s</priority>" % self.priority_id
        if self.ip_address:
            conf_str += "<ipAddress>%s</ipAddress>" % self.ip_address
        if self.vpn_instance_name:
            if not self.ip_address:
                self.module.fail_json(
                    msg='Error: ip_address can not be null if vpn_instance_name is exist.')
            conf_str += "<srcVpnName>%s</srcVpnName>" % self.vpn_instance_name

        if self.nickname or self.pseudo_nickname or self.pseudo_priority:
            conf_str += "<trillType>"
            if self.nickname:
                conf_str += "<localNickname>%s</localNickname>" % self.nickname
            if self.pseudo_nickname:
                conf_str += "<pseudoNickname>%s</pseudoNickname>" % self.pseudo_nickname
            if self.pseudo_priority:
                if not self.pseudo_nickname:
                    self.module.fail_json(
                        msg='Error: pseudo_nickname can not be null if pseudo_priority is exist.')
                conf_str += "<pseudoPriority>%s</pseudoPriority>" % self.pseudo_priority
            conf_str += "</trillType>"

        conf_str += CE_NC_CREATE_DFS_GROUP_INFO_TAIL
        recv_xml = set_nc_config(self.module, conf_str)
        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Merge DFS group info failed.')

        self.updates_cmd.append("dfs-group 1")
        if self.priority_id:
            self.updates_cmd.append("priority %s" % self.priority_id)
        if self.ip_address:
            if self.vpn_instance_name:
                self.updates_cmd.append(
                    "source ip %s vpn-instance %s" % (self.ip_address, self.vpn_instance_name))
            else:
                self.updates_cmd.append("source ip %s" % self.ip_address)
        if self.nickname:
            self.updates_cmd.append("source nickname %s" % self.nickname)
        if self.pseudo_nickname:
            if self.pseudo_priority:
                self.updates_cmd.append(
                    "pseudo-nickname %s priority %s" % (self.pseudo_nickname, self.pseudo_priority))
            else:
                self.updates_cmd.append(
                    "pseudo-nickname %s" % self.pseudo_nickname)

        self.changed = True

    def delete_dfs_group(self):
        """delete dfg group"""

        conf_str = CE_NC_DELETE_DFS_GROUP_INFO_HEADER % self.dfs_group_id
        conf_str += CE_NC_DELETE_DFS_GROUP_INFO_TAIL

        recv_xml = set_nc_config(self.module, conf_str)
        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Delete DFS group id failed.')
        self.updates_cmd.append("undo dfs-group 1")
        self.changed = True

    def delete_dfs_group_attribute(self):
        """delete dfg group attribute info"""

        cmd = "dfs-group %s" % self.dfs_group_id
        self.cli_add_command(cmd)
        change = False
        if self.priority_id and self.dfs_group_info["priority"] == self.priority_id:
            cmd = "priority %s" % self.priority_id
            self.cli_add_command(cmd, True)
            change = True

        if self.ip_address and self.dfs_group_info["ipAddress"] == self.ip_address:
            if self.vpn_instance_name and self.dfs_group_info["srcVpnName"] == self.vpn_instance_name:
                cmd = "source ip %s vpn-instance %s" % (
                    self.ip_address, self.vpn_instance_name)
                self.cli_add_command(cmd, True)
            else:
                cmd = "source ip %s" % self.ip_address
                self.cli_add_command(cmd, True)
            change = True

        if self.nickname and self.dfs_group_info["localNickname"] == self.nickname:
            cmd = "source nickname %s" % self.nickname
            self.cli_add_command(cmd, True)
            change = True
        if self.pseudo_nickname and self.dfs_group_info["pseudoNickname"] == self.pseudo_nickname:
            if self.pseudo_priority:
                cmd = "pseudo-nickname %s priority %s" % (
                    self.pseudo_nickname, self.pseudo_priority)
                self.cli_add_command(cmd, True)
            else:
                cmd = "pseudo-nickname %s" % self.pseudo_nickname
                self.cli_add_command(cmd, True)
            change = True
        if change:
            self.cli_load_config(self.commands)
            self.changed = True

    def modify_peer_link(self):
        """modify peer link info"""

        eth_trunk_id = "Eth-Trunk"
        eth_trunk_id += self.eth_trunk_id
        conf_str = CE_NC_MERGE_PEER_LINK_INFO % (
            self.peer_link_id, eth_trunk_id)
        recv_xml = set_nc_config(self.module, conf_str)
        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Merge peer link failed.')
        self.updates_cmd.append("peer-link %s" % self.peer_link_id)
        self.changed = True

    def delete_peer_link(self):
        """delete peer link info"""

        eth_trunk_id = "Eth-Trunk"
        eth_trunk_id += self.eth_trunk_id
        conf_str = CE_NC_DELETE_PEER_LINK_INFO % (
            self.peer_link_id, eth_trunk_id)
        recv_xml = set_nc_config(self.module, conf_str)
        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Delete peer link failed.')
        self.updates_cmd.append("undo peer-link %s" % self.peer_link_id)
        self.changed = True

    def check_params(self):
        """Check all input params"""

        # dfs_group_id check
        if self.dfs_group_id:
            if self.dfs_group_id != "1":
                self.module.fail_json(
                    msg='Error: The value of dfs_group_id must be 1.')

        # nickname check
        if self.nickname:
            if not self.nickname.isdigit():
                self.module.fail_json(
                    msg='Error: The value of nickname is an integer.')
            if int(self.nickname) < 1 or int(self.nickname) > 65471:
                self.module.fail_json(
                    msg='Error: The nickname is not in the range from 1 to 65471.')

        # pseudo_nickname check
        if self.pseudo_nickname:
            if not self.pseudo_nickname.isdigit():
                self.module.fail_json(
                    msg='Error: The value of pseudo_nickname is an integer.')
            if int(self.pseudo_nickname) < 1 or int(self.pseudo_nickname) > 65471:
                self.module.fail_json(
                    msg='Error: The pseudo_nickname is not in the range from 1 to 65471.')

        # pseudo_priority check
        if self.pseudo_priority:
            if not self.pseudo_priority.isdigit():
                self.module.fail_json(
                    msg='Error: The value of pseudo_priority is an integer.')
            if int(self.pseudo_priority) < 128 or int(self.pseudo_priority) > 255:
                self.module.fail_json(
                    msg='Error: The pseudo_priority is not in the range from 128 to 255.')

        # ip_address check
        if self.ip_address:
            if not is_valid_address(self.ip_address):
                self.module.fail_json(
                    msg='Error: The %s is not a valid ip address.' % self.ip_address)

        # vpn_instance_name check
        if self.vpn_instance_name:
            if len(self.vpn_instance_name) > 31 \
                    or len(self.vpn_instance_name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: The length of vpn_instance_name is not in the range from 1 to 31.')

        # priority_id check
        if self.priority_id:
            if not self.priority_id.isdigit():
                self.module.fail_json(
                    msg='Error: The value of priority_id is an integer.')
            if int(self.priority_id) < 1 or int(self.priority_id) > 254:
                self.module.fail_json(
                    msg='Error: The priority_id is not in the range from 1 to 254.')

        # peer_link_id check
        if self.peer_link_id:
            if self.peer_link_id != "1":
                self.module.fail_json(
                    msg='Error: The value of peer_link_id must be 1.')

        # eth_trunk_id check
        if self.eth_trunk_id:
            if not self.eth_trunk_id.isdigit():
                self.module.fail_json(
                    msg='Error: The value of eth_trunk_id is an integer.')
            if int(self.eth_trunk_id) < 0 or int(self.eth_trunk_id) > 511:
                self.module.fail_json(
                    msg='Error: The value of eth_trunk_id is not in the range from 0 to 511.')

    def get_proposed(self):
        """get proposed info"""

        if self.dfs_group_id:
            self.proposed["dfs_group_id"] = self.dfs_group_id
        if self.nickname:
            self.proposed["nickname"] = self.nickname
        if self.pseudo_nickname:
            self.proposed["pseudo_nickname"] = self.pseudo_nickname
        if self.pseudo_priority:
            self.proposed["pseudo_priority"] = self.pseudo_priority
        if self.ip_address:
            self.proposed["ip_address"] = self.ip_address
        if self.vpn_instance_name:
            self.proposed["vpn_instance_name"] = self.vpn_instance_name
        if self.priority_id:
            self.proposed["priority_id"] = self.priority_id
        if self.eth_trunk_id:
            self.proposed["eth_trunk_id"] = self.eth_trunk_id
        if self.peer_link_id:
            self.proposed["peer_link_id"] = self.peer_link_id
        if self.state:
            self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        if self.dfs_group_id:
            self.dfs_group_info = self.get_dfs_group_info()
        if self.peer_link_id and not self.eth_trunk_id:
            self.peer_link_info = self.get_peer_link_info()
        if self.dfs_group_info:
            if self.dfs_group_id:
                self.existing["dfs_group_id"] = self.dfs_group_info["groupId"]
            if self.nickname:
                self.existing["nickname"] = self.dfs_group_info[
                    "localNickname"]
            if self.pseudo_nickname:
                self.existing["pseudo_nickname"] = self.dfs_group_info[
                    "pseudoNickname"]
            if self.pseudo_priority:
                self.existing["pseudo_priority"] = self.dfs_group_info[
                    "pseudoPriority"]
            if self.ip_address:
                self.existing["ip_address"] = self.dfs_group_info["ipAddress"]
            if self.vpn_instance_name:
                self.existing["vpn_instance_name"] = self.dfs_group_info[
                    "srcVpnName"]
            if self.priority_id:
                self.existing["priority_id"] = self.dfs_group_info["priority"]
        if self.peer_link_info:
            if self.eth_trunk_id:
                self.existing["eth_trunk_id"] = self.peer_link_info["portName"]
            if self.peer_link_id:
                self.existing["peer_link_id"] = self.peer_link_info["linkId"]

    def get_end_state(self):
        """get end state info"""
        if self.dfs_group_id:
            self.dfs_group_info = self.get_dfs_group_info()
        if self.peer_link_id and not self.eth_trunk_id:
            self.peer_link_info = self.get_peer_link_info()

        if self.dfs_group_info:
            if self.dfs_group_id:
                self.end_state["dfs_group_id"] = self.dfs_group_info["groupId"]
            if self.nickname:
                self.end_state["nickname"] = self.dfs_group_info[
                    "localNickname"]
            if self.pseudo_nickname:
                self.end_state["pseudo_nickname"] = self.dfs_group_info[
                    "pseudoNickname"]
            if self.pseudo_priority:
                self.end_state["pseudo_priority"] = self.dfs_group_info[
                    "pseudoPriority"]
            if self.ip_address:
                self.end_state["ip_address"] = self.dfs_group_info["ipAddress"]
            if self.vpn_instance_name:
                self.end_state["vpn_instance_name"] = self.dfs_group_info[
                    "srcVpnName"]
            if self.priority_id:
                self.end_state["priority_id"] = self.dfs_group_info["priority"]
        if self.peer_link_info:
            if self.eth_trunk_id:
                self.end_state[
                    "eth_trunk_id"] = self.peer_link_info["portName"]
            if self.peer_link_id:
                self.end_state["peer_link_id"] = self.peer_link_info["linkId"]

    def work(self):
        """worker"""

        self.check_params()
        self.get_existing()
        self.get_proposed()
        if self.dfs_group_id:
            if self.state == "present":
                if self.dfs_group_info:
                    if self.nickname or self.pseudo_nickname or self.pseudo_priority or self.priority_id \
                            or self.ip_address or self.vpn_instance_name:
                        if self.nickname:
                            if self.dfs_group_info["ipAddress"] != "0.0.0.0":
                                self.module.fail_json(msg='Error: nickname and ip_address can not be exist at the '
                                                          'same time.')
                        if self.ip_address:
                            if self.dfs_group_info["localNickname"] != "0":
                                self.module.fail_json(msg='Error: nickname and ip_address can not be exist at the '
                                                          'same time.')
                        self.modify_dfs_group()
                else:
                    self.create_dfs_group()
            else:
                if not self.dfs_group_info:
                    self.module.fail_json(
                        msg='Error: DFS Group does not exist.')
                if not self.nickname and not self.pseudo_nickname and not self.pseudo_priority and not self.priority_id\
                        and not self.ip_address and not self.vpn_instance_name:
                    self.delete_dfs_group()
                else:
                    self.delete_dfs_group_attribute()

        if self.eth_trunk_id and not self.peer_link_id:
            self.module.fail_json(
                msg='Error: eth_trunk_id and peer_link_id must be config at the same time.')
        if self.peer_link_id and not self.eth_trunk_id:
            self.module.fail_json(
                msg='Error: eth_trunk_id and peer_link_id must be config at the same time.')

        if self.eth_trunk_id and self.peer_link_id:
            if self.state == "present":
                self.modify_peer_link()
            else:
                if self.peer_link_info:
                    self.delete_peer_link()

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
        dfs_group_id=dict(type='str'),
        nickname=dict(type='str'),
        pseudo_nickname=dict(type='str'),
        pseudo_priority=dict(type='str'),
        ip_address=dict(type='str'),
        vpn_instance_name=dict(type='str'),
        priority_id=dict(type='str'),
        eth_trunk_id=dict(type='str'),
        peer_link_id=dict(type='str'),
        state=dict(type='str', default='present',
                   choices=['present', 'absent'])
    )
    argument_spec.update(ce_argument_spec)
    module = MlagConfig(argument_spec=argument_spec)
    module.work()


if __name__ == '__main__':
    main()
