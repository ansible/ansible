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


class MPLS_ldpAcceptTargetHello(object):
    """Manages configuration of an MPLS_ldpInBoundFecPeerAll instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.acceptmode = self.module.params['acceptmode']
        self.ipprefixname = self.module.params['ipprefixname']

        self.state = self.module.params['state']

        self.ldpAcceptTargetHello_info = dict()

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
        # 其他参数待同步增加补充
        # if self.ipPrefixName:
        #    if len(self.ipPrefixName) < 1 or len(self.ipPrefixName) > 169:
        #        self.module.fail_json(
        #            msg = 'Error: The length of ipPrefixName is not in the range from 1 to 169.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ldpAcceptTargetHello_dict(self):
        """ get one isis attributes dict."""

        ldpAcceptTargetHello_info = dict()

        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpAcceptTargetHello")

        conf_str = constr_leaf_novalue(conf_str, "acceptMode")
        conf_str = constr_leaf_novalue(conf_str, "ipPrefixName")

        conf_str = constr_container_tail(conf_str, "ldpAcceptTargetHello")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return ldpAcceptTargetHello_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        ldpAcceptTargetHello_info['vrfname'] = self.vrfname

        root = ElementTree.fromstring(xml_str)
        ldpAcceptTargetHello = root.find("mpls/mplsLdp/ldpInstances/ldpInstance/ldpAcceptTargetHello")

        if len(ldpAcceptTargetHello) != 0:
            for hello in ldpAcceptTargetHello:
                if hello.tag in ["acceptMode",
                                 "ipPrefixName"]:
                    ldpAcceptTargetHello_info[hello.tag.lower()] = hello.text

        return ldpAcceptTargetHello_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        if self.acceptmode:
            self.proposed["acceptmode"] = self.acceptmode
        if self.ipprefixname:
            self.proposed["ipprefixname"] = self.ipprefixname

    def get_existing(self):
        """get existing info"""
        if self.ldpAcceptTargetHello_info:
            # parent keys ?
            self.existing = copy.deepcopy(self.ldpAcceptTargetHello_info)

    def get_end_state(self):
        """get end state info"""

        ldpAcceptTargetHello_info = self.get_ldpAcceptTargetHello_dict()
        if not ldpAcceptTargetHello_info:
            return
        self.end_state = copy.deepcopy(ldpAcceptTargetHello_info)

    def common_process(self, opreationType, operation_Desc):
        """common  process"""

        conf_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpAcceptTargetHello  xc:operation=\"%s\"" % opreationType)

        conf_str = constr_leaf_value(conf_str, "acceptMode", self.acceptmode)
        conf_str = constr_leaf_value(conf_str, "ipPrefixName", self.ipprefixname)

        conf_str = constr_container_tail(conf_str, "ldpAcceptTargetHello")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, conf_str, True)
        self.check_response(recv_xml, operation_Desc)
        self.changed = True

        # 命令行补充更新

    def create_process(self):
        """Create isis process"""

        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge isis process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete isis  process"""

        conf_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpAcceptTargetHello  xc:operation=\"delete\"")

        conf_str = constr_leaf_value(conf_str, "acceptMode", self.acceptmode)
        conf_str = constr_leaf_value(conf_str, "ipPrefixName", self.ipprefixname)

        conf_str = constr_container_tail(conf_str, "ldpAcceptTargetHello")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, conf_str, True)
        self.check_response(recv_xml, "DELETE_OPERTION")
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()

        self.ldpAcceptTargetHello_info = self.get_ldpAcceptTargetHello_dict()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.ldpAcceptTargetHello_info:
                # create  process
                self.create_process()
            else:
                # merge  process
                self.merge_process()
        elif self.state == "absent":
            if self.ldpAcceptTargetHello_info:
                # remove  process
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: ldpAcceptTargetHello instance does not exist')
        elif self.state == "query":
            # 查询输出
            if not self.ldpAcceptTargetHello_info:
                self.module.fail_json(msg='Error: ldpAcceptTargetHello instance does not exist')

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
        acceptmode=dict(required=False, choices=['none', 'all', 'peer-group']),
        ipprefixname=dict(required=False, type='str'),

        state=dict(required=False, choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpAcceptTargetHello(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
