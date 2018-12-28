# -*- coding: utf-8 -*-
# !/usr/bin/python

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
# logging.basicConfig(filename='example.log',level=logging.DEBUG)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_ldp_instance_authpeergroup
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


class MPLS_authPeerGroup(object):
    """Manages configuration of an  MPLS_authPeerGroup instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        self.vrfname = self.module.params['vrfname']
        self.preference = self.module.params['preference']
        self.authentype = self.module.params['authentype']
        self.authpeergroupname = self.module.params['authpeergroupname']
        self.authenmodeenable = self.module.params['authenmodeenable']
        self.md5password = self.module.params['md5password']

        self.state = self.module.params['state']

        self.authPeerGroup_info = dict()

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

        # if self.authPeerGroupName:
        #     if len(self.authPeerGroupName) < 1 or len(self.authPeerGroupName) > 169:
        #         self.module.fail_json(
        #             msg = 'Error: The length of authPeerGroupName is not in the range form 1 to 169.')
        #
        # if self.md5Password:
        #     if len(self.md5Password) < 1 or len(self.md5Password) > 432:
        #         self.module.fail_json(
        #             msg = 'Error: The length of md5Password is not in the range form 1 to 432.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_authPeerGroup_dict(self):
        """get one dict."""

        authPeerGroup_info = dict()

        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "authPeerGroups")
        conf_str = constr_container_head(conf_str, "authPeerGroup")

        if self.preference:
            conf_str = constr_leaf_value(conf_str, "preference", self.preference)
        else:
            conf_str = constr_leaf_novalue(conf_str, "preference")
        # Does not support filter by authPeerGroupName
        # if self.authpeergroupname:
        #    conf_str = constr_leaf_value(conf_str,      "authPeerGroupName", self.authpeergroupname)
        # else:
        conf_str = constr_leaf_novalue(conf_str, "authPeerGroupName")

        conf_str = constr_leaf_novalue(conf_str, "authenModeEnable")
        conf_str = constr_leaf_novalue(conf_str, "authenType")
        conf_str = constr_leaf_novalue(conf_str, "md5Password")
        conf_str = constr_leaf_novalue(conf_str, "keyChainName")

        conf_str = constr_container_tail(conf_str, "authPeerGroup")
        conf_str = constr_container_tail(conf_str, "authPeerGroups")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        logging.debug(xml_str)
        if "<data/>" in xml_str:
            return authPeerGroup_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")
        # self.module.fail_json(msg=xml_str)

        authPeerGroup_info["vrfname"] = self.vrfname
        root = ElementTree.fromstring(xml_str)
        authPeerGroups = root.findall("data/mpls/mplsLdp/ldpInstances/ldpInstance/authPeerGroups/authPeerGroup")
        if authPeerGroups is not None:
            authPeerGroup_info['groups'] = list()
            for group in authPeerGroups:
                peerGroup_dict = dict()
                for ele in group:
                    if ele.tag in ["preference",
                                   "authPeerGroupName",
                                   "authenModeEnable",
                                   "authenType",
                                   "md5Password",
                                   "keyChainName"]:
                        peerGroup_dict[ele.tag.lower()] = ele.text
                authPeerGroup_info['groups'].append(peerGroup_dict)
        return authPeerGroup_info

    def get_proposed(self):
        """get proposed info"""
        self.proposed["vrfname"] = self.vrfname
        if self.preference:
            self.proposed["preference"] = self.preference
        if self.authpeergroupname:
            self.proposed["authpeergroupname"] = self.authpeergroupname
        if self.authenmodeenable:
            self.proposed["authenmodeenable"] = self.authenmodeenable
        if self.md5password:
            self.proposed["md5password"] = self.md5password

        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if not self.authPeerGroup_info:
            return

        self.existing = copy.deepcopy(self.authPeerGroup_info)

    def get_end_state(self):
        """get end state info"""

        authPeerGroup_info = self.get_authPeerGroup_dict()
        if not authPeerGroup_info:
            return

        self.end_state = copy.deepcopy(self.authPeerGroup_info)

    def common_process(self, operation, operation_Desc):
        """common process"""

        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "authPeerGroup", operation)

        xml_str = constr_leaf_value(xml_str, "preference", self.preference)
        # xml_str = constr_leaf_value(xml_str, "authenType", self.authentype)
        xml_str = constr_leaf_value(xml_str, "authPeerGroupName", self.authpeergroupname)
        xml_str = constr_leaf_value(xml_str, "authenModeEnable", self.authenmodeenable)
        xml_str = constr_leaf_value(xml_str, "md5Password", self.md5password)

        xml_str = constr_container_process_tail(xml_str, "authPeerGroup")
        xml_str = constr_container_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "ldpInstances")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operation_Desc)
        self.changed = True

        # 命令行更新

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
        xml_str = constr_container_process_head(xml_str, "authPeerGroup", NE_COMMON_XML_OPERATION_DELETE)

        xml_str = constr_leaf_value(xml_str, "preference", self.preference)
        xml_str = constr_leaf_value(xml_str, "authPeerGroupName", self.authpeergroupname)

        xml_str = constr_container_process_tail(xml_str, "authPeerGroup")
        xml_str = constr_container_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "ldpInstances")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL
        # logging.debug(xml_str)
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        # 命令行更新
        self.changed = True

    def work(self):
        """worker"""

        self.check_params()

        self.authPeerGroup_info = self.get_authPeerGroup_dict()
        self.get_proposed()
        self.get_existing()
        if self.state == "present":
            if self.authPeerGroup_info:
                self.create_process()
            else:
                self.merge_process()
        elif self.state == "absent":
            if self.authPeerGroup_info:
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: Mpls instance is not exist.')
        elif self.state == "qurey":
            if not self.authPeerGroup_info:
                self.module.fail_json(msg='Error: Mpls instance is not exist.')

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
        preference=dict(required=False, type='int'),
        authentype=dict(required=False, type='str'),
        authpeergroupname=dict(required=False, type='str'),
        authenmodeenable=dict(required=False, choices=['mode_none', 'mode_enable']),
        md5password=dict(required=False, type='str'),

        state=dict(required=False, type='str', choices=['present', 'absent', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_authPeerGroup(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
