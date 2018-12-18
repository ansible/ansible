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
module: ce_vxlan_tunnel
version_added: "2.4"
short_description: Manages VXLAN tunnel configuration on HUAWEI CloudEngine devices.
description:
    - This module offers the ability to set the VNI and mapped to the BD,
      and configure an ingress replication list on HUAWEI CloudEngine devices.
author:
    - Li Yanfeng (@QijunPan)
options:
    bridge_domain_id:
        description:
            - Specifies a bridge domain ID. The value is an integer ranging from 1 to 16777215.
    vni_id:
        description:
            - Specifies a VXLAN network identifier (VNI) ID. The value is an integer ranging from 1 to 16000000.
    nve_name:
        description:
            - Specifies the number of an NVE interface. The value ranges from 1 to 2.
    nve_mode:
        description:
            - Specifies the working mode of an NVE interface.
        choices: ['mode-l2','mode-l3']
    peer_list_ip:
        description:
            - Specifies the IP address of a remote VXLAN tunnel endpoints (VTEP).
              The value is in dotted decimal notation.
    protocol_type:
        description:
            - The operation type of routing protocol.
        choices: ['bgp','null']
    source_ip:
        description:
            - Specifies an IP address for a source VTEP. The value is in dotted decimal notation.
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
- name: vxlan tunnel module test
  hosts: ce128
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

  - name: Make sure nve_name is exist, ensure vni_id and protocol_type is configured on Nve1 interface.
    ce_vxlan_tunnel:
      nve_name: Nve1
      vni_id: 100
      protocol_type: bgp
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {nve_interface_name": "Nve1", nve_mode": "mode-l2", "source_ip": "0.0.0.0"}
existing:
    description:
        - k/v pairs of existing rollback
    returned: always
    type: dict
    sample: {nve_interface_name": "Nve1", nve_mode": "mode-l3", "source_ip": "0.0.0.0"}

updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface Nve1",
             "mode l3"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {nve_interface_name": "Nve1", nve_mode": "mode-l3", "source_ip": "0.0.0.0"}
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, get_config, ce_argument_spec

CE_NC_GET_VNI_BD_INFO = """
<filter type="subtree">
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Vni2Bds>
      <nvo3Vni2Bd>
        <vniId></vniId>
        <bdId></bdId>
      </nvo3Vni2Bd>
    </nvo3Vni2Bds>
  </nvo3>
</filter>
"""

CE_NC_GET_NVE_INFO = """
<filter type="subtree">
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Nves>
      <nvo3Nve>
        <ifName>%s</ifName>
      </nvo3Nve>
    </nvo3Nves>
  </nvo3>
</filter>
"""

CE_NC_MERGE_VNI_BD_ID = """
<config>
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Vni2Bds>
      <nvo3Vni2Bd operation="create">
        <vniId>%s</vniId>
        <bdId>%s</bdId>
      </nvo3Vni2Bd>
    </nvo3Vni2Bds>
  </nvo3>
</config>
"""

CE_NC_DELETE_VNI_BD_ID = """
<config>
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Vni2Bds>
      <nvo3Vni2Bd operation="delete">
        <vniId>%s</vniId>
        <bdId>%s</bdId>
      </nvo3Vni2Bd>
    </nvo3Vni2Bds>
  </nvo3>
</config>
"""

CE_NC_MERGE_NVE_MODE = """
<config>
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Nves>
      <nvo3Nve operation="merge">
        <ifName>%s</ifName>
        <nveType>%s</nveType>
      </nvo3Nve>
    </nvo3Nves>
  </nvo3>
</config>
"""

CE_NC_MERGE_NVE_SOURCE_IP_PROTOCOL = """
<config>
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Nves>
      <nvo3Nve operation="merge">
        <ifName>%s</ifName>
        <srcAddr>%s</srcAddr>
      </nvo3Nve>
    </nvo3Nves>
  </nvo3>
</config>
"""

