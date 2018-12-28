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


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_ldp_instance
version_added: "2.6"
short_description: Manages configuration of MPLS LDP instance parameters on HUAWEI netengine switches.
description:
    - Manages configuration of MPLS LDP instance parameters on HUAWEI netengine switches.
author: Haoliansheng (@netengine-Ansible)
notes:  Support create public and private vpn instance. Support delete private mpls ldp vpn instance.
        But does not support to delete public instance.

options:
    vrfname:
        description: - LDP VPN multi-instance name.
        required: true
        default: null
    lsrid:
        description: - LSR ID of an instance.
        required: false
        default: null
    igpsyncdelaytime:
        description: - Specifies the interval at which an interface waits to establish an LSP after an LDP session is set up.in seconds.
        required: false
        default: null
    gracefuldeleteenable:
        description: - The flag of enabling graceful delete.
        required: false
        default: null
        choices:['true', 'false']
    gracefuldeletetime:
        description: - Delay time for removing a upstream label after the LDP session between the NE and the upstream node goes Down.in seconds.
        required: false
        default: null
    nomappingenable:
        description: - Prohibits the sending of mappings to a remote neighbor. By default, mappings can be sent to all remote neighbors.
        required: false
        default: null
        choices:['true', 'false']
    autododrequestenable:
        description: - Auto Dod Request.
        required: false
        default: null
        choices:['true', 'false']
    authenmodeenable:
        description: - Global LDP authentication mode.
        required: false
        default: null
        choices:['authenmodeenable', 'mode_enable']
    md5password:
        description: - Global LDP MD5 Password. If you want to clear the MD5 password, you can configure the authentication mode to 'None Configuration'. \
        The password is a string ranging from 1 to 255 characters for a plaintext password and 20 to 432 characters for a ciphertext password.
        required: false
        default: null
    splithorizon:
        description: - Controls the sending of IPv4 label mapping messages to downstream LDP peers.
        required: false
        default: null
        choices:['true', 'false']
    ldpsendallloopback:
        description: - Advertises routes to all local loopback addresses to LDP peers.
        required: false
        default: null
        choices:['true', 'false']
    ldplongestmatch:
        description: - Longest Match.
        required: false
        default: null
        choices:['true', 'false']
    loopdetect:
        description: - Enables or disables loop detect on an LSR.
        required: false
        default: null
        choices:['true', 'false']
    ldplabelctrlmode:
        description: - Specifies label distribution control mode to be Independent or Ordered.
        required: false
        default: null
        choices:['Ordered', 'Independent']
    ldptrastamode:
        description: - LDP traffic statistic mode.
        required: false
        default: null
        choices:['none', 'host', 'host-ip-prefix']
    ldptrastaipprefname:
        description: - Specifies or clear the IP prefix triggering mode,LDP is triggered to establish or to clear LSPs by IP address prefixes,\
        The IP prefix is a string of 1 to 169 characters, spaces not supported.
        required: false
        default: null
    autormtkeepalivehold:
        description: - Specifies the value of the keepalive packet holding timer (s).in seconds for auto remote peer.
        required: false
        default: null
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

  - name: "Merge MPLS LDP public instance"
    ne_ldp_instance:
            vrfname=_public_
            lsrid=3.3.3.3
            igpsyncdelaytime=10
            gracefuldeleteenable=true
            gracefuldeletetime=20
            nomappingenable=true
            autododrequestenable=true
            authenmodeenable=mode_enable
            md5password=12345
            splithorizon=false
            ldpsendallloopback=true
            ldplongestmatch=true
            loopdetect=false
            ldplabelctrlmode=Ordered
            ldptrastamode=none
            autormtkeepalivehold=100
            state=present
          provider="{{ cli }}"
    register: data
    ignore_errors: false

  - name: "Merge mpls ldp VPN instance"
    ne_ldp_instance: vrfname=vpn1  state=present provider="{{ cli }}"
    register: data
    ignore_errors: true

  - name: "Delete mpls ldp VPN instance"
    ne_ldp_instance: vrfname=vpn1  state=absent provider="{{ cli }}"
    register: data
    ignore_errors: true

  - name: "Query MPLS LDP instance configurations"
    ne_ldp_instance: vrfname=_public_ state=query provider="{{ cli }}"
    register: data
    ignore_errors: false

  - name: "Delete mpls ldp public instance"
    ne_ldp_instance: vrfname=_public_ state=absent provider="{{ cli }}"
    register: data
    ignore_errors: true
