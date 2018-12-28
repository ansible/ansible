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

from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_delete
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_process_tail
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_process_head
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_tail
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_head
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_novalue
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_value
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import copy
import re
import socket
import sys
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_bgp
version_added: "2.6"
short_description: Manages BGP configuration on HUAWEI CloudEngine switches.
description:
    - Manages BGP configurations on HUAWEI CloudEngine switches.
author:
    - wangyuanqiang (@CloudEngine-Ansible)
    - Modified by gewuyue for support YANG
options:
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent','query']
    bgpbfddetectmultiplier:
        description:
            - BFD detect multiplier.
              The value is an integer ranging from 3 to 50. The default value is 3.
        required: false
        default: 3
    bgpbfdenable:
        description:
            - Enable BGP. By default, BGP is disabled.
        required: false
        default: false
        choices: ['true','false']
    bgpbfdminrx:
        description:
            - Enable GR of the BGP speaker in the specified address family, peer address, or peer group.
        required: false
        default: false
        choices: ['true','false']
    bgpbfdmintx:
        description:
            - Period of waiting for the End-Of-RIB flag.
              The value is an integer ranging from 3 to 3000. The default value is 600.
        required: false
        default: null
    bgpbfdtrigger:
        description:
            - The function to automatically select router IDs for all VPN BGP instances is enabled.
        required: false
        default: false
        choices: ['true','false']
    bgpbfdtriggeripprefix:
        description:
            - If the value is true, the system stores all route update messages received from all peers (groups) after
              BGP connection setup.
              If the value is false, the system stores only BGP update messages that are received from peers and pass
              the configured import policy.
        required: false
        default: false
        choices: ['true','false']
'''

EXAMPLES = '''

- name: CloudEngine BGP test
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli

  tasks:

  - name: "Enable BGP"
    ne_bgp:
      state: present
      as_number: 100
      confed_id_number: 250
      provider: "{{ cli }}"

  - name: "Disable BGP"
    ne_bgp:
      state: absent
      as_number: 100
      confed_id_number: 250
      provider: "{{ cli }}"

