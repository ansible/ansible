# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys
import socket
import copy
import re

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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module:
version_added: "2.6"
short_description:
description:
    -
author: Haoliansheng (@CloudEngine-Ansible)
notes:
options:
'''

EXAMPLES = '''
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample:
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class MPLS_ldpOutBoundBgpPeer(object):
    """Manages configuration of an ISIS instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        self.vrfname = self.module.params['vrfname']
        self.ldptopologyid = self.module.params['ldptopologyid']
        self.ipfamily = self.module.params['ipfamily']
        self.peerid = self.module.params['peerid']
        self.bgppolicymode = self.module.params['bgppolicymode']
        self.bgpipprefixname = self.module.params['bgpipprefixname']

        self.state = self.module.params['state']

        self.ldpOutBoundBgpPeer_info = dict()

        # state
        self.changed = False
        # self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""

        # if self.bgpIpPrefixName:
        #    if len(self.bgpIpPrefixName) < 1 or len(self.bgpIpPrefixName) > 169:
        #        self.module.fail_json(
        #            msg = "Error: The length of bgpIpPrefixName is not in the range from 1 to 169.")

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ldpOutBoundBgpPeer_dict(self):
        """get one dict."""

        ldpOutBoundBgpPeer_info = dict()

        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpTopologyInstances")
        conf_str = constr_container_head(conf_str, "ldpTopologyInstance")
        conf_str = constr_leaf_value(conf_str, "ldpTopologyId", self.ldptopologyid)
        conf_str = constr_leaf_value(conf_str, "ipFamily", self.ipfamily)
        conf_str = constr_container_head(conf_str, "ldpOutBoundBgpPeers")
        conf_str = constr_container_head(conf_str, "ldpOutBoundBgpPeer")
        if self.peerid:
            conf_str = constr_leaf_value(conf_str, "peerid", self.peerid)
        else:
            conf_str = constr_leaf_novalue(conf_str, "peerid")

        conf_str = constr_leaf_novalue(conf_str, "bgpPolicyMode")
        conf_str = constr_leaf_novalue(conf_str, "bgpIpPrefixName")

        conf_str = constr_container_tail(conf_str, "ldpOutBoundBgpPeer")
        conf_str = constr_container_tail(conf_str, "ldpOutBoundBgpPeers")
        conf_str = constr_container_tail(conf_str, "ldpTopologyInstance")
        conf_str = constr_container_tail(conf_str, "ldpTopologyInstances")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return ldpOutBoundBgpPeer_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        ldpOutBoundBgpPeer_info['vrfname'] = self.vrfname
        ldpOutBoundBgpPeer_info['ldptopologyid'] = self.ldptopologyid
        ldpOutBoundBgpPeer_info['ipfamily'] = self.ipfamily

        root = ElementTree.fromstring(xml_str)
        ldpOutBoundBgpPeers = root.findall(
            "data/mpls/mplsLdp/ldpInstances/ldpInstance/ldpTopologyInstances/ldpTopologyInstance/ldpOutBoundBgpPeers/ldpOutBoundBgpPeer")
        if ldpOutBoundBgpPeers is not None:
            ldpOutBoundBgpPeer_info['bgpPeers'] = list()
            for peer in ldpOutBoundBgpPeers:
                peer_dict = dict()
                for ele in peer:
                    if ele.tag in ["peerid",
                                   "bgpPolicyMode",
                                   "bgpIpPrefixName"]:
                        peer_dict[ele.tag.lower()] = ele.text
                ldpOutBoundBgpPeer_info['bgpPeers'].append(peer_dict)
        return ldpOutBoundBgpPeer_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["peerid"] = self.peerid
        self.proposed["bgppolicymode"] = self.bgppolicymode
        if self.bgpipprefixname:
            self.proposed["bgpipprefixname"] = self.bgpipprefixname

    def get_existing(self):
        """get existing info"""
        if self.ldpOutBoundBgpPeer_info:
            # parent keys ?
            self.existing = copy.deepcopy(self.ldpOutBoundBgpPeer_info)

    def get_end_state(self):
        """get end state info"""

        ldpOutBoundBgpPeer_info = self.get_ldpOutBoundBgpPeer_dict()
        if not ldpOutBoundBgpPeer_info:
            return
        self.end_state = copy.deepcopy(ldpOutBoundBgpPeer_info)

    def common_process(self, operationType, operationDesc):
        """Common  isis process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_head(xml_str, "ldpTopologyInstances")
        xml_str = constr_container_head(xml_str, "ldpTopologyInstance")
        xml_str = constr_leaf_value(xml_str, "ldpTopologyId", self.ldptopologyid)
        xml_str = constr_leaf_value(xml_str, "ipFamily", self.ipfamily)
        xml_str = constr_container_process_head(xml_str, "ldpOutBoundBgpPeer", operationType)

        xml_str = constr_leaf_value(xml_str, "peerid", self.peerid)
        xml_str = constr_leaf_value(xml_str, "bgpPolicyMode", self.bgppolicymode)
        xml_str = constr_leaf_value(xml_str, "bgpIpPrefixName", self.bgpipprefixname)

        xml_str = constr_container_process_tail(xml_str, "ldpOutBoundBgpPeer")
        xml_str = constr_container_tail(xml_str, "ldpTopologyInstance")
        xml_str = constr_container_tail(xml_str, "ldpTopologyInstances")
        xml_str = constr_container_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "ldpInstances")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

    def create_process(self):
        """Create isis process"""

        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge isis process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete isis  process"""

        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_head(xml_str, "ldpTopologyInstances")
        xml_str = constr_container_head(xml_str, "ldpTopologyInstance")
        xml_str = constr_leaf_value(xml_str, "ldpTopologyId", self.ldptopologyid)
        xml_str = constr_leaf_value(xml_str, "ipFamily", self.ipfamily)
        xml_str = constr_container_process_head(xml_str, "ldpOutBoundBgpPeer", NE_COMMON_XML_OPERATION_DELETE)

        xml_str = constr_leaf_value(xml_str, "peerid", self.peerid)
        xml_str = constr_leaf_value(xml_str, "bgpPolicyMode", self.bgppolicymode)

        xml_str = constr_container_process_tail(xml_str, "ldpOutBoundBgpPeer")
        xml_str = constr_container_tail(xml_str, "ldpTopologyInstance")
        xml_str = constr_container_tail(xml_str, "ldpTopologyInstances")
        xml_str = constr_container_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "ldpInstances")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        self.changed = True

    def work(self):
        """worker"""
        self.check_params()

        self.ldpOutBoundBgpPeer_info = self.get_ldpOutBoundBgpPeer_dict()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.ldpOutBoundBgpPeer_info:
                # create  process
                self.create_process()
            else:
                # merge  process
                self.merge_process()
        elif self.state == "absent":
            if self.ldpOutBoundBgpPeer_info:
                # remove  process
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: ldpOutBoundBgpPeer instance does not exist')
        elif self.state == "query":
            # 查询输出
            if not self.ldpOutBoundBgpPeer_info:
                self.module.fail_json(msg='Error: ldpOutBoundBgpPeer instance does not exist')

        self.get_end_state()

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state

        self.module.exit_json(**self.results)


def main():
    """Module main"""

    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        ldptopologyid=dict(required=True, type='int'),
        ipfamily=dict(required=True, type='int'),
        peerid=dict(required=False, type='str'),
        bgppolicymode=dict(required=False, choices=['none', 'host', 'ip-prefix', 'default']),
        bgpipprefixname=dict(required=False, type='str'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpOutBoundBgpPeer(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
