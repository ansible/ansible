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
module: ne_ldp_instance
version_added: "2.6"
short_description: Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
description:
    - Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
author: Haoliansheng (@netengine-Ansible)
options:

'''

EXAMPLES = '''
---

- name: NE device mpls ldp module test
  hosts: mydevice
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli
  connection: netconf
  gather_facts: no

  tasks:

  - name: "Query mpls ldp remote peer "
    ne_ldp_instance_remotepeer_stateinfo: vrfname=_public_  remotepeername=test_remote1 state=query provider="{{ cli }}"
    register: data
    ignore_errors: true
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "remotepeername": "test_remote1",
        "state": "present",
        "vrfname": "_public_"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:
    "existing": {
        "remotepeername": "test_remote1",
        "remotepeerstateinfo": {
            "autoconfigtype": {
                "autoconfigac": "default",
                "autoconfigl2": "default",
                "autoconfigrlfa": "default",
                "autoconfigsp": "default"
            },
            "peerstate": "Inactive"
        },
        "vrfname": "_public_"
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: false
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

# import logging
# logging.basicConfig(filename='example.log',level=#logging.DEBUG)

# import pydevd
# pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)


class MPLS_ldpInstance_RemotePeer_State(object):
    """Manages configuration of a LDP intance
       Xpath: /mpls/mplsLdp/ldpInstances/ldpInstance/ldpRemotePeers/ldpRemotePeer/remotePeerStateInfo
    """

    def __init__(self, argument_spec):
        """Constructor"""

        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.remotepeername = self.module.params['remotepeername']
        self.state = self.module.params['state']

        # state
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()

    def init_module(self):
        """init module"""
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def get_ldp_instance_dict(self):
        """Get LDP instance inforamtion
        """
        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        # Just only build key paramters.
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpRemotePeers")
        conf_str = constr_container_head(conf_str, "ldpRemotePeer")
        conf_str = constr_leaf_value(conf_str, "remotePeerName", self.remotepeername)
        conf_str = constr_container_head(conf_str, "remotePeerStateInfo")

        conf_str = constr_leaf_novalue(conf_str, "peerState")
        conf_str = constr_leaf_novalue(conf_str, "negotiatedHelloHoldTime")
        conf_str = constr_container_head(conf_str, "autoConfigType")
        conf_str = constr_leaf_novalue(conf_str, "autoConfigAc")
        conf_str = constr_leaf_novalue(conf_str, "autoConfigL2")
        conf_str = constr_leaf_novalue(conf_str, "autoConfigRlfa")
        conf_str = constr_leaf_novalue(conf_str, "autoConfigSP")
        conf_str = constr_container_tail(conf_str, "autoConfigType")
        conf_str = constr_container_tail(conf_str, "remotePeerStateInfo")

        conf_str = constr_container_tail(conf_str, "ldpRemotePeer")
        conf_str = constr_container_tail(conf_str, "ldpRemotePeers")
        conf_str = constr_container_tail(conf_str, "ldpInstance")
        conf_str = constr_container_tail(conf_str, "ldpInstances")
        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return None
        ldpInstance_info = dict()

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        root = ElementTree.fromstring(xml_str)
        ldpInstance_info["vrfname"] = self.vrfname
        ldpInstance_info["remotepeername"] = self.remotepeername
        ldpInstance_info["remotepeerstateinfo"] = list()

        remoteStateInfo = root.findall(
            "data/mpls/mplsLdp/ldpInstances/ldpInstance/ldpRemotePeers/ldpRemotePeer/remotePeerStateInfo")
        if len(remoteStateInfo) != 0:
            remotePeer_dict = dict()
            for remoteState in remoteStateInfo:
                for ele in remoteState:
                    if ele.tag in ["peerState", "negotiatedHelloHoldTime"]:
                        remotePeer_dict[ele.tag.lower()] = ele.text
                    if ele.tag == "autoConfigType":
                        remotePeer_dict["autoconfigtype"] = dict()
                        autoConfig_dict = dict()
                        for autoCfg in ele:
                            autoConfig_dict[autoCfg.tag.lower()] = autoCfg.text
                        remotePeer_dict["autoconfigtype"] = autoConfig_dict

            ldpInstance_info["remotepeerstateinfo"] = remotePeer_dict
        return ldpInstance_info

    def get_proposed(self):
        """Get proposed information"""

        self.proposed["state"] = self.state
        self.proposed["vrfname"] = self.vrfname
        self.proposed["remotepeername"] = self.remotepeername

    def get_existing(self):
        """Get existing configuration"""
        instance_info = self.get_ldp_instance_dict()
        if not instance_info:
            return
        self.existing = instance_info

    def work(self):
        """ Main process    """

        self.get_proposed()
        self.get_existing()
        self.results['existing'] = self.existing
        self.module.exit_json(**self.results)


def main():
    """ Mian flow"""
    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        remotepeername=dict(required=True, type='str'),
        state=dict(required=False, default='query', choices=['query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpInstance_RemotePeer_State(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
