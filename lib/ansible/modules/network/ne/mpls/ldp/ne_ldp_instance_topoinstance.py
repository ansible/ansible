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
module: ne_ldp_instance_topoinstance
version_added: "2.6"
short_description: Manages configuration of MPLS LDP interface on HUAWEI netengine switches.
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

import logging
logging.basicConfig(filename='example.log', level=logging.DEBUG)


class MPLS_ldpInstanceTopo(object):
    """Manages configuration of a LDP intance remote peer information
       Xpath: /mpls/mplsLdp/ldpInstances/ldpInstance/ldpTopologyInstances/ldpTopologyInstance
    """

    def __init__(self, argument_spec):
        """Constructor"""

        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.ldptopologyid = self.module.params['ldptopologyid']
        self.ipfamily = self.module.params['ipfamily']
        self.lsptrpolicyname = self.module.params['lsptrpolicyname']
        self.autofrrlsptriggermode = self.module.params['autofrrlsptriggermode']
        self.autofrrlspipprefixname = self.module.params['autofrrlspipprefixname']
        self.state = self.module.params['state']

        # LDP Instance info
        self.ldpInstanceTopo_info = dict()

        # state
        self.changed = False
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init module"""
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """check all input params"""
        # Don't need check , error return by host.

    def check_response(self, xml_str, xml_name):
        """Check if operation is succeed."""
        if "<ok/>" not in xml_str:
            self.module.fail_json(
                msg='Error: %s failed.' % xml_name)

    def get_ldp_InstanceTopo_dict(self):
        """Get LDP instance remote peer inforamtion
        """
        # Head process
        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        # Body process
        # Just only build key paramters.
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpTopologyInstances")
        conf_str = constr_container_head(conf_str, "ldpTopologyInstance")
        conf_str = constr_leaf_value(conf_str, "ldpTopologyId", self.ldptopologyid)
        conf_str = constr_leaf_value(conf_str, "ipFamily", self.ipfamily)
        conf_str = constr_leaf_novalue(conf_str, "topologyName")
        conf_str = constr_leaf_novalue(conf_str, "lspTrPolicyName")
        conf_str = constr_leaf_novalue(conf_str, "autoFrrlspTriggerMode")
        conf_str = constr_leaf_novalue(conf_str, "autoFrrlspIpPrefixName")

        # Tail process
        conf_str = constr_container_tail(conf_str, "ldpTopologyInstance")
        conf_str = constr_container_tail(conf_str, "ldpTopologyInstances")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL
        logging.debug("begin test by gewuyue ")
        logging.debug(conf_str)
        xml_str = get_nc_config(self.module, conf_str)
        logging.debug(xml_str)
        if "<data/>" in xml_str:
            return None

        ldpInstance_info = dict()
        ldpInstance_info["vrfname"] = self.vrfname

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        # Get the remote peer infomation, remotePeer is the multi record.
        ldpInstance_info["topoinstances"] = list()
        root = ElementTree.fromstring(xml_str)
        topoinstances = root.findall(
            "data/mpls/mplsLdp/ldpInstances/ldpInstance/ldpTopologyInstances/ldpTopologyInstance")
        if len(topoinstances) != 0:
            for topoinstance in topoinstances:
                topoinstance_dict = dict()
                for ele in topoinstance:
                    topoinstance_dict[ele.tag.lower()] = ele.text
                ldpInstance_info["topoinstances"].append(topoinstance_dict)
        return ldpInstance_info

    def get_proposed(self):
        """Get proposed information"""
        self.proposed["state"] = self.state
        self.proposed["vrfname"] = self.vrfname
        if self.ldptopologyid is not None:
            self.proposed["ldptopologyid"] = self.ldptopologyid
        if self.ipfamily is not None:
            self.proposed["ipfamily"] = self.ipfamily
        if self.lsptrpolicyname is not None:
            self.proposed["lsptrpolicyname"] = self.lsptrpolicyname
        if self.autofrrlsptriggermode is not None:
            self.proposed["autofrrlsptriggermode"] = self.autofrrlsptriggermode
        if self.autofrrlspipprefixname is not None:
            self.proposed["autofrrlspipprefixname"] = self.autofrrlspipprefixname

    def get_existing(self):
        """Get existing configuration"""
        instance_info = self.get_ldp_InstanceTopo_dict()
        if not instance_info:
            return
        self.existing = instance_info
        self.ldpInstanceTopo_info = instance_info

    def get_end_state(self):
        """Get end state information"""
        instance_info = self.get_ldp_InstanceTopo_dict()
        if not instance_info:
            return
        self.end_state = instance_info

    def common_process(self, operationType, operationDesc):
        """Common  MPLS LDP  process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")

        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "ldpTopologyInstance", operationType)
        xml_str = constr_leaf_value(xml_str, "ldpTopologyId", self.ldptopologyid)
        xml_str = constr_leaf_value(xml_str, "ipFamily", self.ipfamily)
        xml_str = constr_leaf_value(xml_str, "lspTrPolicyName", self.lsptrpolicyname)
        xml_str = constr_leaf_value(xml_str, "autoFrrlspTriggerMode", self.autofrrlsptriggermode)
        xml_str = constr_leaf_value(xml_str, "autoFrrlspIpPrefixName", self.autofrrlspipprefixname)
        # Tail process
        xml_str = constr_container_process_tail(xml_str, "ldpTopologyInstance")
        xml_str = constr_container_process_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True
        # cmd line add here, to do next version.

    def create_process(self):
        """Create MPLS LDP  process"""
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge MPLS LDP process"""
        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete MPLS LDP  process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")

        # Body process , just need build key parameters
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "ldpTopologyInstance", NE_COMMON_XML_OPERATION_DELETE)
        xml_str = constr_leaf_value(xml_str, "ldpTopologyId", self.ldptopologyid)
        xml_str = constr_leaf_value(xml_str, "ipFamily", self.ipfamily)

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "ldpTopologyInstance")
        xml_str = constr_container_process_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

    def work(self):
        """ Main process
        """
        self.check_params()
        #
        self.get_proposed()
        #
        self.get_existing()

        # Deal present or absent or query
        if self.state == "present":
            if not self.ldpInstanceTopo_info:
                self.create_process()
            else:
                self.merge_process()
        elif self.state == "absent":
            if self.ldpInstanceTopo_info:
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: MPLS LDP interface does not exist')
        elif self.state == "query":
            if not self.ldpInstanceTopo_info:
                self.module.fail_json(msg='Error: MPLS LDP interface does not exist')

        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state

        self.module.exit_json(**self.results)


def main():
    """mian flow"""
    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        ldptopologyid=dict(required=True, type='int'),
        ipfamily=dict(required=True, type='int'),
        lsptrpolicyname=dict(required=False, type='str'),
        autofrrlsptriggermode=dict(required=False, choices=['all', 'host', 'none', 'ip-prefix']),
        autofrrlspipprefixname=dict(required=False, type='str'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpInstanceTopo(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