'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"as_number": "100", state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"bgp_enable": [["100"], ["true"]]}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"bgp_enable": [["100"], ["true"]]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["bgp 100"]
'''

# Configure bgp site packet, use yang or schema modified head namespace.
NE_COMMON_XML_PROCESS_BGP_BFD_PARA_HEAD = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <bgp xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp">
          <bgpcomm>
            <bgpLsp>
              <bgpLspBfd>
                <bgpLspBfdParameter xc:operation="%s">

"""

NE_COMMON_XML_PROCESS_BGP_BFD_PARA_TAIL = """
                </bgpLspBfdParameter>
              </bgpLspBfd>
            </bgpLsp>
          </bgpcomm>
        </bgp>
    </config>
"""
NE_COMMON_XML_GET_BGP_BFD_PARA_HEAD = """
    <filter type="subtree">
        <bgp xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp">
            <bgpcomm>
            <bgpLsp>
              <bgpLspBfd>
                <bgpLspBfdParameter>
"""

NE_COMMON_XML_GET_BGP_BFD_PARA_TAIL = """
               </bgpLspBfdParameter>
              </bgpLspBfd>
            </bgpLsp>
          </bgpcomm>
        </bgp>
    </filter>
"""


class BgpBfdPara(object):
    """Manange BGP BFD parameter"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # bgp site info
        self.bgpbfddetectmultiplier = self.module.params['bgpbfddetectmultiplier']
        self.bgpbfdenable = self.module.params['bgpbfdenable']
        self.bgpbfdminrx = self.module.params['bgpbfdminrx']
        self.bgpbfdmintx = self.module.params['bgpbfdmintx']
        self.bgpbfdtrigger = self.module.params['bgpbfdtrigger']
        self.bgpbfdtriggeripprefix = self.module.params['bgpbfdtriggeripprefix']

        self.state = self.module.params['state']

        # bgp bfd para info
        self.bfd_para_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init_module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        #
        # check bfd para
        # if self.bgpbfddetectmultiplier:
        #    if int(self.bgpbfddetectmultiplier) > 50 or int(self.bgpbfddetectmultiplier) < 3:
        #        module.fail_json(
        #            msg='bgpbfddetectmultiplier %s is out of [3 - 50].' % self.bgpbfddetectmultiplier)
        #
        # if self.bgpbfdminrx:
        #    if int(self.bgpbfdminrx) > 1000 or int(self.bgpbfdminrx) < 3:
        #        module.fail_json(
        #            msg='bgpbfdminrx %s is out of [3 - 1000].' % self.bgpbfdminrx)
        #
        # if self.bgpbfdmintx:
        #    if int(self.bgpbfdmintx) > 1000 or int(self.bgpbfdmintx) < 3:
        #        module.fail_json(
        # msg='bgpbfdmintx %s is out of [3 - 1000].' % self.bgpbfdmintx)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_bfd_para_dict(self):
        """ get one vrf attributes dict."""

        bfd_para_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_BGP_BFD_PARA_HEAD

        # Body info
        conf_str = constr_leaf_novalue(conf_str, "bgpBfdDetectMultiplier")
        conf_str = constr_leaf_novalue(conf_str, "bgpBfdEnable")
        conf_str = constr_leaf_novalue(conf_str, "bgpBfdMinRx")
        conf_str = constr_leaf_novalue(conf_str, "bgpBfdMinTx")
        conf_str = constr_leaf_novalue(conf_str, "bgpBfdTrigger")
        conf_str = constr_leaf_novalue(conf_str, "bgpBfdTriggerIpPrefix")

        # Tail info
        conf_str += NE_COMMON_XML_GET_BGP_BFD_PARA_TAIL
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return bfd_para_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # get process base info
        # re_find = re.findall(
        #    r'.*<instanceId>(.*)</instanceId>.*', xml_str)

        root = ElementTree.fromstring(xml_str)
        BgpBfdPara = root.find(
            "bgp/bgpcomm/bgpLsp/bgpLspBfd/bgpLspBfdParameter")
        # if BgpBfdPara is not None:
        if len(BgpBfdPara) != 0:
            for bfdPara in BgpBfdPara:
                if bfdPara.tag in ["bgpBfdDetectMultiplier",
                                   "bgpBfdEnable",
                                   "bgpBfdMinRx",
                                   "bgpBfdMinTx",
                                   "bgpBfdTrigger",
                                   "bgpBfdTriggerIpPrefix"
                                   ]:
                    bfd_para_info[bfdPara.tag.lower()] = bfdPara.text

        return bfd_para_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["state"] = self.state

        if self.bgpbfddetectmultiplier:
            self.proposed["bgpbfddetectmultiplier"] = self.bgpbfddetectmultiplier
        if self.bgpbfdenable:
            self.proposed["bgpbfdenable"] = self.bgpbfdenable
        if self.bgpbfdminrx:
            self.proposed["bgpbfdminrx"] = self.bgpbfdminrx
        if self.bgpbfdmintx:
            self.proposed["bgpbfdmintx"] = self.bgpbfdmintx
        if self.bgpbfdtrigger:
            self.proposed["bgpbfdtrigger"] = self.bgpbfdtrigger
        if self.bgpbfdtriggeripprefix:
            self.proposed["bgpbfdtriggeripprefix"] = self.bgpbfdtriggeripprefix

    def get_existing(self):
        """get existing info"""
        if not self.bfd_para_info:
            return

        self.existing = copy.deepcopy(self.bfd_para_info)

    def get_end_state(self):
        """get end state info"""

        bfd_para_info = self.get_bfd_para_dict()
        if not bfd_para_info:
            return

        self.end_state = copy.deepcopy(bfd_para_info)

    def common_process(self, operationType, operationDesc):
        """Common site process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_BGP_BFD_PARA_HEAD % operationType
        # Body process
        if self.bgpbfddetectmultiplier is not None:
            if len(self.bgpbfddetectmultiplier) == 0:
                xml_str = constr_leaf_delete(
                    xml_str, "bgpBfdDetectMultiplier", self.bgpbfddetectmultiplier)
            else:
                xml_str = constr_leaf_value(
                    xml_str, "bgpBfdDetectMultiplier", self.bgpbfddetectmultiplier)

        xml_str = constr_leaf_value(xml_str, "bgpBfdEnable", self.bgpbfdenable)

        if self.bgpbfdminrx is not None:
            if len(self.bgpbfdminrx) == 0:
                xml_str = constr_leaf_delete(
                    xml_str, "bgpBfdMinRx", self.bgpbfdminrx)
            else:
                xml_str = constr_leaf_value(
                    xml_str, "bgpBfdMinRx", self.bgpbfdminrx)

        if self.bgpbfdmintx is not None:
            if len(self.bgpbfdmintx) == 0:
                xml_str = constr_leaf_delete(
                    xml_str, "bgpBfdMinTx", self.bgpbfdmintx)
            else:
                xml_str = constr_leaf_value(
                    xml_str, "bgpBfdMinTx", self.bgpbfdmintx)

        xml_str = constr_leaf_value(
            xml_str, "bgpBfdTrigger", self.bgpbfdtrigger)
        xml_str = constr_leaf_value(
            xml_str,
            "bgpBfdTriggerIpPrefix",
            self.bgpbfdtriggeripprefix)

        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_BGP_BFD_PARA_TAIL
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # if self.bgpbfddetectmultiplier is not None:
        #    if len(self.bgpbfddetectmultiplier) != 0 :
        #        self.updates_cmd.append("mpls bgp bfd detect-multiplier %s" % self.bgpbfddetectmultiplier)
        #    else :
        #        self.updates_cmd.append("undo mpls bgp bfd detect-multiplier")
        #
        # if self.bgpbfdenable is not None:
        #    if self.bgpbfdenable == "true":
        #        self.updates_cmd.append("mpls bgp bfd enable")
        #    else:
        #        self.updates_cmd.append("undo mpls bgp bfd enable")
        #
        # if self.bgpbfdminrx is not None:
        #    if len(self.bgpbfdminrx) != 0 :
        #        self.updates_cmd.append("mpls bgp bfd min-rx-interval %s" % self.bgpbfdminrx)
        #    else :
        #        self.updates_cmd.append("undo mpls bgp bfd min-rx-interval")
        #
        # if self.bgpbfdmintx is not None:
        #    if len(self.bgpbfdmintx) != 0 :
        #        self.updates_cmd.append("mpls bgp bfd min-tx-interval %s" % self.bgpbfdmintx)
        #    else :
        #        self.updates_cmd.append("undo mpls bgp bfd min-tx-interval")
        #
        # if self.bgpbfdtrigger is not None:
        #    if self.bgpbfdtrigger == "host":
        #        self.updates_cmd.append("mpls bgp bfd-trigger-tunnel host")
        #    elif self.bgpbfdtrigger == "none":
        #        self.updates_cmd.append("undo mpls bgp bfd-trigger-tunnel")
        #    elif self.bgpbfdtrigger == "ip-prefix" and self.bgpbfdtriggeripprefix is not None and len(self.bgpbfdtriggeripprefix) !=0:
        #        self.updates_cmd.append("mpls bgp bfd-trigger-tunnel %s" % self.bgpbfdtriggeripprefix)

    # def create_process(self):
        # """Create bgp process"""

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        # self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge bgp process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    # def delete_process(self):
        # """Delete bgp  process"""
        # Head process
        # xml_str = NE_COMMON_XML_PROCESS_BGP_BFD_PARA_HEAD % NE_COMMON_XML_OPERATION_DELETE
        # Body process
        # xml_str = constr_leaf_value(xml_str, "bgpBfdEnable", self.bgpbfdenable)
        # Tail process
        # xml_str += NE_COMMON_XML_PROCESS_BGP_BFD_PARA_TAIL

        # recv_xml = set_nc_config(self.module, xml_str, True)
        # self.check_response(recv_xml, "DELETE_PROCESS")

        # self.updates_cmd.append("undo bgp %s" % self.asNumber)
        # self.changed = True

    def work(self):
        """worker"""
        self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.bfd_para_info = self.get_bfd_para_dict()
        self.get_proposed()
        self.get_existing()
        # deal present or absent
        if self.state == "present":
            # merge bgp process
            self.merge_process()
        # elif self.state == "absent":
            # if self.bfd_para_info:
            # remove bgp process
            # self.delete_process()
            # else:
            # self.module.fail_json(msg='Error: BGP site does not exist')
        elif self.state == "query":
            if not self.bfd_para_info:
                self.module.fail_json(
                    msg='Error: BGP BFD parameter does not exist')

        self.get_end_state()

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """main"""

    argument_spec = dict(
        bgpbfddetectmultiplier=dict(required=False, type='str'),
        bgpbfdenable=dict(required=False, choices=['true', 'false']),
        bgpbfdminrx=dict(required=False, type='str'),
        bgpbfdmintx=dict(required=False, type='str'),
        bgpbfdtrigger=dict(
            required=False, choices=[
                'none', 'host', 'ip-prefix']),
        bgpbfdtriggeripprefix=dict(required=False, type='str'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = BgpBfdPara(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
