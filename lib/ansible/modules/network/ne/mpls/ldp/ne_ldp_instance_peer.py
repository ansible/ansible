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

DOCUMENTATION = '''
---
module: ne_ldp_instance_peer
version_added: "2.6"
short_description: Manages configuration of MPLS LDP peer parameters on HUAWEI netengine switches.
description:
    - Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
author: Haoliansheng (@netengine-Ansible)
options:

'''

EXAMPLES = '''
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "peerid": "2.2.2.2",
        "state": "present",
        "vrfname": "_public_"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {
        "peers": [
            {
                "authenmodeenable": "mode_enable",
                "authentype": "md5",
                "md5password": "%^%#B]FgV!C#[:rcpeXB60q!*/lsT(#NnX@vY!D\"F0`$%^%#",
                "outbound": "true",
                "peerid": "2.2.2.2"
            }
        ],
        "vrfname": "_public_"
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: {
        "peers": [
            {
                "authenmodeenable": "mode_enable",
                "authentype": "md5",
                "md5password": "%^%#B]FgV!C#[:rcpeXB60q!*/lsT(#NnX@vY!D\"F0`$%^%#",
                "outbound": "true",
                "peerid": "2.2.2.2"
            }
        ],
        "vrfname": "_public_"
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class MPLS_ldpPeer(object):
    """Manages configuration of a LDP intance  peer information
       Xpath: /mpls/mplsLdp/ldpInstances/ldpInstance/ldpPeers/ldpPeer
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        self.vrfname = self.module.params['vrfname']
        self.peerid = self.module.params['peerid']
        self.authenmodeenable = self.module.params['authenmodeenable']
        self.md5password = self.module.params['md5password']
        self.outbound = self.module.params['outbound']

        self.state = self.module.params['state']

        self.ldpPeer_info = dict()

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
        # if self.md5password:
        #    if len(self.md5password) < 1 or len(self.md5password) > 432:
        #        self.module.fail_json(
        #            msg = 'Error: The length of md5Password is not in the range form 1 to 432.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_ldpPeer_dict(self):
        """get one dict."""

        ldpPeer_info = dict()

        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpPeers")
        conf_str = constr_container_head(conf_str, "ldpPeer")

        if self.peerid:
            conf_str = constr_leaf_value(conf_str, "peerid", self.peerid)
        else:
            conf_str = constr_leaf_novalue(conf_str, "peerid")
        conf_str = constr_leaf_novalue(conf_str, "authenModeEnable")
        conf_str = constr_leaf_novalue(conf_str, "authenType")
        conf_str = constr_leaf_novalue(conf_str, "md5Password")
        conf_str = constr_leaf_novalue(conf_str, "keyChainName")
        conf_str = constr_leaf_novalue(conf_str, "outBound")

        conf_str = constr_container_tail(conf_str, "ldpPeer")
        conf_str = constr_container_tail(conf_str, "ldpPeers")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str)

        if "<data/>" in xml_str:
            return ldpPeer_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")
        ldpPeer_info['vrfname'] = self.vrfname

        root = ElementTree.fromstring(xml_str)
        ldpPeers = root.findall("data/mpls/mplsLdp/ldpInstances/ldpInstance/ldpPeers/ldpPeer")
        if ldpPeers is not None:
            ldpPeer_info['peers'] = list()
            for peer in ldpPeers:
                peer_dict = dict()
                for ele in peer:
                    if ele.tag in ["peerid",
                                   "authenModeEnable",
                                   "md5Password",
                                   "keyChainName",
                                   "outBound"]:
                        peer_dict[ele.tag.lower()] = ele.text
                ldpPeer_info['peers'].append(peer_dict)
        return ldpPeer_info

    def get_proposed(self):
        """get proposed info"""
        self.proposed["state"] = self.state
        self.proposed["vrfname"] = self.vrfname

        if self.peerid is not None:
            self.proposed["peerid"] = self.peerid
        if self.authenmodeenable is not None:
            self.proposed["authenmodeenable"] = self.authenmodeenable
        if self.md5password is not None:
            self.proposed["md5password"] = self.md5password
        if self.outbound is not None:
            self.proposed["outbound"] = self.outbound

    def get_existing(self):
        """get existing info"""

        if not self.ldpPeer_info:
            return

        self.existing = copy.deepcopy(self.ldpPeer_info)

    def get_end_state(self):
        """get end state info"""

        ldpPeer_info = self.get_ldpPeer_dict()
        if not ldpPeer_info:
            return
        self.end_state = copy.deepcopy(ldpPeer_info)

    def common_porcess(self, operationType, operationDesc):
        """common process"""

        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD

        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "ldpPeer", operationType)

        xml_str = constr_leaf_value(xml_str, "peerid", self.peerid)
        xml_str = constr_leaf_value(xml_str, "authenModeEnable", self.authenmodeenable)
        xml_str = constr_leaf_value(xml_str, "md5Password", self.md5password)
        xml_str = constr_leaf_value(xml_str, "outBound", self.outbound)

        xml_str = constr_container_process_tail(xml_str, "ldpPeer")
        xml_str = constr_container_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "ldpInstances")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # cmd line add here~

    def create_process(self):
        """Create  process"""
        self.common_porcess(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge  process"""
        self.common_porcess(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete  process"""

        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD

        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "ldpPeer", NE_COMMON_XML_OPERATION_DELETE)

        xml_str = constr_leaf_value(xml_str, "peerid", self.peerid)

        xml_str = constr_container_process_tail(xml_str, "ldpPeer")
        xml_str = constr_container_process_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "DELETE_PROCESS")

        self.changed = True

    def work(self):
        """worker"""

        self.check_params()

        self.ldpPeer_info = self.get_ldpPeer_dict()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if not self.ldpPeer_info:
                self.create_process()
            else:
                self.merge_process()

        elif self.state == "absent":
            if self.ldpPeer_info:
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: ldpPeer instance does not exist.')

        elif self.state == "query":

            if not self.ldpPeer_info:
                self.module.fail_json(msg='Error: ldpPeer instance does not exist.')

        self.get_end_state()

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
        vrfname=dict(required=True, type='str'),
        peerid=dict(required=True, type='str'),
        authenmodeenable=dict(required=False, choices=['mode_none', 'mode_enable', 'mode_exclude']),
        md5password=dict(required=False, type='str'),
        outbound=dict(required=False, choices=['true', 'false']),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpPeer(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
