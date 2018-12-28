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
module: ne_ldp_instance_interface
version_added: "2.6"
short_description: Manages configuration of MPLS LDP interface on HUAWEI netengine switches.
description:
    - Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
author: Haoliansheng (@netengine-Ansible)
options:

'''

EXAMPLES = '''
'''

RETURN = '''
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
# logging.basicConfig(filename='example.log',level=logging.DEBUG)
# logging.debug('This message should go to the log file')
# import pydevd
# pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)


class MPLS_ldpInstanceInteface(object):
    """Manages configuration of a LDP intance remote peer information
       Xpath: /mpls/mplsLdp/ldpInstances/ldpInstance/ldpInterfaces/ldpInterface
    """

    def __init__(self, argument_spec):
        """Constructor"""

        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.ifname = self.module.params['ifname']
        self.helloholdtime = self.module.params['helloholdtime']
        self.hellosendtime = self.module.params['hellosendtime']
        self.igpsyncdelaytime = self.module.params['igpsyncdelaytime']
        self.keepaliveholdtime = self.module.params['keepaliveholdtime']
        self.keepalivesendtime = self.module.params['keepalivesendtime']
        self.labeladvmode = self.module.params['labeladvmode']
        self.mldpp2mpdisable = self.module.params['mldpp2mpdisable']
        self.transportaddrinterface = self.module.params['transportaddrinterface']
        self.locallsridaddrinterface = self.module.params['locallsridaddrinterface']
        self.state = self.module.params['state']

        # LDP Instance info
        self.ldpInstanceInterface_info = dict()

        # state

        self.changed = False
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
        """check all input params"""
        # Don't need check , error return by host.

    def check_response(self, xml_str, xml_name):
        """Check if operation is succeed."""
        if "<ok/>" not in xml_str:
            self.module.fail_json(
                msg='Error: %s failed.' % xml_name)

    def get_ldp_interface_dict(self):
        """Get LDP instance remote peer inforamtion
        """
        # Head process
        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        # Body process
        # Just only build key paramters.
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "ldpInterfaces")
        conf_str = constr_container_head(conf_str, "ldpInterface")
        conf_str = constr_leaf_value(conf_str, "ifName", self.ifname)

        conf_str = constr_leaf_novalue(conf_str, "helloSendTime")
        conf_str = constr_leaf_novalue(conf_str, "helloHoldTime")
        conf_str = constr_leaf_novalue(conf_str, "keepaliveSendTime")
        conf_str = constr_leaf_novalue(conf_str, "keepaliveHoldTime")
        conf_str = constr_leaf_novalue(conf_str, "igpSyncDelayTime")
        conf_str = constr_leaf_novalue(conf_str, "mLdpP2mpDisable")
        conf_str = constr_leaf_novalue(conf_str, "transportAddrInterface")
        conf_str = constr_leaf_novalue(conf_str, "localLsrIdAddrInterface")
        conf_str = constr_leaf_novalue(conf_str, "labelAdvMode")

        # Tail process
        conf_str = constr_container_tail(conf_str, "ldpInterface")
        conf_str = constr_container_tail(conf_str, "ldpInterfaces")
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
        ldpInstance = root.find("mpls/mplsLdp/ldpInstances/ldpInstance")
        if len(ldpInstance) != 0:
            for para in ldpInstance:
                if para.tag in ["vrfName"]:
                    ldpInstance_info[para.tag.lower()] = para.text

        # Get the remote peer infomation, remotePeer is the multi record.
        ldpInstance_info["interfaces"] = list()
        interfaces = root.findall(
            "data/mpls/mplsLdp/ldpInstances/ldpInstance/ldpInterfaces/ldpInterface")
        if len(interfaces) != 0:
            for interface in interfaces:
                interface_dict = dict()
                for ele in interface:
                    interface_dict[ele.tag.lower()] = ele.text
                ldpInstance_info["interfaces"].append(interface_dict)
        return ldpInstance_info

    def get_proposed(self):
        """Get proposed information"""

        self.proposed["state"] = self.state
        self.proposed["vrfname"] = self.vrfname
        self.proposed["ifname"] = self.ifname

        # Just only display the input paramters
        if self.helloholdtime is not None:
            self.proposed["helloholdtime"] = self.helloholdtime
        if self.hellosendtime is not None:
            self.proposed["hellosendtime"] = self.hellosendtime
        if self.igpsyncdelaytime is not None:
            self.proposed["igpsyncdelaytime"] = self.igpsyncdelaytime
        if self.keepaliveholdtime is not None:
            self.proposed["keepaliveholdtime"] = self.keepaliveholdtime
        if self.keepalivesendtime is not None:
            self.proposed["keepalivesendtime"] = self.keepalivesendtime
        if self.labeladvmode is not None:
            self.proposed["labeladvmode"] = self.labeladvmode
        if self.mldpp2mpdisable is not None:
            self.proposed["mldpp2mpdisable"] = self.mldpp2mpdisable
        if self.transportaddrinterface is not None:
            self.proposed["transportaddrinterface"] = self.transportaddrinterface
        if self.locallsridaddrinterface is not None:
            self.proposed["locallsridaddrinterface"] = self.locallsridaddrinterface

    def get_existing(self):
        """Get existing configuration"""
        instance_info = self.get_ldp_interface_dict()
        if not instance_info:
            return
        self.existing = instance_info
        self.ldpInstance_info = instance_info

    def get_end_state(self):
        """Get end state information"""
        instance_info = self.get_ldp_interface_dict()
        if not instance_info:
            return
        self.end_state = instance_info

    def common_process(self, operationType, operationDesc):
        """Common  MPLS LDP  process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")

        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "ldpInterface", operationType)
        xml_str = constr_leaf_value(xml_str, "ifName", self.ifname)
        xml_str = constr_leaf_value(xml_str, "helloSendTime", self.hellosendtime)
        xml_str = constr_leaf_value(xml_str, "helloHoldTime", self.helloholdtime)
        xml_str = constr_leaf_value(xml_str, "keepaliveSendTime", self.keepalivesendtime)
        xml_str = constr_leaf_value(xml_str, "keepaliveHoldTime", self.keepaliveholdtime)
        xml_str = constr_leaf_value(xml_str, "igpSyncDelayTime", self.igpsyncdelaytime)
        xml_str = constr_leaf_value(xml_str, "mLdpP2mpDisable", self.mldpp2mpdisable)
        xml_str = constr_leaf_value(xml_str, "transportAddrInterface", self.transportaddrinterface)
        xml_str = constr_leaf_value(xml_str, "localLsrIdAddrInterface", self.locallsridaddrinterface)
        xml_str = constr_leaf_value(xml_str, "labelAdvMode", self.labeladvmode)
        # Tail process
        xml_str = constr_container_process_tail(xml_str, "ldpInterface")
        xml_str = constr_container_process_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True
        # cmd line add here, to do next version.

    def create_process(self):
        """Create MPLS LDP  process"""
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge MPLS LDP process"""
        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete MPLS LDP  process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD

        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_head(xml_str, "ldpInstances")
        xml_str = constr_container_head(xml_str, "ldpInstance")

        # Body process , just need build key parameters
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "ldpInterface", NE_COMMON_XML_OPERATION_DELETE)
        xml_str = constr_leaf_value(xml_str, "ifName", self.ifname)

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "ldpInterface")
        xml_str = constr_container_process_tail(xml_str, "ldpInstance")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

    def work(self):
        """ Main process
        """
        self.check_params()
        #
        self.get_proposed()
        #
        self.get_existing()

        # Deal present or absent or query
        if self.state == "present":
            if not self.ldpInstance_info:
                # create isis process
                self.create_process()
            else:
                # merge isis process
                self.merge_process()
        elif self.state == "absent":
            if self.ldpInstance_info:
                # remove isis process
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: MPLS LDP interface does not exist')
        elif self.state == "query":
            # 查询输出
            if not self.ldpInstance_info:
                self.module.fail_json(msg='Error: MPLS LDP interface does not exist')

        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state

        self.module.exit_json(**self.results)


def main():
    """mian flow"""
    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        ifname=dict(required=True, type='str'),
        helloholdtime=dict(required=False, type='int'),
        hellosendtime=dict(required=False, type='int'),
        igpsyncdelaytime=dict(required=False, type='int'),
        keepaliveholdtime=dict(required=False, type='int'),
        keepalivesendtime=dict(required=False, type='int'),
        labeladvmode=dict(required=False, choices=['DU', 'DOD']),
        mldpp2mpdisable=dict(required=False, choices=['true', 'false']),
        transportaddrinterface=dict(required=False, type='str'),
        locallsridaddrinterface=dict(required=False, type='str'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpInstanceInteface(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
