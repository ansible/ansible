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
module: ne_ldp_instance_interface_status
version_added: "2.6"
short_description: Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
description:
    - Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
author: Haoliansheng (@netengine-Ansible)
options:

'''

EXAMPLES = '''
'''

RETURN = '''
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


class MPLS_ldpInstanceInterfaceStatus(object):
    """Manages configuration of a LDP intance remote peer information
       Xpath: /mpls/mplsLdp/ldpInstances/ldpInstance/ldpInterfaces/ldpInterface/ldpInterfaceStatus
    """

    def __init__(self, argument_spec):
        """Constructor"""

        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.ifname = self.module.params['ifname']
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
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpInterfaces")
        conf_str = constr_container_head(conf_str, "ldpInterface")
        conf_str = constr_leaf_value(conf_str, "ifName", self.ifname)
        #    <ldpInterfaceStatus>
        #      <interfaceState/>
        #     <labelDistMode/>
        #      <negotiatedHelloHoldTime/>
        #      <effectiveMtu/>
        #      <autoConfig/>
        #    </ldpInterfaceStatus>
        conf_str = constr_container_head(conf_str, "ldpInterfaceStatus")
        conf_str = constr_leaf_novalue(conf_str, "interfaceState")
        conf_str = constr_leaf_novalue(conf_str, "labelDistMode")
        conf_str = constr_leaf_novalue(conf_str, "negotiatedHelloHoldTime")
        conf_str = constr_leaf_novalue(conf_str, "effectiveMtu")
        conf_str = constr_leaf_novalue(conf_str, "autoConfig")
        # Tail process
        conf_str = constr_container_tail(conf_str, "ldpInterfaceStatus")
        conf_str = constr_container_tail(conf_str, "ldpInterface")
        conf_str = constr_container_tail(conf_str, "ldpInterfaces")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return None

        ldpInstance_info = dict()
        ldpInstance_info["vrfname"] = self.vrfname
        ldpInstance_info["ifname"] = self.ifname

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        # Get the remote peer infomation, remotePeer is the multi record.
        root = ElementTree.fromstring(xml_str)

        ldpInstance_info["interfaces"] = list()
        ldpInterfaceStatus = root.findall(
            "data/mpls/mplsLdp/ldpInstances/ldpInstance/ldpInterfaces/ldpInterface/ldpInterfaceStatus")
        if len(ldpInterfaceStatus) != 0:
            for interfaceStatu in ldpInterfaceStatus:
                interfaceStatu_dict = dict()
                for ele in interfaceStatu:
                    interfaceStatu_dict[ele.tag.lower()] = ele.text
                ldpInstance_info["interfaces"].append(interfaceStatu_dict)
        return ldpInstance_info

    def get_proposed(self):
        """Get proposed information"""
        self.proposed["state"] = self.state
        self.proposed["vrfname"] = self.vrfname
        self.proposed["ifname"] = self.ifname

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
        ifname=dict(required=True, type='str'),
        state=dict(required=False, default='query', choices=['query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpInstanceInterfaceStatus(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