'''

RETURN = '''
proposed:
  description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample:  {
        "authenmodeenable": "mode_enable",
        "autododrequestenable": "true",
        "autormtkeepalivehold": 100,
        "gracefuldeleteenable": "true",
        "gracefuldeletetime": 20,
        "igpsyncdelaytime": 10,
        "ldplabelctrlmode": "Ordered",
        "ldplongestmatch": "true",
        "ldpsendallloopback": "true",
        "ldptrastamode": "none",
        "loopdetect": "false",
        "lsrid": "3.3.3.3",
        "md5password": "12345",
        "nomappingenable": "true",
        "splithorizon": "false",
        "state": "present",
        "vrfname": "_public_"
    }

existing:
  description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: { "authenmodeenable": "mode_none",
        "gracefuldeleteenable": "false",
        "igpsyncdelaytime": "10",
        "ldplabelctrlmode": "Ordered",
        "loopdetect": "false",
        "splithorizon": "false",
        "vrfname": "vpn1" },
end_state:
  description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: {
        "authenmodeenable": "mode_none",
        "gracefuldeleteenable": "false",
        "igpsyncdelaytime": "10",
        "ldplabelctrlmode": "Ordered",
        "loopdetect": "false",
        "splithorizon": "false",
        "vrfname": "vpn1"
    },
