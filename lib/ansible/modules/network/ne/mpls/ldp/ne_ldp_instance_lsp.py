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


class MPLS_ldpLsp(object):
    """Manages configuration of an MPLS_ldpLsp instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.modules = None
        self.init_module()

        self.lspaddr = self.module.params['lspaddr']
        self.prefixlength = self.module.params['prefixlength']
        self.lspindex = self.module.params['lspindex']
        self.lsptype = self.module.params['lsptype']
        self.outifacename = self.module.params['outifacename']
        self.nexthop = self.module.params['nexthop']
        self.vrfname = self.module.params['vrfname']

        self.state = self.module.params['state']

        self.ldpLsp_info = dict()

        self.changed = False
        self.updates_cmd = list()
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
        # if self.prefixLength is not None:
        #    if self.prefixLength < 1 or self.prefixLength > 32:
        #        self.module.fail_json(
        #            msg = 'Error: prefixLength is not in the range from 1 to 32.')
        # if self.lspIndex is not None:
        #    if self.lspIndex < 5000001 or self.lspIndex > 7000000:
        #        self.module.fail_json(
        #            msg = 'Error: lspIndex is not in the range from 5000001 to 7000000.')
        # if self.outIfaceName is not None:
        #    if len(self.outIfaceName) < 1 or len(self.outIfaceName) > 63:
        #        self.module.fail_json(
        #            msg = 'Error: The length of outIfaceName is not in the range from 1 to 63.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ldpLsp_dict(self):
        """get one dict."""
        ldpLsp_info = dict()

        # <ldpLsp>
        #     <lspIndex>5024577</lspIndex>
        #     <lspAddr>1.1.1.1</lspAddr>
        #     <prefixLength>32</prefixLength>
        #     <lspType>Egress</lspType>
        #     <outIfaceName>LoopBack0</outIfaceName>
        #     <nextHop>127.0.0.1</nextHop>
        #     <isFrrLsp>false</isFrrLsp>
        #     <isRlfaLsp>false</isRlfaLsp>
        #     <lspTimeStamp>270352</lspTimeStamp>
        #     <inLabel>33027</inLabel>
        #   </ldpLsp>

        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpLsps")
        conf_str = constr_container_head(conf_str, "ldpLsp")

        if self.lspaddr:
            conf_str = constr_leaf_value(conf_str, "lspAddr", self.lspaddr)
        else:
            conf_str = constr_leaf_novalue(conf_str, "lspAddr")

        if self.prefixlength:
            conf_str = constr_leaf_value(conf_str, "prefixLength", self.prefixlength)
        else:
            conf_str = constr_leaf_novalue(conf_str, "prefixLength")

        if self.lspindex:
            conf_str = constr_leaf_value(conf_str, "lspIndex", self.lspindex)
        else:
            conf_str = constr_leaf_novalue(conf_str, "lspIndex")

        if self.lsptype:
            conf_str = constr_leaf_value(conf_str, "lspType", self.lsptype)
        else:
            conf_str = constr_leaf_novalue(conf_str, "lspType")

        if self.outifacename:
            conf_str = constr_leaf_value(conf_str, "outIfaceName", self.outifacename)
        else:
            conf_str = constr_leaf_novalue(conf_str, "outIfaceName")

        if self.nexthop:
            conf_str = constr_leaf_value(conf_str, "nextHop", self.nexthop)
        else:
            conf_str = constr_leaf_novalue(conf_str, "nextHop")

        conf_str = constr_leaf_novalue(conf_str, "isFrrLsp")
        conf_str = constr_leaf_novalue(conf_str, "isRlfaLsp")
        conf_str = constr_leaf_novalue(conf_str, "lspMtu")
        conf_str = constr_leaf_novalue(conf_str, "lspTimeStamp")
        conf_str = constr_leaf_novalue(conf_str, "inLabel")
        conf_str = constr_leaf_novalue(conf_str, "outLabel")

        conf_str = constr_container_tail(conf_str, "ldpLsp")
        conf_str = constr_container_tail(conf_str, "ldpLsps")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return ldpLsp_info
        ldpLsp_info['vrfname'] = self.vrfname

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        root = ElementTree.fromstring(xml_str)
        ldpLsps = root.findall("data/mpls/mplsLdp/ldpInstances/ldpInstance/ldpLsps/ldpLsp")

        if ldpLsps is not None:
            ldpLsp_info['ldpLsps'] = list()
            for lsp in ldpLsps:
                lsp_dict = dict()
                for ele in lsp:
                    if ele.tag in ["lspAddr",
                                   "prefixLength",
                                   "lspIndex",
                                   "lspType",
                                   "outIfaceName",
                                   "nextHop",
                                   "isFrrLsp",
                                   "isRlfaLsp",
                                   "lspMtu",
                                   "lspTimeStamp",
                                   "inLabel",
                                   "outLabel"]:
                        lsp_dict[ele.tag.lower()] = ele.text
                ldpLsp_info['ldpLsps'].append(lsp_dict)
        return ldpLsp_info

    def get_proposed(self):
        """get proposed info"""
        # query only

    def get_existing(self):
        """get existing info"""
        if self.ldpLsp_info:
            self.existing = copy.deepcopy(self.ldpLsp_info)

    def get_end_state(self):
        """get end state info"""
        if self.ldpLsp_info:
            self.end_state = copy.deepcopy(self.ldpLsp_info)

    def work(self):
        self.check_params()

        self.ldpLsp_info = self.get_ldpLsp_dict()
        self.get_proposed()
        self.get_existing()

        if not self.ldpLsp_info:
            self.module.fail_json(msg='Error: ldpLsp instance is not exist')

        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing

        self.module.exit_json(**self.results)


def main():
    """Module Main"""

    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        lspaddr=dict(required=False, type='str'),
        prefixlength=dict(required=False, type='int'),
        lspindex=dict(required=False, type='int'),
        lsptype=dict(required=False, choices=['Ingress', 'Transit', 'Egress', 'Ingress_Transit', 'Bud']),
        outifacename=dict(required=False, type='str'),
        nexthop=dict(required=False, type='str'),

        state=dict(required=False, default='query', choices=['query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpLsp(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
