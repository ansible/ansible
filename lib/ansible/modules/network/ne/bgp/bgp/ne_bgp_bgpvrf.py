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

from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_delete
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_process_tail
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_process_head
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_tail
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_head
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_novalue
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_value
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_BGP_INSTANCE_TAIL
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_BGP_INSTANCE_HEADER
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_GET_BGP_VRF_TAIL
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_GET_BGP_VRF_HEAD
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
    vrfname:
        description:
            - Name of a BGP instance. The name is a case-sensitive string of characters.
        required: false
        default: null
    vrfsession:
        description:
            Create VPN session view.
        required: false
        default: false
        choices: ['true','false']
    defaultaftype:
        description:
            - Type of a created address family, which can be IPv4 unicast or IPv6 unicast.
              The default type is IPv4 unicast.
        required: false
        default: null
        choices: ['ipv4uni','ipv6uni']
    connretrytime:
        description:
            - ConnectRetry interval. The value is an integer, in seconds. The default value is 32s.
        required: false
        default: null
    holdtime:
        description:
            - Hold time, in seconds. The value of the hold time can be 0 or range from 3 to 65535.
        required: false
        default: null
    keepalivetime:
        description:
            - If the value of a timer changes, the BGP peer relationship between the routers is disconnected.
              The value is an integer ranging from 0 to 21845. The default value is 60.
        required: false
        default: null
    minholdtime:
        description:
            - Min hold time, in seconds. The value of the hold time can be 0 or range from 20 to 65535.
        required: false
        default: null
    vrfridautosel:
        description:
            - If the value is true, VPN BGP instances are enabled to automatically select router IDs.
              If the value is false, VPN BGP instances are disabled from automatically selecting router IDs.
        required: false
        default: false
        choices: ['true','false']
    ebgpifsensitive:
        description:
            - Immediately reset session if a link connected peer goes down
        required: false
        default: false
        choices: ['true','false']
    routerid:
        description:
            - ID of a router that is in IPv4 address format.
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
    sample: ["ipv4-family vpn-instance a"]
