# -*- coding: utf-8 -*-
# !/usr/bin/python
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
module: ne_ldp_instance_peerinfo
version_added: "2.6"
short_description: Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
description:
    - Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
author: Haoliansheng (@netengine-Ansible)
options:

'''

EXAMPLES = '''
---

- name: NE device mpls module test
  hosts: mydevice
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli
  connection: netconf
  gather_facts: no



  tasks:


  - name: "Query peer infomation"
    ne_ldp_instance_peerinfo: vrfname=_public_ state=query provider="{{ cli }}"
    register: data
    ignore_errors: true

'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "state": "query",
        "vrfname": "_public_"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {
        "ldpPeerInfo": [
            {
                "announcementcapability": "false",
                "keepalivesendtime": "0",
                "labeladvmode": "UNAVAILABLE",
                "mldpmbbcapability": "false",
                "mldpp2mpcapability": "false",
                "peerftflag": "false",
                "peerloopdetect": "false",
                "peerlsrid": "2.2.2.2:0",
                "peermaxpdulen": "0",
                "peerpvlimit": "0",
                "peertportaddr": "2.2.2.2"
            }
        ],
        "vrfname": "_public_"
    },
'''


import sys
import copy
import socket

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_TAIL
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_TAIL

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_value
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_novalue
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_tail
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_tail


class MPLS_ldpInstancePeerInfo(object):
    """Query intance  peer information
       Xpath: /mpls/mplsLdp/ldpInstances/ldpInstance/ldpPeerInfos/ldpPeerInfo
    """

    def __init__(self, argument_spec):
        """Constructor"""

        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.peerlsrid = self.module.params['peerlsrid']
        self.state = self.module.params['state']

        # state
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()

    def init_module(self):
        """init module"""
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def get_ldp_interface_status_dict(self):
        """Get LDP instance interface status
        """
        # Head process
        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        # Body process
        # Just only build key paramters.
        if self.vrfname is not None:
            conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        else:
            conf_str = constr_leaf_novalue(conf_str, "vrfName")

        conf_str = constr_container_head(conf_str, "ldpPeerInfos")
        conf_str = constr_container_head(conf_str, "ldpPeerInfo")
        if self.peerlsrid is not None:
            conf_str = constr_leaf_value(conf_str, "peerLsrid", self.peerlsrid)
        else:
            conf_str = constr_leaf_novalue(conf_str, "peerLsrid")

        # <ldpPeerInfos>
        #  <ldpPeerInfo>
        #    <peerLsrid/>
        #    <peerMaxPduLen/>
        #    <peerLoopDetect/>
        #    <peerFtFlag/>
        #    <peerTportAddr/>
        #    <peerPVLimit/>
        #    <keepaliveSendTime/>
        #    <recoveryTimer/>
        #    <reconnectTimer/>
        #    <labelAdvMode/>
        #    <announcementCapability/>
        #    <mldpP2mpCapability/>
        #    <mldpMBBCapability/>
        #    <vrfName/><<<<<-no need this .
        #  </ldpPeerInfo>
        # </ldpPeerInfos>
        conf_str = constr_leaf_novalue(conf_str, "peerMaxPduLen")
        conf_str = constr_leaf_novalue(conf_str, "peerLoopDetect")
        conf_str = constr_leaf_novalue(conf_str, "peerFtFlag")
        conf_str = constr_leaf_novalue(conf_str, "peerTportAddr")
        conf_str = constr_leaf_novalue(conf_str, "keepaliveSendTime")
        conf_str = constr_leaf_novalue(conf_str, "recoveryTimer")
        conf_str = constr_leaf_novalue(conf_str, "peerPVLimit")
        conf_str = constr_leaf_novalue(conf_str, "reconnectTimer")
        conf_str = constr_leaf_novalue(conf_str, "labelAdvMode")
        conf_str = constr_leaf_novalue(conf_str, "announcementCapability")
        conf_str = constr_leaf_novalue(conf_str, "mldpP2mpCapability")
        conf_str = constr_leaf_novalue(conf_str, "mldpMBBCapability")
        # Tail process
        conf_str = constr_container_tail(conf_str, "ldpPeerInfo")
        conf_str = constr_container_tail(conf_str, "ldpPeerInfos")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return None

        ldpInstance_info = dict()

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        root = ElementTree.fromstring(xml_str)
        ldpInstance = root.find("mpls/mplsLdp/ldpInstances/ldpInstance")
        if len(ldpInstance) != 0:
            for para in ldpInstance:
                if para.tag == "vrfName":
                    ldpInstance_info[para.tag.lower()] = para.text

        # Get the remote peer infomation, remotePeer is the multi record.
        ldpInstance_info["ldpPeerInfo"] = list()
        ldpPeerInfo = root.findall(
            "data/mpls/mplsLdp/ldpInstances/ldpInstance/ldpPeerInfos/ldpPeerInfo")
        if len(ldpPeerInfo) != 0:
            for peerInfo in ldpPeerInfo:
                ldpPeerInfo_dict = dict()
                for ele in peerInfo:
                    ldpPeerInfo_dict[ele.tag.lower()] = ele.text
                ldpInstance_info["ldpPeerInfo"].append(ldpPeerInfo_dict)
        return ldpInstance_info

    def get_proposed(self):
        """Get proposed information"""
        self.proposed["state"] = self.state
        if self.vrfname is not None:
            self.proposed["vrfname"] = self.vrfname
        if self.peerlsrid is not None:
            self.proposed["peerlsrid"] = self.peerlsrid

    def get_existing(self):
        """Get existing configuration"""
        instance_info = self.get_ldp_interface_status_dict()
        if not instance_info:
            return
        self.existing = instance_info

    def work(self):
        """ Main process
        """
        self.get_proposed()
        self.get_existing()
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.module.exit_json(**self.results)


def main():
    """mian flow"""
    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        peerlsrid=dict(required=False, type='str'),
        state=dict(required=False, default='query', choices=['query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpInstancePeerInfo(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