CE_NC_MERGE_VNI_PEER_ADDRESS_IP_HEAD = """
<config>
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Nves>
      <nvo3Nve>
        <ifName>%s</ifName>
        <vniMembers>
          <vniMember>
            <vniId>%s</vniId>
"""

CE_NC_MERGE_VNI_PEER_ADDRESS_IP_END = """
          </vniMember>
        </vniMembers>
      </nvo3Nve>
    </nvo3Nves>
  </nvo3>
</config>
"""
CE_NC_MERGE_VNI_PEER_ADDRESS_IP_MERGE = """
<nvo3VniPeers>
  <nvo3VniPeer operation="merge">
    <peerAddr>%s</peerAddr>
  </nvo3VniPeer>
</nvo3VniPeers>
"""

CE_NC_DELETE_VNI_PEER_ADDRESS_IP_HEAD = """
<config>
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Nves>
      <nvo3Nve>
        <ifName>%s</ifName>
        <vniMembers>
          <vniMember operation="delete">
            <vniId>%s</vniId>
"""
CE_NC_DELETE_VNI_PEER_ADDRESS_IP_END = """
          </vniMember>
        </vniMembers>
      </nvo3Nve>
    </nvo3Nves>
  </nvo3>
</config>
"""
CE_NC_DELETE_VNI_PEER_ADDRESS_IP_DELETE = """
<nvo3VniPeers>
  <nvo3VniPeer operation="delete">
    <peerAddr>%s</peerAddr>
  </nvo3VniPeer>
</nvo3VniPeers>
"""

CE_NC_DELETE_PEER_ADDRESS_IP_HEAD = """
<config>
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Nves>
      <nvo3Nve>
        <ifName>%s</ifName>
        <vniMembers>
          <vniMember>
            <vniId>%s</vniId>
"""
CE_NC_DELETE_PEER_ADDRESS_IP_END = """
          </vniMember>
        </vniMembers>
      </nvo3Nve>
    </nvo3Nves>
  </nvo3>
</config>
"""
CE_NC_MERGE_VNI_PROTOCOL = """
<config>
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Nves>
      <nvo3Nve>
        <ifName>%s</ifName>
        <vniMembers>
          <vniMember operation="merge">
            <vniId>%s</vniId>
            <protocol>%s</protocol>
          </vniMember>
        </vniMembers>
      </nvo3Nve>
    </nvo3Nves>
  </nvo3>
</config>
"""

