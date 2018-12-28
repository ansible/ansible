# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys
import socket
import copy
import re
#
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
#
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_TAIL
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_TAIL
#
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_value
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_novalue
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_tail
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_tail
#
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


class MPLS_ldpBfd(object):
    """Manages configuration of an MPLS_ldpBfd instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.ldpbfdenable = self.module.params['ldpbfdenable']
        self.ldpbfdmintx = self.module.params['ldpbfdmintx']
        self.ldpbfdminrx = self.module.params['ldpbfdminrx']
        self.ldpbfddetectmultiplier = self.module.params['ldpbfddetectmultiplier']
        self.ldpbfdtrigger = self.module.params['ldpbfdtrigger']
        self.feclistname = self.module.params['feclistname']
        self.nexthopaddress = self.module.params['nexthopaddress']
        self.outifname = self.module.params['outifname']
        self.ldpbfdtriggertunnel = self.module.params['ldpbfdtriggertunnel']
        self.tunnelipprefixname = self.module.params['tunnelipprefixname']
        self.tnlfeclistname = self.module.params['tnlfeclistname']

        self.state = self.module.params['state']
        #  info
        self.ldpBfd_info = dict()

        # state
        self.changed = False
        # self.updates_cmd = list()
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

        # if self.ldpBfdMinTx:
        #    if self.ldpBfdMinTx < 3 or self.ldpBfdMinTx > 1000:
        #        self.module.fail_json(
        #            msg = 'Error: ldpBfdMinTx is not in the range of 3 to 1000.')
        #
        # if self.ldpBfdMinRx:
        #    if self.ldpBfdMinRx < 3 or self.ldpBfdMinRx > 1000:
        #        self.module.fail_json(
        #            msg = 'Error: ldpBfdMinRx is not in the range of 3 to 1000.')
        #
        # if self.ldpBfdDetectMultiplier:
        #    if self.ldpBfdDetectMultiplier < 3 or self.ldpBfdDetectMultiplier > 50:
        #        self.module.fail_json(
        #            msg = 'Error: ldpBfdDetectMultiplier is not in the range of 3 to 50.')
        #
        # if self.fecListName:
        #    if len(self.fecListName) > 31 or len(self.fecListName) < 1:
        #        self.module.fail_json(
        #            msg = 'Error: fecListName is not int the range form 1 to 31.')
        #
        # if self.nextHopAddress:
        #    if len(self.nextHopAddress) > 255 or len(self.nextHopAddress) < 0:
        #        self.module.fail_json(
        #            msg = 'Error:The length of nextHopAddress is not int the range form 0 to 255.')
        #
        # if self.outIfName:
        #    if len(self.outIfName) > 63 or len(self.outIfName) < 1:
        #        self.module.fail_json(
        #            msg = 'Error:The length of outIfName is not int the range form 1 to 63.')
        #
        # if self.tunnelIpPreFixName:
        #    if len(self.tunnelIpPreFixName) > 169 or len(self.tunnelIpPreFixName) < 1:
        #        self.module.fail_json(
        #            msg = 'Error: tunnelIpPreFixName is not int the range form 1 to 169.')
        #
        # if self.tnlFecListName:
        #    if len(self.tnlFecListName) > 31 or len(self.tnlFecListName) < 1:
        #        self.module.fail_json(
        #            msg = 'Error:The length of tnlFecListName is not in the range form 1 to 31')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ldpBfd_dict(self):
        """get one dict."""

        ldpBfd_info = dict()

        # Head info
        conf_str = NE_COMMON_XML_GET_MPLS_HEAD

        # Body info
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpBfd")

        conf_str = constr_leaf_novalue(conf_str, "ldpBfdEnable")
        conf_str = constr_leaf_novalue(conf_str, "ldpBfdMinTx")
        conf_str = constr_leaf_novalue(conf_str, "ldpBfdMinRx")
        conf_str = constr_leaf_novalue(conf_str, "ldpBfdDetectMultiplier")
        conf_str = constr_leaf_novalue(conf_str, "ldpBfdTrigger")
        conf_str = constr_leaf_novalue(conf_str, "fecListName")
        conf_str = constr_leaf_novalue(conf_str, "nextHopAddress")
        conf_str = constr_leaf_novalue(conf_str, "outIfName")
        conf_str = constr_leaf_novalue(conf_str, "ldpBfdTriggerTunnel")
        conf_str = constr_leaf_novalue(conf_str, "tunnelIpPreFixName")
        conf_str = constr_leaf_novalue(conf_str, "tnlFecListName")

        conf_str = constr_container_tail(conf_str, "ldpBfd")
        conf_str = constr_container_tail(conf_str, "mplsLdp")

        # Tail info
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL
        xml_str = get_nc_config(self.module, conf_str)

        # 如果<rpc-reply>的<data>标签是空的,也就是说是"<data/>"的形式,则返回空的dict()
        if "<data/>" in xml_str:
            return ldpBfd_info

        # 如果<rpc-reply>的<data>标签非空,把查到的数据写到dict()中
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        # get process base info
        root = ElementTree.fromstring(xml_str)
        ldpBfd = root.find("mpls/mplsLdp/ldpBfd")
        if ldpBfd is not None:
            for info in ldpBfd:
                if info.tag in ["ldpBfdEnable",
                                "ldpBfdMinTx",
                                "ldpBfdMinRx",
                                "ldpBfdDetectMultiplier",
                                "ldpBfdTrigger",
                                "fecListName",
                                "nextHopAddress",
                                "outIfName",
                                "ldpBfdTriggerTunnel",
                                "tunnelIpPreFixName",
                                "tnlFecListName"]:
                    ldpBfd_info[info.tag.lower()] = info.text
        return ldpBfd_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["state"] = self.state

        if self.ldpbfdenable:
            self.proposed["ldpbfdenable"] = self.ldpbfdenable
        if self.ldpbfdmintx:
            self.proposed["ldpbfdmintx"] = self.ldpbfdmintx
        if self.ldpbfdminrx:
            self.proposed["ldpbfdminrx"] = self.ldpbfdminrx
        if self.ldpbfddetectmultiplier:
            self.proposed["ldpbfddetectmultiplier"] = self.ldpbfddetectmultiplier
        if self.ldpbfdtrigger:
            self.proposed["ldpbfdtrigger"] = self.ldpbfdtrigger
        if self.feclistname:
            self.proposed["feclistname"] = self.feclistname
        if self.nexthopaddress:
            self.proposed["nexthopaddress"] = self.nexthopaddress
        if self.outifname:
            self.proposed["outifname"] = self.outifname
        if self.ldpbfdtriggertunnel:
            self.proposed["ldpbfdtriggertunnel"] = self.ldpbfdtriggertunnel
        if self.tunnelipprefixname:
            self.proposed["tunnelipprefixname"] = self.tunnelipprefixname
        if self.tnlfeclistname:
            self.proposed["tnlfeclistname"] = self.tnlfeclistname

    def get_existing(self):
        """get existing info"""
        if not self.ldpBfd_info:
            return
        self.existing = copy.deepcopy(self.ldpBfd_info)

    def get_end_state(self):
        """get end state info"""

        ldpBfd_info = self.get_ldpBfd_dict()
        if not ldpBfd_info:
            return
        self.end_state = copy.deepcopy(ldpBfd_info)

    def common_process(self, operationType, operationDesc):
        """common process"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD

        # Body process
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpBfd xc:operation = \"merge\"")

        if self.ldpbfdenable:
            xml_str = constr_leaf_value(xml_str, "ldpBfdEnable", self.ldpbfdenable)
        if self.ldpbfdmintx:
            xml_str = constr_leaf_value(xml_str, "ldpBfdMinTx", self.ldpbfdmintx)
        if self.ldpbfdminrx:
            xml_str = constr_leaf_value(xml_str, "ldpBfdMinRx", self.ldpbfdminrx)
        if self.ldpbfddetectmultiplier:
            xml_str = constr_leaf_value(xml_str, "ldpBfdDetectMultiplier", self.ldpbfddetectmultiplier)
        if self.feclistname:
            xml_str = constr_leaf_value(xml_str, "fecListName", self.feclistname)
        if self.nexthopaddress:
            xml_str = constr_leaf_value(xml_str, "nextHopAddress", self.nexthopaddress)
        if self.outifname:
            xml_str = constr_leaf_value(xml_str, "outIfName", self.outifname)
        if self.ldpbfdtriggertunnel:
            xml_str = constr_leaf_value(xml_str, "ldpBfdTriggerTunnel", self.ldpbfdtriggertunnel)
        if self.tunnelipprefixname:
            xml_str = constr_leaf_value(xml_str, "tunnelIpPreFixName", self.tunnelipprefixname)
        if self.tnlfeclistname:
            xml_str = constr_leaf_value(xml_str, "tnlFecListName", self.tnlfeclistname)

        xml_str = constr_container_tail(xml_str, "ldpBfd")
        xml_str = constr_container_tail(xml_str, "mplsLdp")

        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL
        recv_xml = set_nc_config(self.module, xml_str)

        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # 补充命令行

    def create_process(self):
        """Create  process"""
        # not support

    def merge_process(self):
        """Merge  process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete  process"""
        # not support

    def work(self):
        """worker"""

        # 参数检查
        self.check_params()

        # 查info
        self.ldpBfd_info = self.get_ldpBfd_dict()
        # 取目的态
        self.get_proposed()
        # 查初态
        self.get_existing()

        # 根据state分发给不同的处理函数
        if self.state == "present":
            self.merge_process()

        elif self.state == "query":
            # 查询输出
            if not self.ldpBfd_info:
                self.module.fail_json(msg='Error: ldpBfd instance does not exist ')

        # 查终态
        self.get_end_state()

        # 生成结果
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        # if self.changed:
        #    self.results['updates'] = self.updates_cmd
        # else:
        #    self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """Module Main"""

    argument_spec = dict(
        ldpbfdenable=dict(required=False, choices=['true', 'false']),
        ldpbfdmintx=dict(required=False, type='int'),
        ldpbfdminrx=dict(required=False, type='int'),
        ldpbfddetectmultiplier=dict(required=False, type='int'),
        ldpbfdtrigger=dict(required=False, choices=['none', 'host', 'fec-list']),
        feclistname=dict(required=False, type='int'),
        nexthopaddress=dict(required=False, type='str'),
        outifname=dict(required=False, type='str'),
        ldpbfdtriggertunnel=dict(required=False, choices=['none', 'host', 'fec-list', 'ip-prefix']),
        tunnelipprefixname=dict(required=False, type='str'),
        tnlfeclistname=dict(required=False, type='str'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpBfd(argument_spec)
    # Just Do It!
    module.work()


if __name__ == '__main__':
    main()
