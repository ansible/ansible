# -*- coding: utf-8 -*-
# !/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.# -*- coding: utf-8 -*-
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
        choices: ['present','absent']
    confedpeerasnum:
        description:
            - Confederation AS number, in two-byte or four-byte format.
              The value is a string of 1 to 11 characters.
        required: false
        default: null

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
    sample: ["confederation peer-as 20"]
'''

# Configure bgp ConfedPeerAs packet, use yang or schema modified head
# namespace.
NE_COMMON_XML_PROCESS_BGP_CONFED_PEERAS_HEAD = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <bgp xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp">
            <bgpcomm>
                <bgpConfedPeerAss>
                    <bgpConfedPeerAs xc:operation="%s">

"""

NE_COMMON_XML_PROCESS_BGP_CONFED_PEERAS_TAIL = """
                    </bgpConfedPeerAs>
                </bgpConfedPeerAss>
            </bgpcomm>
        </bgp>
    </config>
"""
NE_COMMON_XML_GET_BGP_CONFED_PEERAS_HEAD = """
    <filter type="subtree">
        <bgp xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp">
            <bgpcomm>
                <bgpConfedPeerAss>
                    <bgpConfedPeerAs>
"""

NE_COMMON_XML_GET_BGP_CONFED_PEERAS_TAIL = """
                    </bgpConfedPeerAs>
                </bgpConfedPeerAss>
            </bgpcomm>
        </bgp>
    </filter>
"""


class BgpConfed(object):
    """Manange confed peerAs"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # bgp confed peerAs info
        self.confedpeerasnum = self.module.params['confedpeerasnum']

        self.state = self.module.params['state']

        # bgp confed peerAs info
        self.confed_info = dict()

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

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_confed_dict(self):
        """ get one confed peerAs dict."""

        confed_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_BGP_CONFED_PEERAS_HEAD

        # Body info
        conf_str = constr_leaf_value(
            conf_str, "confedPeerAsNum", self.confedpeerasnum)

        # Tail info
        conf_str += NE_COMMON_XML_GET_BGP_CONFED_PEERAS_TAIL
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return confed_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # get process base info
        # re_find = re.findall(
        #    r'.*<instanceId>(.*)</instanceId>.*', xml_str)

        root = ElementTree.fromstring(xml_str)
        confedPeerAs = root.find(
            "bgp/bgpcomm/bgpConfedPeerAss/bgpConfedPeerAs")
        # if bgpVrf is not None:
        if len(confedPeerAs) != 0:
            for confed in confedPeerAs:
                if confed.tag in ["confedPeerAsNum"
                                  ]:
                    confed_info[confed.tag.lower()] = confed.text

        return confed_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["confedpeerasnum"] = self.confedpeerasnum
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        if not self.confed_info:
            return

        self.existing = copy.deepcopy(self.confed_info)

    def get_end_state(self):
        """get end state info"""

        confed_info = self.get_confed_dict()
        if not confed_info:
            return

        self.end_state = copy.deepcopy(confed_info)

    def common_process(self, operationType, operationDesc):
        """Common site process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_BGP_CONFED_PEERAS_HEAD % operationType
        # Body process
        xml_str = constr_leaf_value(
            xml_str, "confedPeerAsNum", self.confedpeerasnum)

        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_BGP_CONFED_PEERAS_TAIL
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        if self.confedpeerasnum:
            self.updates_cmd.append(
                "confederation peer-as %s " %
                self.confedpeerasnum)

    def create_process(self):
        """Create bgp process"""

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    # def merge_process(self):
        # """Merge bgp process"""

        # self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete bgp  process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_BGP_CONFED_PEERAS_HEAD % NE_COMMON_XML_OPERATION_DELETE
        # Body process
        xml_str = constr_leaf_value(
            xml_str, "confedPeerAsNum", self.confedpeerasnum)
        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_BGP_CONFED_PEERAS_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        self.updates_cmd.append(
            "undo confederation peer-as %s" %
            self.confedpeerasnum)
        self.changed = True

    def work(self):
        """worker"""
        # self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.confed_info = self.get_confed_dict()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.confed_info:
                # create bgp process
                self.create_process()
            # else:
                # merge bgp process
                # self.merge_process()
        elif self.state == "absent":
            # if self.confed_info:
                # remove bgp process
            self.delete_process()
            # else:
            # self.module.fail_json(
            # msg='Error: BGP confederation peer AS does not exist')
        elif self.state == "query":
            if not self.confed_info:
                self.module.fail_json(
                    msg='Error: BGP confederation peer AS does not exist')

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
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
        confedpeerasnum=dict(required=True, type='str'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = BgpConfed(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