'''


class BgpSite(object):
    """Manange vpn instance"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # bgp vrf info
        self.vrfname = self.module.params['vrfname']
        self.vrfsession = self.module.params['vrfsession']
        self.defaultaftype = self.module.params['defaultaftype']
        self.connretrytime = self.module.params['connretrytime']
        self.holdtime = self.module.params['holdtime']
        self.keepalivetime = self.module.params['keepalivetime']
        self.minholdtime = self.module.params['minholdtime']
        self.vrfridautosel = self.module.params['vrfridautosel']
        self.routerid = self.module.params['routerid']
        self.ebgpifsensitive = self.module.params['ebgpifsensitive']

        self.state = self.module.params['state']

        # bgp vrf info
        self.vrf_info = dict()

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

        # check site
        # if self.vrfname:
        #    if len(self.vrfname) > 31 or len(self.vrfname) == 0:
        #        module.fail_json(
        #            msg='The len of vrfname %s is out of [1 - 31].' % self.vrfname)
        #
        # if self.connretrytime:
        #    if int(self.connretrytime) > 65535 or int(self.connretrytime) < 1:
        #        module.fail_json(
        #            msg='connretrytime %s is out of [1 - 65535].' % self.connretrytime)
        # if self.holdtime:
        #    if int(self.holdtime) != 0 and int(self.holdtime) > 65535 or int(self.holdtime) < 3:
        #        module.fail_json(
        #            msg='holdtime %s is out of [3 - 65535].' % self.holdtime)
        # if self.keepalivetime:
        #    if int(self.keepalivetime) > 21845 or int(self.keepalivetime) < 0:
        #        module.fail_json(
        #            msg='keepalivetime %s is out of [0 - 21845].' % self.keepalivetime)
        #
        # if self.minholdtime:
        #    if int(self.minholdtime) != 0 and int(self.minholdtime) < 20 or int(self.minholdtime) > 65535:
        #        self.module.fail_json(
        # msg='Error: minholdtime is not in the range from 20 to 65535.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_vrf_dict(self):
        """ get one vrf attributes dict."""

        vrf_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_BGP_VRF_HEAD

        # Body info
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        # conf_str = constr_leaf_novalue(conf_str, "vrfSession")
        # conf_str = constr_leaf_novalue(conf_str, "defaultAfType")
        # conf_str = constr_leaf_novalue(conf_str, "connRetryTime")
        # conf_str = constr_leaf_novalue(conf_str, "holdTime")
        # conf_str = constr_leaf_novalue(conf_str, "keepaliveTime")
        # conf_str = constr_leaf_novalue(conf_str, "minHoldTime")
        # conf_str = constr_leaf_novalue(conf_str, "vrfRidAutoSel")
        # conf_str = constr_leaf_novalue(conf_str, "routerId")
        # conf_str = constr_leaf_novalue(conf_str, "ebgpIfSensitive")

        # Tail info
        conf_str += NE_COMMON_XML_GET_BGP_VRF_TAIL
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return vrf_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # get process base info
        # re_find = re.findall(
        #    r'.*<instanceId>(.*)</instanceId>.*', xml_str)

        root = ElementTree.fromstring(xml_str)
        bgpVrf = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf")
        # if bgpVrf is not None:
        if len(bgpVrf) != 0:
            for vrf in bgpVrf:
                if vrf.tag in ["vrfName",
                               "vrfSession",
                               "defaultAfType",
                               "connRetryTime",
                               "holdTime",
                               "keepaliveTime",
                               "minHoldTime",
                               "vrfRidAutoSel",
                               "routerId",
                               "ebgpIfSensitive"
                               ]:
                    vrf_info[vrf.tag.lower()] = vrf.text

        return vrf_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        self.proposed["state"] = self.state

        if self.vrfsession:
            self.proposed["vrfsession"] = self.vrfsession
        if self.defaultaftype:
            self.proposed["defaultaftype"] = self.defaultaftype
        if self.connretrytime:
            self.proposed["connretrytime"] = self.connretrytime
        if self.holdtime:
            self.proposed["holdtime"] = self.holdtime
        if self.keepalivetime:
            self.proposed["keepalivetime"] = self.keepalivetime
        if self.minholdtime:
            self.proposed["minholdtime"] = self.minholdtime
        if self.vrfridautosel:
            self.proposed["vrfridautosel"] = self.vrfridautosel
        if self.routerid:
            self.proposed["routerid"] = self.routerid
        if self.ebgpifsensitive:
            self.proposed["ebgpifsensitive"] = self.ebgpifsensitive

    def get_existing(self):
        """get existing info"""
        if not self.vrf_info:
            return

        self.existing = copy.deepcopy(self.vrf_info)

    def get_end_state(self):
        """get end state info"""

        vrf_info = self.get_vrf_dict()
        if not vrf_info:
            return

        self.end_state = copy.deepcopy(vrf_info)

    def common_process(self, operationType, operationDesc):
        """Common site process"""
        # Head process
        xml_str = NE_BGP_INSTANCE_HEADER % operationType
        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        # yang process leaf delete
        if self.connretrytime is not None:
            if len(self.connretrytime) == 0:
                xml_str = constr_leaf_delete(
                    xml_str, "connRetryTime", self.connretrytime)
            else:
                xml_str = constr_leaf_value(
                    xml_str, "connRetryTime", self.connretrytime)
        if self.holdtime is not None:
            if len(self.holdtime) == 0:
                xml_str = constr_leaf_delete(
                    xml_str, "holdTime", self.holdtime)
            else:
                xml_str = constr_leaf_value(xml_str, "holdTime", self.holdtime)
        if self.keepalivetime is not None:
            if len(self.keepalivetime) == 0:
                xml_str = constr_leaf_delete(
                    xml_str, "keepaliveTime", self.keepalivetime)
            else:
                xml_str = constr_leaf_value(
                    xml_str, "keepaliveTime", self.keepalivetime)
        if self.minholdtime is not None:
            if len(self.minholdtime) == 0:
                xml_str = constr_leaf_delete(
                    xml_str, "minHoldTime", self.minholdtime)
            else:
                xml_str = constr_leaf_value(
                    xml_str, "minHoldTime", self.minholdtime)
        xml_str = constr_leaf_value(xml_str, "vrfSession", self.vrfsession)
        xml_str = constr_leaf_value(
            xml_str, "defaultAfType", self.defaultaftype)
        xml_str = constr_leaf_value(
            xml_str, "vrfRidAutoSel", self.vrfridautosel)
        xml_str = constr_leaf_value(xml_str, "routerId", self.routerid)
        xml_str = constr_leaf_value(
            xml_str, "ebgpIfSensitive", self.ebgpifsensitive)

        # Tail process
        xml_str += NE_BGP_INSTANCE_TAIL
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # 命令行更新待补充其他
        if self.vrfname:
            if self.defaultaftype == "ipv4uni" or self.defaultaftype is None:
                self.updates_cmd.append(
                    "ipv4-family vpn-instance %s" %
                    self.vrfname)
            elif self.defaultaftype == "ipv6uni":
                self.updates_cmd.append(
                    "ipv6-family vpn-instance %s" %
                    self.vrfname)

        if self.vrfsession is not None:
            if self.vrfsession == "true":
                self.updates_cmd.append("vpn-instance %s" % self.vrfname)
            else:
                self.updates_cmd.append("undo vpn-instance %s" % self.vrfname)

        if self.keepalivetime is not None:
            if len(self.keepalivetime) != 0:
                self.updates_cmd.append(
                    "timer keepalive %s" %
                    self.keepalivetime)
            else:
                self.updates_cmd.append("undo timer keepalive")
        if self.holdtime is not None:
            if len(self.holdtime) != 0:
                self.updates_cmd.append("hold %s" % self.holdtime)
            else:
                self.updates_cmd.append("undo hold")
        if self.minholdtime is not None:
            if len(self.minholdtime) != 0:
                self.updates_cmd.append("min-holdtime %s" % self.minholdtime)
            else:
                self.updates_cmd.append("undo  min-holdtime")

        if self.vrfridautosel is not None:
            if self.vrfridautosel == "true":
                self.updates_cmd.append("router-id auto-select")
            else:
                self.updates_cmd.append("undo router-id auto-select")

        if self.vrfridautosel is not None:
            if self.ebgpifsensitive == "true":
                self.updates_cmd.append("ebgp-interface-sensitive")
            else:
                self.updates_cmd.append("undo ebgp-interface-sensitive")

        if self.connretrytime is not None:
            if len(self.connretrytime) != 0:
                self.updates_cmd.append(
                    "timer connect-retry %s" %
                    self.connretrytime)
            else:
                self.updates_cmd.append("undo timer connect-retry")

        if self.routerid:
            self.updates_cmd.append("router-id %s " % self.routerid)

    def create_process(self):
        """Create bgp process"""

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge bgp process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete bgp  process"""
        # Head process
        xml_str = NE_BGP_INSTANCE_HEADER % NE_COMMON_XML_OPERATION_DELETE
        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_leaf_value(xml_str, "vrfSession", self.vrfsession)
        # Tail process
        xml_str += NE_BGP_INSTANCE_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        self.updates_cmd.append("undo vpn-instance %s" % self.vrfname)
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.vrf_info = self.get_vrf_dict()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.vrf_info:
                # create vrf process
                self.create_process()
            else:
                # merge vrf process
                self.merge_process()
        elif self.state == "absent":
            if self.vrf_info:
                # remove vrf process
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: BGP instance does not exist')
        elif self.state == "query":
            # 查询输出
            if not self.vrf_info:
                self.module.fail_json(msg='Error: BGP instance does not exist')

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
        vrfname=dict(required=True, type='str'),
        vrfsession=dict(required=False, choices=['true', 'false']),
        defaultaftype=dict(required=False, choices=['ipv4uni', 'ipv6uni']),
        connretrytime=dict(required=False, type='str'),
        holdtime=dict(required=False, type='str'),
        keepalivetime=dict(required=False, type='str'),
        minholdtime=dict(required=False, type='str'),
        vrfridautosel=dict(required=False, choices=['true', 'false']),
        routerid=dict(required=False, type='str'),
        ebgpifsensitive=dict(required=False, choices=['true', 'false']),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = BgpSite(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