CE_NC_DELETE_VNI_PROTOCOL = """
<config>
  <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <nvo3Nves>
      <nvo3Nve>
        <ifName>%s</ifName>
        <vniMembers>
          <vniMember operation="delete">
            <vniId>%s</vniId>
            <protocol>%s</protocol>
          </vniMember>
        </vniMembers>
      </nvo3Nve>
    </nvo3Nves>
  </nvo3>
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


class VxlanTunnel(object):
    """
    Manages vxlan tunnel configuration.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.bridge_domain_id = self.module.params['bridge_domain_id']
        self.vni_id = self.module.params['vni_id']
        self.nve_name = self.module.params['nve_name']
        self.nve_mode = self.module.params['nve_mode']
        self.peer_list_ip = self.module.params['peer_list_ip']
        self.protocol_type = self.module.params['protocol_type']
        self.source_ip = self.module.params['source_ip']
        self.state = self.module.params['state']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.existing = dict()
        self.proposed = dict()
        self.end_state = dict()

        # configuration nve info
        self.vni2bd_info = None
        self.nve_info = None

    def init_module(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_current_config(self, vni_id, peer_ip_list):
        """get current configuration"""

        flags = list()
        exp = " | include vni "
        exp += vni_id
        exp += " head-end peer-list "
        for peer_ip in peer_ip_list:
            exp += "| exclude %s " % peer_ip
        flags.append(exp)
        return get_config(self.module, flags)

    def get_vni2bd_dict(self):
        """ get vni2bd attributes dict."""

        vni2bd_info = dict()
        # get vni bd info
        conf_str = CE_NC_GET_VNI_BD_INFO
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return vni2bd_info
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        # get vni to bridge domain id info
        root = ElementTree.fromstring(xml_str)
        vni2bd_info["vni2BdInfos"] = list()
        vni2bds = root.findall("data/nvo3/nvo3Vni2Bds/nvo3Vni2Bd")

        if vni2bds:
            for vni2bd in vni2bds:
                vni_dict = dict()
                for ele in vni2bd:
                    if ele.tag in ["vniId", "bdId"]:
                        vni_dict[ele.tag] = ele.text
                vni2bd_info["vni2BdInfos"].append(vni_dict)

        return vni2bd_info

    def check_nve_interface(self, nve_name):
        """is nve interface exist"""

        if not self.nve_info:
            return False

        if self.nve_info["ifName"] == nve_name:
            return True
        return False

    def get_nve_dict(self, nve_name):
        """ get nve interface attributes dict."""

        nve_info = dict()
        # get nve info
        conf_str = CE_NC_GET_NVE_INFO % nve_name
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return nve_info
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get nve info
        root = ElementTree.fromstring(xml_str)
        nvo3 = root.find("data/nvo3/nvo3Nves/nvo3Nve")
        if nvo3:
            for nve in nvo3:
                if nve.tag in ["srcAddr", "ifName", "nveType"]:
                    nve_info[nve.tag] = nve.text

        # get nve vni info
        nve_info["vni_peer_protocols"] = list()

        vni_members = root.findall(
            "data/nvo3/nvo3Nves/nvo3Nve/vniMembers/vniMember")
        if vni_members:
            for member in vni_members:
                vni_dict = dict()
                for ele in member:
                    if ele.tag in ["vniId", "protocol"]:
                        vni_dict[ele.tag] = ele.text
                nve_info["vni_peer_protocols"].append(vni_dict)

        # get vni peer address ip info
        nve_info["vni_peer_ips"] = list()
        vni_peers = root.findall(
            "data/nvo3/nvo3Nves/nvo3Nve/vniMembers/vniMember/nvo3VniPeers/nvo3VniPeer")
        if vni_peers:
            for peer_address in vni_peers:
                vni_peer_dict = dict()
                for ele in peer_address:
                    if ele.tag in ["vniId", "peerAddr"]:
                        vni_peer_dict[ele.tag] = ele.text
                nve_info["vni_peer_ips"].append(vni_peer_dict)

        return nve_info

    def check_nve_name(self):
        """Gets Nve interface name"""

        if self.nve_name is None:
            return False
        if self.nve_name in ["Nve1", "Nve2"]:
            return True
        return False

    def is_vni_bd_exist(self, vni_id, bd_id):
        """is vni to bridge-domain-id exist"""

        if not self.vni2bd_info:
            return False

        for vni2bd in self.vni2bd_info["vni2BdInfos"]:
            if vni2bd["vniId"] == vni_id and vni2bd["bdId"] == bd_id:
                return True
        return False

    def is_vni_bd_change(self, vni_id, bd_id):
        """is vni to bridge-domain-id change"""

        if not self.vni2bd_info:
            return True

        for vni2bd in self.vni2bd_info["vni2BdInfos"]:
            if vni2bd["vniId"] == vni_id and vni2bd["bdId"] == bd_id:
                return False
        return True

    def is_nve_mode_exist(self, nve_name, mode):
        """is nve interface mode exist"""

        if not self.nve_info:
            return False

        if self.nve_info["ifName"] == nve_name and self.nve_info["nveType"] == mode:
            return True
        return False

    def is_nve_mode_change(self, nve_name, mode):
        """is nve interface mode change"""

        if not self.nve_info:
            return True

        if self.nve_info["ifName"] == nve_name and self.nve_info["nveType"] == mode:
            return False
        return True

    def is_nve_source_ip_exist(self, nve_name, source_ip):
        """is vni to bridge-domain-id exist"""

        if not self.nve_info:
            return False

        if self.nve_info["ifName"] == nve_name and self.nve_info["srcAddr"] == source_ip:
            return True
        return False

    def is_nve_source_ip_change(self, nve_name, source_ip):
        """is vni to bridge-domain-id change"""

        if not self.nve_info:
            return True

        if self.nve_info["ifName"] == nve_name and self.nve_info["srcAddr"] == source_ip:
            return False
        return True

    def is_vni_protocol_exist(self, nve_name, vni_id, protocol_type):
        """is vni protocol exist"""

        if not self.nve_info:
            return False
        if self.nve_info["ifName"] == nve_name:
            for member in self.nve_info["vni_peer_protocols"]:
                if member["vniId"] == vni_id and member["protocol"] == protocol_type:
                    return True
        return False

    def is_vni_protocol_change(self, nve_name, vni_id, protocol_type):
        """is vni protocol change"""

        if not self.nve_info:
            return True
        if self.nve_info["ifName"] == nve_name:
            for member in self.nve_info["vni_peer_protocols"]:
                if member["vniId"] == vni_id and member["protocol"] == protocol_type:
                    return False
        return True

    def is_vni_peer_list_exist(self, nve_name, vni_id, peer_ip):
        """is vni peer list exist"""

        if not self.nve_info:
            return False
        if self.nve_info["ifName"] == nve_name:
            for member in self.nve_info["vni_peer_ips"]:
                if member["vniId"] == vni_id and member["peerAddr"] == peer_ip:
                    return True
        return False

    def is_vni_peer_list_change(self, nve_name, vni_id, peer_ip_list):
        """is vni peer list change"""

        if not self.nve_info:
            return True
        for peer_ip in peer_ip_list:
            if self.nve_info["ifName"] == nve_name:
                if not self.nve_info["vni_peer_ips"]:
                    return True
                for member in self.nve_info["vni_peer_ips"]:
                    if member["vniId"] != vni_id:
                        return True
                    elif member["vniId"] == vni_id and member["peerAddr"] != peer_ip:
                        return True
        return False

    def config_merge_vni2bd(self, bd_id, vni_id):
        """config vni to bd id"""

        if self.is_vni_bd_change(vni_id, bd_id):
            cfg_xml = CE_NC_MERGE_VNI_BD_ID % (vni_id, bd_id)
            recv_xml = set_nc_config(self.module, cfg_xml)
            self.check_response(recv_xml, "MERGE_VNI_BD")
            self.updates_cmd.append("bridge-domain %s" % bd_id)
            self.updates_cmd.append("vxlan vni %s" % vni_id)
            self.changed = True

    def config_merge_mode(self, nve_name, mode):
        """config nve mode"""

        if self.is_nve_mode_change(nve_name, mode):
            cfg_xml = CE_NC_MERGE_NVE_MODE % (nve_name, mode)
            recv_xml = set_nc_config(self.module, cfg_xml)
            self.check_response(recv_xml, "MERGE_MODE")
            self.updates_cmd.append("interface %s" % nve_name)
            self.updates_cmd.append("mode l3")
            self.changed = True

    def config_merge_source_ip(self, nve_name, source_ip):
        """config nve source ip"""

        if self.is_nve_source_ip_change(nve_name, source_ip):
            cfg_xml = CE_NC_MERGE_NVE_SOURCE_IP_PROTOCOL % (
                nve_name, source_ip)
            recv_xml = set_nc_config(self.module, cfg_xml)
            self.check_response(recv_xml, "MERGE_SOURCE_IP")
            self.updates_cmd.append("interface %s" % nve_name)
            self.updates_cmd.append("source %s" % source_ip)
            self.changed = True

    def config_merge_vni_peer_ip(self, nve_name, vni_id, peer_ip_list):
        """config vni peer ip"""

        if self.is_vni_peer_list_change(nve_name, vni_id, peer_ip_list):
            cfg_xml = CE_NC_MERGE_VNI_PEER_ADDRESS_IP_HEAD % (
                nve_name, vni_id)
            for peer_ip in peer_ip_list:
                cfg_xml += CE_NC_MERGE_VNI_PEER_ADDRESS_IP_MERGE % peer_ip
            cfg_xml += CE_NC_MERGE_VNI_PEER_ADDRESS_IP_END
            recv_xml = set_nc_config(self.module, cfg_xml)
            self.check_response(recv_xml, "MERGE_VNI_PEER_IP")
            self.updates_cmd.append("interface %s" % nve_name)

            for peer_ip in peer_ip_list:
                cmd_output = "vni %s head-end peer-list %s" % (vni_id, peer_ip)
                self.updates_cmd.append(cmd_output)
            self.changed = True

    def config_merge_vni_protocol_type(self, nve_name, vni_id, protocol_type):
        """config vni protocol type"""

        if self.is_vni_protocol_change(nve_name, vni_id, protocol_type):
            cfg_xml = CE_NC_MERGE_VNI_PROTOCOL % (
                nve_name, vni_id, protocol_type)
            recv_xml = set_nc_config(self.module, cfg_xml)
            self.check_response(recv_xml, "MERGE_VNI_PEER_PROTOCOL")
            self.updates_cmd.append("interface %s" % nve_name)

            if protocol_type == "bgp":
                self.updates_cmd.append(
                    "vni %s head-end peer-list protocol %s" % (vni_id, protocol_type))
            else:
                self.updates_cmd.append(
                    "undo vni %s head-end peer-list protocol bgp" % vni_id)
            self.changed = True

    def config_delete_vni2bd(self, bd_id, vni_id):
        """remove vni to bd id"""

        if not self.is_vni_bd_exist(vni_id, bd_id):
            return
        cfg_xml = CE_NC_DELETE_VNI_BD_ID % (vni_id, bd_id)
        recv_xml = set_nc_config(self.module, cfg_xml)
        self.check_response(recv_xml, "DELETE_VNI_BD")
        self.updates_cmd.append(
            "bridge-domain %s" % bd_id)
        self.updates_cmd.append(
            "undo vxlan vni %s" % vni_id)

        self.changed = True

    def config_delete_mode(self, nve_name, mode):
        """nve mode"""

        if mode == "mode-l3":
            if not self.is_nve_mode_exist(nve_name, mode):
                return
            cfg_xml = CE_NC_MERGE_NVE_MODE % (nve_name, "mode-l2")

            recv_xml = set_nc_config(self.module, cfg_xml)
            self.check_response(recv_xml, "DELETE_MODE")
            self.updates_cmd.append("interface %s" % nve_name)
            self.updates_cmd.append("undo mode l3")
            self.changed = True
        else:
            self.module.fail_json(
                msg='Error: Can not configure undo mode l2.')

    def config_delete_source_ip(self, nve_name, source_ip):
        """nve source ip"""

        if not self.is_nve_source_ip_exist(nve_name, source_ip):
            return
        ipaddr = "0.0.0.0"
        cfg_xml = CE_NC_MERGE_NVE_SOURCE_IP_PROTOCOL % (
            nve_name, ipaddr)
        recv_xml = set_nc_config(self.module, cfg_xml)
        self.check_response(recv_xml, "DELETE_SOURCE_IP")
        self.updates_cmd.append("interface %s" % nve_name)
        self.updates_cmd.append("undo source %s" % source_ip)
        self.changed = True

    def config_delete_vni_peer_ip(self, nve_name, vni_id, peer_ip_list):
        """remove vni peer ip"""

        for peer_ip in peer_ip_list:
            if not self.is_vni_peer_list_exist(nve_name, vni_id, peer_ip):
                self.module.fail_json(msg='Error: The %s does not exist' % peer_ip)
        config = self.get_current_config(vni_id, peer_ip_list)
        if not config:
            cfg_xml = CE_NC_DELETE_VNI_PEER_ADDRESS_IP_HEAD % (
                nve_name, vni_id)
            for peer_ip in peer_ip_list:
                cfg_xml += CE_NC_DELETE_VNI_PEER_ADDRESS_IP_DELETE % peer_ip
            cfg_xml += CE_NC_DELETE_VNI_PEER_ADDRESS_IP_END
        else:
            cfg_xml = CE_NC_DELETE_PEER_ADDRESS_IP_HEAD % (
                nve_name, vni_id)
            for peer_ip in peer_ip_list:
                cfg_xml += CE_NC_DELETE_VNI_PEER_ADDRESS_IP_DELETE % peer_ip
            cfg_xml += CE_NC_DELETE_PEER_ADDRESS_IP_END

        recv_xml = set_nc_config(self.module, cfg_xml)
        self.check_response(recv_xml, "DELETE_VNI_PEER_IP")
        self.updates_cmd.append("interface %s" % nve_name)

        for peer_ip in peer_ip_list:
            cmd_output = "undo vni %s head-end peer-list %s" % (vni_id, peer_ip)
            self.updates_cmd.append(cmd_output)

        self.changed = True

    def config_delete_vni_protocol_type(self, nve_name, vni_id, protocol_type):
        """remove vni protocol type"""

        if not self.is_vni_protocol_exist(nve_name, vni_id, protocol_type):
            return

        cfg_xml = CE_NC_DELETE_VNI_PROTOCOL % (nve_name, vni_id, protocol_type)
        recv_xml = set_nc_config(self.module, cfg_xml)
        self.check_response(recv_xml, "DELETE_VNI_PEER_PROTOCOL")
        self.updates_cmd.append("interface %s" % nve_name)
        self.updates_cmd.append(
            "undo vni %s head-end peer-list protocol bgp " % vni_id)
        self.changed = True

    def check_params(self):
        """Check all input params"""

        # bridge_domain_id check
        if self.bridge_domain_id:
            if not self.bridge_domain_id.isdigit():
                self.module.fail_json(
                    msg='Error: The parameter of bridge domain id is invalid.')
            if int(self.bridge_domain_id) > 16777215 or int(self.bridge_domain_id) < 1:
                self.module.fail_json(
                    msg='Error: The bridge domain id must be an integer between 1 and 16777215.')
        # vni_id check
        if self.vni_id:
            if not self.vni_id.isdigit():
                self.module.fail_json(
                    msg='Error: The parameter of vni id is invalid.')
            if int(self.vni_id) > 16000000 or int(self.vni_id) < 1:
                self.module.fail_json(
                    msg='Error: The vni id must be an integer between 1 and 16000000.')

        # nve_name check
        if self.nve_name:
            if not self.check_nve_name():
                self.module.fail_json(
                    msg='Error: Error: NVE interface %s is invalid.' % self.nve_name)

        # peer_list_ip check
        if self.peer_list_ip:
            for peer_ip in self.peer_list_ip:
                if not is_valid_address(peer_ip):
                    self.module.fail_json(
                        msg='Error: The ip address %s is invalid.' % self.peer_list_ip)
        # source_ip check
        if self.source_ip:
            if not is_valid_address(self.source_ip):
                self.module.fail_json(
                    msg='Error: The ip address %s is invalid.' % self.source_ip)

    def get_proposed(self):
        """get proposed info"""

        if self.bridge_domain_id:
            self.proposed["bridge_domain_id"] = self.bridge_domain_id
        if self.vni_id:
            self.proposed["vni_id"] = self.vni_id
        if self.nve_name:
            self.proposed["nve_name"] = self.nve_name
        if self.nve_mode:
            self.proposed["nve_mode"] = self.nve_mode
        if self.peer_list_ip:
            self.proposed["peer_list_ip"] = self.peer_list_ip
        if self.source_ip:
            self.proposed["source_ip"] = self.source_ip
        if self.state:
            self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if self.vni2bd_info:
            self.existing["vni_to_bridge_domain"] = self.vni2bd_info[
                "vni2BdInfos"]

        if self.nve_info:
            self.existing["nve_interface_name"] = self.nve_info["ifName"]
            self.existing["source_ip"] = self.nve_info["srcAddr"]
            self.existing["nve_mode"] = self.nve_info["nveType"]
            self.existing["vni_peer_list_ip"] = self.nve_info[
                "vni_peer_ips"]
            self.existing["vni_peer_list_protocol"] = self.nve_info[
                "vni_peer_protocols"]

    def get_end_state(self):
        """get end state info"""

        vni2bd_info = self.get_vni2bd_dict()
        if vni2bd_info:
            self.end_state["vni_to_bridge_domain"] = vni2bd_info["vni2BdInfos"]

        nve_info = self.get_nve_dict(self.nve_name)
        if nve_info:
            self.end_state["nve_interface_name"] = nve_info["ifName"]
            self.end_state["source_ip"] = nve_info["srcAddr"]
            self.end_state["nve_mode"] = nve_info["nveType"]
            self.end_state["vni_peer_list_ip"] = nve_info[
                "vni_peer_ips"]
            self.end_state["vni_peer_list_protocol"] = nve_info[
                "vni_peer_protocols"]

    def work(self):
        """worker"""

        self.check_params()
        self.vni2bd_info = self.get_vni2bd_dict()
        if self.nve_name:
            self.nve_info = self.get_nve_dict(self.nve_name)
        self.get_existing()
        self.get_proposed()
        # deal present or absent
        if self.state == "present":
            if self.bridge_domain_id and self.vni_id:
                self.config_merge_vni2bd(self.bridge_domain_id, self.vni_id)
            if self.nve_name:
                if self.check_nve_interface(self.nve_name):
                    if self.nve_mode:
                        self.config_merge_mode(self.nve_name, self.nve_mode)
                    if self.source_ip:
                        self.config_merge_source_ip(
                            self.nve_name, self.source_ip)
                    if self.vni_id and self.peer_list_ip:
                        self.config_merge_vni_peer_ip(
                            self.nve_name, self.vni_id, self.peer_list_ip)
                    if self.vni_id and self.protocol_type:
                        self.config_merge_vni_protocol_type(
                            self.nve_name, self.vni_id, self.protocol_type)
                else:
                    self.module.fail_json(
                        msg='Error: Nve interface %s does not exist.' % self.nve_name)

        else:
            if self.bridge_domain_id and self.vni_id:
                self.config_delete_vni2bd(self.bridge_domain_id, self.vni_id)
            if self.nve_name:
                if self.check_nve_interface(self.nve_name):
                    if self.nve_mode:
                        self.config_delete_mode(self.nve_name, self.nve_mode)
                    if self.source_ip:
                        self.config_delete_source_ip(
                            self.nve_name, self.source_ip)
                    if self.vni_id and self.peer_list_ip:
                        self.config_delete_vni_peer_ip(
                            self.nve_name, self.vni_id, self.peer_list_ip)
                    if self.vni_id and self.protocol_type:
                        self.config_delete_vni_protocol_type(
                            self.nve_name, self.vni_id, self.protocol_type)
                else:
                    self.module.fail_json(
                        msg='Error: Nve interface %s does not exist.' % self.nve_name)

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
    """Module main"""

    argument_spec = dict(
        bridge_domain_id=dict(required=False),
        vni_id=dict(required=False, type='str'),
        nve_name=dict(required=False, type='str'),
        nve_mode=dict(required=False, choices=['mode-l2', 'mode-l3']),
        peer_list_ip=dict(required=False, type='list'),
        protocol_type=dict(required=False, type='str', choices=[
            'bgp', 'null']),

        source_ip=dict(required=False),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )
    argument_spec.update(ce_argument_spec)
    module = VxlanTunnel(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
