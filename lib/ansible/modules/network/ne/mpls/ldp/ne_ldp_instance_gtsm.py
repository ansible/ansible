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
module: ne_ldp_instance_gtsm
version_added: "2.6"
short_description: Configures a list of GTSM security attributes
description:
    -
author: Haoliansheng (@CloudEngine-Ansible)
notes:
options:
    vrfname:
        description: - LDP VPN multi-instance name.
        required: true
        default: null
    peerTransportAddr:
        description: - Specifies a GTSM transport address.
        required: false
        default: null
    gtsmHops:
        description: - Specifies the maximum number of GTSM hops.
        required: false
        default: null
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


class MPLS_ldpGtsm(object):
    """  Configures a list of GTSM security attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        self.vrfname = self.module.params['vrfname']
        self.peertransportaddr = self.module.params['peertransportaddr']
        self.gtsmhops = self.module.params['gtsmhops']

        self.state = self.module.params['state']

        self.ldpGtsm_info = dict()

        self.changed = False
        # self.updates_cmd = list()
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
        """Check all input params"""

        # if self.gtsmHops:
        #    if self.gtsmHops < 1 or self.gtsmHops > 255:
        #        self.module.fail_json(
        #            msg = 'Error: gtsmHops is not in the range form 1 to 255')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ldpGtsm_dict(self):
        """get one dict."""

        ldpGtsm_info = dict()

        conf_str = NE_COMMON_XML_GET_MPLS_HEAD

        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpGtsms")
        conf_str = constr_container_head(conf_str, "ldpGtsm")

        if self.peertransportaddr:
            conf_str = constr_leaf_value(conf_str, "peerTransportAddr", self.peertransportaddr)
        else:
            conf_str = constr_leaf_novalue(conf_str, "peerTransportAddr")

        conf_str = constr_leaf_novalue(conf_str, "gtsmHops")

        conf_str = constr_container_tail(conf_str, "ldpGtsm")
        conf_str = constr_container_tail(conf_str, "ldpGtsms")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return ldpGtsm_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        ldpGtsm_info['vrfname'] = self.vrfname
        # get process base info
        root = ElementTree.fromstring(xml_str)
        ldpGtsms = root.findall("data/mpls/mplsLdp/ldpInstances/ldpInstance/ldpGtsms/ldpGtsm")
        if ldpGtsms is not None:
            ldpGtsm_info['gtsms'] = list()
            for gtsm in ldpGtsms:
                gtsm_dict = dict()
                for ele in gtsm:
                    if ele.tag in ["peerTransportAddr", "gtsmHops"]:
                        gtsm_dict[ele.tag.lower()] = ele.text
                ldpGtsm_info['gtsms'].append(gtsm_dict)
        return ldpGtsm_info

    def get_proposed(self):
        """get proposed info"""
        self.proposed["peertransportaddr"] = self.peertransportaddr
        self.proposed["vrfname"] = self.vrfname
        self.proposed["state"] = self.state
        if self.gtsmhops:
            self.proposed["gtsmhops"] = self.gtsmhops

    def get_existing(self):
        """get existing info"""
        if not self.ldpGtsm_info:
            return
        self.existing = copy.deepcopy(self.ldpGtsm_info)

    def get_end_state(self):
        """get end state info"""
        ldpGtsm_info = self.get_ldpGtsm_dict()
        if not ldpGtsm_info:
            return
        self.end_state = copy.deepcopy(ldpGtsm_info)

    def common_process(self, operationType, operationDesc):
        """common process"""

        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "ldpGtsm", operationType)

        xml_str = constr_leaf_value(xml_str, "peerTransportAddr", self.peertransportaddr)
        xml_str = constr_leaf_value(xml_str, "gtsmHops", self.gtsmhops)

        xml_str = constr_container_process_tail(xml_str, "ldpGtsm")
        xml_str = constr_container_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "ldpInstances")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # 命令行待补充

    def create_process(self):
        """Create  process"""
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge  process"""
        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete  process"""

        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "ldpGtsm", NE_COMMON_XML_OPERATION_DELETE)

        xml_str = constr_leaf_value(xml_str, "peerTransportAddr", self.peertransportaddr)

        xml_str = constr_container_process_tail(xml_str, "ldpGtsm")
        xml_str = constr_container_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "ldpInstances")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()

        self.ldpGtsm_info = self.get_ldpGtsm_dict()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if not self.ldpGtsm_info:
                self.create_process()
            else:
                self.merge_process()

        elif self.state == "absent":
            if self.ldpGtsm_info:
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: ldpGtsm instance does not exist.')

        elif self.state == "query":

            if not self.ldpGtsm_info:
                self.module.fail_json(msg='Error: ldpGtsm instance does not exist.')

        self.get_end_state()

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state

        self.module.exit_json(**self.results)


def main():
    """Module Main"""

    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        peertransportaddr=dict(required=True, type='str'),
        gtsmhops=dict(required=False, type='int'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))
    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpGtsm(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