changed:
  description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class MPLS_ldpInstance(object):
    """Manages configuration of a LDP intance
       Xpath: /mpls/mplsLdp/ldpInstances/ldpInstance
    """

    def __init__(self, argument_spec):
        """Constructor"""

        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.lsrid = self.module.params['lsrid']
        self.igpsyncdelaytime = self.module.params['igpsyncdelaytime']
        self.gracefuldeleteenable = self.module.params['gracefuldeleteenable']
        self.gracefuldeletetime = self.module.params['gracefuldeletetime']
        self.nomappingenable = self.module.params['nomappingenable']
        self.autododrequestenable = self.module.params['autododrequestenable']
        self.authenmodeenable = self.module.params['authenmodeenable']
        self.authentype = self.module.params['authentype']
        self.md5password = self.module.params['md5password']
        self.splithorizon = self.module.params['splithorizon']
        self.ldpsendallloopback = self.module.params['ldpsendallloopback']
        self.ldplongestmatch = self.module.params['ldplongestmatch']
        self.loopdetect = self.module.params['loopdetect']
        self.ldplabelctrlmode = self.module.params['ldplabelctrlmode']
        self.ldptrastamode = self.module.params['ldptrastamode']
        self.ldptrastaipprefname = self.module.params['ldptrastaipprefname']
        self.autormtkeepalivehold = self.module.params['autormtkeepalivehold']
        self.state = self.module.params['state']

        # LDP Instance info
        self.ldpInstance_info = dict()

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

    def get_ldp_instance_dict(self):
        """Get LDP instance inforamtion
        """
        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpInstances")
        conf_str = constr_container_head(conf_str, "ldpInstance")
        # Just only build key paramters.
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        # conf_str = constr_leaf_novalue(conf_str, "lsrid")
        # conf_str = constr_leaf_novalue(conf_str, "igpSyncDelayTime")
        # conf_str = constr_leaf_novalue(conf_str, "gracefulDeleteEnable")
        # conf_str = constr_leaf_novalue(conf_str, "gracefulDeleteTime")
        # conf_str = constr_leaf_novalue(conf_str, "noMappingEnable")
        # conf_str = constr_leaf_novalue(conf_str, "autoDodRequestEnable")
        # conf_str = constr_leaf_novalue(conf_str, "authenModeEnable")
        # conf_str = constr_leaf_novalue(conf_str, "md5Password")
        # conf_str = constr_leaf_novalue(conf_str, "splitHorizon")
        # conf_str = constr_leaf_novalue(conf_str, "ldpSendAllLoopBack")
        # conf_str = constr_leaf_novalue(conf_str, "ldpLongestMatch")
        # conf_str = constr_leaf_novalue(conf_str, "loopDetect")
        # conf_str = constr_leaf_novalue(conf_str, "ldpLabelCtrlMode")
        # conf_str = constr_leaf_novalue(conf_str, "ldpTraStaMode")
        # conf_str = constr_leaf_novalue(conf_str, "ldpTraStaIpPrefName")
        # conf_str = constr_leaf_novalue(conf_str, "autoRmtKeepaliveHold")
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
        # self.module.fail_json(
        # msg =xml_str)
        root = ElementTree.fromstring(xml_str)
        ldpInstance = root.find("mpls/mplsLdp/ldpInstances/ldpInstance")
        if len(ldpInstance) != 0:
            for para in ldpInstance:
                if para.tag in [
                    "vrfName",
                    "lsrid",
                    "authenModeEnable",
                    "authenType",
                    "autoDodRequestEnable",
                    "autoRmtKeepaliveHold",
                    "gracefulDeleteEnable",
                    "gracefulDeleteTime",
                    "igpSyncDelayTime",
                    "ldpLabelCtrlMode",
                    "ldpLongestMatch",
                    "ldpTraStaIpPrefName",
                    "ldpTraStaMode",
                    "loopDetect",
                    "md5Password",
                    "noMappingEnable",
                        "splitHorizon"]:
                    ldpInstance_info[para.tag.lower()] = para.text
        return ldpInstance_info

    def get_proposed(self):
        """Get proposed information"""

        self.proposed["state"] = self.state
        self.proposed["vrfname"] = self.vrfname

        # Just only display the input paramters
        if self.lsrid is not None:
            self.proposed["lsrid"] = self.lsrid
        if self.igpsyncdelaytime is not None:
            self.proposed["igpsyncdelaytime"] = self.igpsyncdelaytime
        if self.gracefuldeleteenable is not None:
            self.proposed["gracefuldeleteenable"] = self.gracefuldeleteenable
        if self.gracefuldeletetime is not None:
            self.proposed["gracefuldeletetime"] = self.gracefuldeletetime
        if self.nomappingenable is not None:
            self.proposed["nomappingenable"] = self.nomappingenable
        if self.autododrequestenable is not None:
            self.proposed["autododrequestenable"] = self.autododrequestenable
        if self.authenmodeenable is not None:
            self.proposed["authenmodeenable"] = self.authenmodeenable
        if self.authentype is not None:
            self.proposed["authentype"] = self.authentype
        if self.md5password is not None:
            self.proposed["md5password"] = self.md5password
        if self.splithorizon is not None:
            self.proposed["splithorizon"] = self.splithorizon
        if self.ldpsendallloopback is not None:
            self.proposed["ldpsendallloopback"] = self.ldpsendallloopback
        if self.ldplongestmatch is not None:
            self.proposed["ldplongestmatch"] = self.ldplongestmatch
        if self.loopdetect is not None:
            self.proposed["loopdetect"] = self.loopdetect
        if self.ldplabelctrlmode is not None:
            self.proposed["ldplabelctrlmode"] = self.ldplabelctrlmode
        if self.ldptrastamode is not None:
            self.proposed["ldptrastamode"] = self.ldptrastamode
        if self.ldptrastaipprefname is not None:
            self.proposed["ldptrastaipprefname"] = self.ldptrastaipprefname
        if self.autormtkeepalivehold is not None:
            self.proposed["autormtkeepalivehold"] = self.autormtkeepalivehold

    def get_existing(self):
        """Get existing configuration"""
        instance_info = self.get_ldp_instance_dict()
        if not instance_info:
            return
        self.existing = instance_info
        self.ldpInstance_info = instance_info

    def get_end_state(self):
        """Get end state information"""
        instance_info = self.get_ldp_instance_dict()
        if not instance_info:
            return
        self.end_state = instance_info

    def common_process(self, operationType, operationDesc):
        """Common  MPLS LDP  process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD
        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str = constr_container_process_head(xml_str, "ldpInstance", operationType)
        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_leaf_value(xml_str, "lsrid", self.lsrid)
        xml_str = constr_leaf_value(xml_str, "authenModeEnable", self.authenmodeenable)
        # xml_str = constr_leaf_value(xml_str, "authenType", self.authentype)
        xml_str = constr_leaf_value(xml_str, "autoDodRequestEnable", self.autododrequestenable)
        xml_str = constr_leaf_value(xml_str, "autoRmtKeepaliveHold", self.autormtkeepalivehold)
        xml_str = constr_leaf_value(xml_str, "gracefulDeleteEnable", self.gracefuldeleteenable)
        xml_str = constr_leaf_value(xml_str, "gracefulDeleteTime", self.gracefuldeletetime)
        xml_str = constr_leaf_value(xml_str, "igpSyncDelayTime", self.igpsyncdelaytime)
        xml_str = constr_leaf_value(xml_str, "ldpLabelCtrlMode", self.ldplabelctrlmode)
        xml_str = constr_leaf_value(xml_str, "ldpLongestMatch", self.ldplongestmatch)
        xml_str = constr_leaf_value(xml_str, "ldpTraStaIpPrefName", self.ldptrastaipprefname)
        xml_str = constr_leaf_value(xml_str, "ldpTraStaMode", self.ldptrastamode)
        xml_str = constr_leaf_value(xml_str, "loopDetect", self.loopdetect)
        xml_str = constr_leaf_value(xml_str, "md5Password", self.md5password)
        xml_str = constr_leaf_value(xml_str, "noMappingEnable", self.nomappingenable)
        xml_str = constr_leaf_value(xml_str, "splitHorizon", self.splithorizon)

        # Tail process
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
        xml_str = constr_container_process_head(xml_str, "ldpInstance", NE_COMMON_XML_OPERATION_DELETE)

        # Body process , just need build key parameters
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)

        # Tail process
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
            if self.existing is None:
                # create isis process
                self.create_process()
            else:
                # merge isis process
                self.merge_process()
        elif self.state == "absent":
            if self.existing is not None:
                # remove isis process
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: MPLS LDP instance does not exist')
        elif self.state == "query":
            # 查询输出
            if not self.existing:
                self.module.fail_json(msg='Error: MPLS LDP instance does not exist')

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
    """mian flow"""
    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        lsrid=dict(required=False, type='str'),
        igpsyncdelaytime=dict(required=False, type='int'),
        gracefuldeleteenable=dict(required=False, choices=['true', 'false']),
        gracefuldeletetime=dict(required=False, type='int'),
        nomappingenable=dict(required=False, choices=['true', 'false']),
        autododrequestenable=dict(required=False, choices=['true', 'false']),
        authenmodeenable=dict(required=False, choices=['mode_none', 'mode_enable']),
        authentype=dict(required=False, type='str'),
        md5password=dict(required=False, type='str'),
        splithorizon=dict(required=False, choices=['true', 'false']),
        ldpsendallloopback=dict(required=False, choices=['true', 'false']),
        ldplongestmatch=dict(required=False, choices=['true', 'false']),
        loopdetect=dict(required=False, choices=['true', 'false']),
        ldplabelctrlmode=dict(required=False, choices=['Ordered', 'Independent']),
        ldptrastamode=dict(required=False, choices=['none', 'host', 'host-ip-prefix']),
        ldptrastaipprefname=dict(required=False, type='str'),
        autormtkeepalivehold=dict(required=False, type='int'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpInstance(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
