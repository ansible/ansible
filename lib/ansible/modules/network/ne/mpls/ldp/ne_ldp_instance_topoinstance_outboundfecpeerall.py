# -*- coding: utf-8 -*-
# !/usr/bin/python
#

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


class MPLS_ldpOutBoundFecPeerAll(object):
    """Manages configuration of an MPLS_ldpOutBoundFecPeerAll instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.ldptopologyid = self.module.params['ldptopologyid']
        self.ipfamily = self.module.params['ipfamily']
        self.fecpolicymode = self.module.params['fecpolicymode']
        self.fecipprefixname = self.module.params['fecipprefixname']

        self.state = self.module.params['state']

        self.ldpOutBoundFecPeerAll = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
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
        # 其他参数待同步增加补充

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ldpOutBoundFecPeerAll_dict(self):
        """ get one isis attributes dict."""

        ldpOutBoundFecPeerAll_info = dict()

        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpTopologyInstances")
        conf_str = constr_container_head(conf_str, "ldpTopologyInstance")
        conf_str = constr_leaf_value(conf_str, "ldpTopologyId", self.ldptopologyid)
        conf_str = constr_leaf_value(conf_str, "ipFamily", self.ipfamily)
        conf_str = constr_container_head(conf_str, "ldpOutBoundFecPeerAll")

        conf_str = constr_leaf_novalue(conf_str, "fecPolicyMode")
        conf_str = constr_leaf_novalue(conf_str, "fecIpPrefixName")

        conf_str = constr_container_tail(conf_str, "ldpOutBoundFecPeerAll")
        conf_str = constr_container_tail(conf_str, "ldpTopologyInstance")
        conf_str = constr_container_tail(conf_str, "ldpTopologyInstances")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return ldpOutBoundFecPeerAll_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        root = ElementTree.fromstring(xml_str)
        ldpOutBoundFecPeerAll = root.find("mpls/mplsLdp/ldpInstances/ldpInstance/ldpTopologyInstances/ldpTopologyInstance/ldpOutBoundFecPeerAll")

        ldpOutBoundFecPeerAll_info['vrfname'] = self.vrfname
        ldpOutBoundFecPeerAll_info['ldptopologyid'] = self.ldptopologyid
        ldpOutBoundFecPeerAll_info['ipfamily'] = self.ipfamily

        if len(ldpOutBoundFecPeerAll) != 0:
            for peer in ldpOutBoundFecPeerAll:
                if peer.tag in ["fecPolicyMode",
                                "fecIpPrefixName"]:
                    ldpOutBoundFecPeerAll_info[peer.tag] = peer.text

        return ldpOutBoundFecPeerAll_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        self.proposed["ldptopologyid"] = self.ldptopologyid
        self.proposed["ipfamily"] = self.ipfamily
        self.proposed["fecpolicymode"] = self.fecpolicymode
        if self.fecipprefixname:
            self.proposed["fecipprefixname"] = self.fecipprefixname

    def get_existing(self):
        """get existing info"""
        if self.ldpOutBoundFecPeerAll_info:
            # parent keys ?
            self.existing = copy.deepcopy(self.ldpOutBoundFecPeerAll_info)

    def get_end_state(self):
        """get end state info"""

        ldpOutBoundFecPeerAll_info = self.get_ldpOutBoundFecPeerAll_dict()
        if not ldpOutBoundFecPeerAll_info:
            return
        self.end_state = copy.deepcopy(ldpOutBoundFecPeerAll_info)

    def merge_process(self, operation_Desc):
        """Merge  process"""

        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_head(xml_str, "ldpTopologyInstances")
        xml_str = constr_container_head(xml_str, "ldpTopologyInstance")
        xml_str = constr_leaf_value(xml_str, "ldpTopologyId", self.ldptopologyid)
        xml_str = constr_leaf_value(xml_str, "ipFamily", self.ipfamily)
        xml_str = constr_container_head(xml_str, "ldpOutBoundFecPeerAll xc:operation=\"merge\"")

        xml_str = constr_leaf_value(xml_str, "fecPolicyMode", self.fecpolicymode)
        xml_str = constr_leaf_value(xml_str, "fecIpPrefixName", self.fecipprefixname)

        xml_str = constr_container_tail(xml_str, "ldpOutBoundFecPeerAll")
        xml_str = constr_container_tail(xml_str, "ldpTopologyInstance")
        xml_str = constr_container_tail(xml_str, "ldpTopologyInstances")
        xml_str = constr_container_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "ldpInstances")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operation_Desc)
        self.changed = True

        # 命令行补充更新

    def delete_process(self, operation_Desc):
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
        xml_str = constr_container_head(xml_str, "ldpOutBoundFecPeerAll xc:operation=\"delete\"")

        xml_str = constr_leaf_value(xml_str, "fecPolicyMode", self.fecpolicymode)

        xml_str = constr_container_tail(xml_str, "ldpOutBoundFecPeerAll")
        xml_str = constr_container_tail(xml_str, "ldpTopologyInstance")
        xml_str = constr_container_tail(xml_str, "ldpTopologyInstances")
        xml_str = constr_container_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "ldpInstances")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operation_Desc)
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()

        self.ldpOutBoundFecPeerAll_info = self.get_ldpOutBoundFecPeerAll_dict()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            self.merge_process("MERGE PROCESS")
        elif self.state == "absent":
            if self.ldpOutBoundFecPeerAll_info:
                self.delete_process("DELETE PROCESS")
            else:
                self.module.fail_json(msg='Error: ldpOutBoundFecPeerAll instance does not exist')
        elif self.state == "query":
            # 查询输出
            if not self.ldpOutBoundFecPeerAll_info:
                self.module.fail_json(msg='Error: ldpOutBoundFecPeerAll instance does not exist')

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
        fecpolicymode=dict(required=False, choices=['none', 'host', 'ip-prefix', 'default']),
        fecipprefixname=dict(required=False, type='str'),

        state=dict(required=False, choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpOutBoundFecPeerAll(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
