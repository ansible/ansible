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


class MPLS_ldpBfdSession(object):
    """Manages configuration of an MPLS_ldpBfdSession instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.fecaddress = self.module.params['fecaddress']
        self.outifname = self.module.params['outifname']
        self.nexthop = self.module.params['nexthop']

        self.state = self.module.params['state']
        #  info
        self.ldpBfdSession_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init module"""

        # required bulabulabula~~~~~
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # if len(self.fecAddress) < 0 or len(self.fecAddress) > 255:
        # self.module.fail_json(
        # msg = 'Error: The length of fecAddress is not in the range from 0 to 255.')
        # if len(self.outIfName) < 0 or len(self.outIfName) > 63:
        # self.module.fail_json(
        # msg = 'Error: The length of outIfName is not in the range from 0 to 63.')
        # if len(self.nextHop) < 0 or len(self.nextHop) > 255:
        # self.module.fail_json(
        # msg = 'Error: The length of nextHop is not in the range from 0 to 255.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ldpBfdSession_dict(self):
        """get one dict."""

        ldpBfdSession_info = dict()

        # Head info
        conf_str = NE_COMMON_XML_GET_MPLS_HEAD

        # Body info
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpBfdSessions")
        conf_str = constr_container_head(conf_str, "ldpBfdSession")

        if self.fecaddress:
            conf_str = constr_leaf_value(conf_str, "fecAddress", self.fecaddress)
        else:
            conf_str = constr_leaf_novalue(conf_str, "fecAddress")

        if self.outifname:
            conf_str = constr_leaf_value(conf_str, "outIfName", self.outifname)
        else:
            conf_str = constr_leaf_novalue(conf_str, "outIfName")

        if self.nexthop:
            conf_str = constr_leaf_value(conf_str, "nextHop", self.nexthop)
        else:
            conf_str = constr_leaf_novalue(conf_str, "nextHop")

        conf_str = constr_leaf_novalue(conf_str, "lspIndex")
        conf_str = constr_leaf_novalue(conf_str, "bfdDiscriminator")
        conf_str = constr_leaf_novalue(conf_str, "sessionState")
        conf_str = constr_leaf_novalue(conf_str, "minTxInt")
        conf_str = constr_leaf_novalue(conf_str, "minRxInt")
        conf_str = constr_leaf_novalue(conf_str, "detectMulti")
        conf_str = constr_leaf_novalue(conf_str, "sessionAge")

        conf_str = constr_container_tail(conf_str, "ldpBfdSession")
        conf_str = constr_container_tail(conf_str, "ldpBfdSessions")
        conf_str = constr_container_tail(conf_str, "mplsLdp")

        # Tail info
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL
        xml_str = get_nc_config(self.module, conf_str)

        # 如果<rpc-reply>的<data>标签是空的,也就是说是"<data/>"的形式,则返回空的dict()
        if "<data/>" in xml_str:
            return ldpBfdSession_info

        # 如果<rpc-reply>的<data>标签非空,把查到的数据写到dict()中
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        # get process base info
        root = ElementTree.fromstring(xml_str)
        ldpBfdSessions = root.findall("data/mpls/mplsLdp/ldpBfdSessions/ldpBfdSession")
        if ldpBfdSessions is not None:
            ldpBfdSession_info['sessions'] = list()
            for ldpBfdSession in ldpBfdSessions:
                session_dict = dict()
                for ele in ldpBfdSession:
                    if ele.tag in ["fecAddress",
                                   "outIfName",
                                   "nextHop",
                                   "lspIndex",
                                   "bfdDiscriminator",
                                   "sessionState",
                                   "minTxInt",
                                   "minRxInt",
                                   "detectMulti",
                                   "sessionAge"]:
                        session_dict[ele.tag.lower()] = ele.text
                ldpBfdSession_info['sessions'].append(session_dict)
        return ldpBfdSession_info

    def get_proposed(self):
        """get proposed info"""
        # 只支持查询,不需要
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        if not self.ldpBfdSession_info:
            return
        self.existing = copy.deepcopy(self.ldpBfdSession_info)

    def get_end_state(self):
        """get end state info"""

        ldpBfdSession_info = self.get_ldpBfdSession_dict()
        if not ldpBfdSession_info:
            return
        self.end_state = copy.deepcopy(ldpBfdSession_info)

    def common_process(self, operationType, operationDesc):
        """common process"""
        # 只支持查询

    def create_process(self):
        """Create  process"""
        # not support

    def merge_process(self):
        """Merge  process"""
        # 只支持查询

    def delete_process(self):
        """Delete  process"""
        # not support

    def work(self):
        """worker"""

        # 参数检查
        self.check_params()

        # 查info
        self.ldpBfdSession_info = self.get_ldpBfdSession_dict()
        # 取目的态
        self.get_proposed()
        # 查初态
        self.get_existing()

        # 根据state分发给不同的处理函数
        if self.state != "query":
            # 查询输出
            self.module.fail_json(msg='Error: Operation not supported')

        # 查终态
        self.get_end_state()

        # 生成结果
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state

        self.module.exit_json(**self.results)


def main():
    """Module Main"""

    argument_spec = dict(
        fecaddress=dict(required=False, type='str'),
        outifname=dict(required=False, type='str'),
        nexthop=dict(required=False, type='str'),

        state=dict(required=False, default='query', choices=['query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpBfdSession(argument_spec)
    # Just Do It!
    module.work()


if __name__ == '__main__':
    main()
