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
    asnumber:
        description:
            - Local AS number.
              The value is a string of 1 to 11 characters.
        required: false
        default: null
    bgpenable:
        description:
            - Enable BGP. By default, BGP is disabled.
        required: false
        default: false
        choices: ['true','false']
    gracefulrestart:
        description:
            - Enable GR of the BGP speaker in the specified address family, peer address, or peer group.
        required: false
        default: false
        choices: ['true','false']
    timewaitforrib:
        description:
            - Period of waiting for the End-Of-RIB flag.
              The value is an integer ranging from 3 to 3000. The default value is 600.
        required: false
        default: null
    bgpridautosel:
        description:
            - The function to automatically select router IDs for all VPN BGP instances is enabled.
        required: false
        default: false
        choices: ['true','false']
    keepallroutes:
        description:
            - If the value is true, the system stores all route update messages received from all peers (groups) after
              BGP connection setup.
              If the value is false, the system stores only BGP update messages that are received from peers and pass
              the configured import policy.
        required: false
        default: false
        choices: ['true','false']
    grpeerreset:
        description:
            - Peer disconnection through GR.
        required: false
        default: false
        choices: ['true','false']
    isshutdown:
        description:
            - Interrupt BGP all neighbor.
        required: false
        default: false
        choices: ['true','false']
    restarttime:
        description:
            - Peer restart time. The range is 3-3600.
        required: false
        default: 150
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
NE_COMMON_XML_PROCESS_BGP_SITE_HEAD = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <bgp xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp">
            <bgpcomm>
                <bgpSite xc:operation="%s">
"""

NE_COMMON_XML_PROCESS_BGP_SITE_TAIL = """
                </bgpSite>
            </bgpcomm>
        </bgp>
    </config>
"""
NE_COMMON_XML_GET_BGP_SITE_HEAD = """
    <filter type="subtree">
        <bgp xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp">
            <bgpcomm>
                <bgpSite>
"""

NE_COMMON_XML_GET_BGP_SITE_TAIL = """
                </bgpSite>
            </bgpcomm>
        </bgp>
    </filter>
"""


class BgpSite(object):
    """Manange vpn instance"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # bgp site info
        self.asnumber = self.module.params['asnumber']
        self.bgpenable = self.module.params['bgpenable']
        self.aspathlimit = self.module.params['aspathlimit']
        self.bgpridautosel = self.module.params['bgpridautosel']
        self.checkfirstas = self.module.params['checkfirstas']
        self.confedidnumber = self.module.params['confedidnumber']
        self.confednonstanded = self.module.params['confednonstanded']
        self.gracefulrestart = self.module.params['gracefulrestart']
        self.grpeerreset = self.module.params['grpeerreset']
        self.isshutdown = self.module.params['isshutdown']
        self.keepallroutes = self.module.params['keepallroutes']
        self.timewaitforrib = self.module.params['timewaitforrib']
        self.restarttime = self.module.params['restarttime']
        self.suppressinterval = self.module.params['suppressinterval']
        self.holdinterval = self.module.params['holdinterval']
        self.clearinterval = self.module.params['clearinterval']

        self.state = self.module.params['state']

        # bgp site info
        self.site_info = dict()

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
        # if self.asnumber:
        #    if len(self.asnumber) > 11 or len(self.asnumber) == 0:
        #        self.module.fail_json(
        #           msg='Error: The len of as_number %s is out of [1 - 11].' % self.asnumber)
        #
        # if self.timewaitforrib:
        #    if self.timewaitforrib < 3 or self.timewaitforrib > 3000:
        #        self.module.fail_json(
        #            msg='Error: timewaitforrib is not in the range from 3 to 3000.')
        #
        # if self.restarttime:
        #    if self.restarttime < 3 or self.restarttime > 3600:
        #        self.module.fail_json(
        # msg='Error: restarttime is not in the range from 3 to 3600.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_vrf_dict(self):
        """ get one vrf attributes dict."""

        site_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_BGP_SITE_HEAD

        # Body info
        conf_str = constr_leaf_novalue(conf_str, "asNumber")
        conf_str = constr_leaf_novalue(conf_str, "bgpEnable")
        conf_str = constr_leaf_novalue(conf_str, "asPathLimit")
        conf_str = constr_leaf_novalue(conf_str, "bgpRidAutoSel")
        conf_str = constr_leaf_novalue(conf_str, "checkFirstAs")
        conf_str = constr_leaf_novalue(conf_str, "confedIdNumber")
        conf_str = constr_leaf_novalue(conf_str, "confedNonstanded")
        conf_str = constr_leaf_novalue(conf_str, "gracefulRestart")
        conf_str = constr_leaf_novalue(conf_str, "grPeerReset")
        conf_str = constr_leaf_novalue(conf_str, "isShutdown")
        conf_str = constr_leaf_novalue(conf_str, "keepAllRoutes")
        conf_str = constr_leaf_novalue(conf_str, "timeWaitForRib")
        conf_str = constr_leaf_novalue(conf_str, "restartTime")
        conf_str = constr_leaf_novalue(conf_str, "suppressInterval")
        conf_str = constr_leaf_novalue(conf_str, "holdInterval")
        conf_str = constr_leaf_novalue(conf_str, "clearInterval")

        # Tail info
        conf_str += NE_COMMON_XML_GET_BGP_SITE_TAIL
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return site_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # get process base info
        # re_find = re.findall(
        #    r'.*<instanceId>(.*)</instanceId>.*', xml_str)

        root = ElementTree.fromstring(xml_str)
        bgpSite = root.find("bgp/bgpcomm/bgpSite")
        # if bgpSite is not None:
        if len(bgpSite) != 0:
            for site in bgpSite:
                if site.tag in ["asNumber",
                                "bgpEnable",
                                "asPathLimit",
                                "bgpRidAutoSel",
                                "checkFirstAs",
                                "confedIdNumber",
                                "confedNonstanded",
                                "gracefulRestart",
                                "grPeerReset",
                                "isShutdown",
                                "keepAllRoutes",
                                "timeWaitForRib",
                                "restartTime",
                                "suppressInterval",
                                "holdInterval",
                                "clearInterval"
                                ]:
                    site_info[site.tag.lower()] = site.text

        return site_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["state"] = self.state

        if self.asnumber:
            self.proposed["asnumber"] = self.asnumber
        if self.bgpenable:
            self.proposed["bgpenable"] = self.bgpenable
        if self.aspathlimit:
            self.proposed["aspathlimit"] = self.aspathlimit
        if self.bgpridautosel:
            self.proposed["bgpridautosel"] = self.bgpridautosel
        if self.checkfirstas:
            self.proposed["checkfirstas"] = self.checkfirstas
        if self.confedidnumber:
            self.proposed["confedidnumber"] = self.confedidnumber
        if self.confednonstanded:
            self.proposed["confednonstanded"] = self.confednonstanded
        if self.gracefulrestart:
            self.proposed["gracefulrestart"] = self.gracefulrestart
        if self.grpeerreset:
            self.proposed["grpeerreset"] = self.grpeerreset
        if self.isshutdown:
            self.proposed["isshutdown"] = self.isshutdown
        if self.keepallroutes:
            self.proposed["keepallroutes"] = self.keepallroutes
        if self.timewaitforrib:
            self.proposed["timewaitforrib"] = self.timewaitforrib
        if self.restarttime:
            self.proposed["restarttime"] = self.restarttime
        if self.suppressinterval:
            self.proposed["suppressinterval"] = self.suppressinterval
        if self.holdinterval:
            self.proposed["holdinterval"] = self.holdinterval
        if self.clearinterval:
            self.proposed["clearinterval"] = self.clearinterval

    def get_existing(self):
        """get existing info"""
        if not self.site_info:
            return

        self.existing = copy.deepcopy(self.site_info)

    def get_end_state(self):
        """get end state info"""

        site_info = self.get_vrf_dict()
        if not site_info:
            return

        self.end_state = copy.deepcopy(site_info)

    def common_process(self, operationType, operationDesc):
        """Common site process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_BGP_SITE_HEAD % operationType
        # Body process
        xml_str = constr_leaf_value(xml_str, "asNumber", self.asnumber)
        xml_str = constr_leaf_value(xml_str, "bgpEnable", self.bgpenable)
        xml_str = constr_leaf_value(xml_str, "asPathLimit", self.aspathlimit)
        xml_str = constr_leaf_value(
            xml_str, "bgpRidAutoSel", self.bgpridautosel)
        xml_str = constr_leaf_value(xml_str, "checkFirstAs", self.checkfirstas)
        xml_str = constr_leaf_value(
            xml_str, "confedIdNumber", self.confedidnumber)
        xml_str = constr_leaf_value(
            xml_str, "confedNonstanded", self.confednonstanded)
        xml_str = constr_leaf_value(
            xml_str, "gracefulRestart", self.gracefulrestart)
        xml_str = constr_leaf_value(xml_str, "grPeerReset", self.grpeerreset)
        xml_str = constr_leaf_value(xml_str, "isShutdown", self.isshutdown)
        xml_str = constr_leaf_value(
            xml_str, "keepAllRoutes", self.keepallroutes)
        xml_str = constr_leaf_value(
            xml_str, "timeWaitForRib", self.timewaitforrib)
        xml_str = constr_leaf_value(xml_str, "restartTime", self.restarttime)
        xml_str = constr_leaf_value(
            xml_str, "suppressInterval", self.suppressinterval)
        xml_str = constr_leaf_value(xml_str, "holdInterval", self.holdinterval)
        xml_str = constr_leaf_value(
            xml_str, "clearInterval", self.clearinterval)

        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_BGP_SITE_TAIL
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # 命令行更新待补充其他
        if self.asnumber:
            self.updates_cmd.append("bgp %s " % self.asnumber)

        if self.aspathlimit:
            self.updates_cmd.append("as-path-limit %s " % self.aspathlimit)

        if self.bgpridautosel is not None:
            if self.bgpridautosel == "true":
                self.updates_cmd.append("router-id vpn-instance auto-select")
            else:
                self.updates_cmd.append(
                    "undo router-id vpn-instance auto-select")

        if self.checkfirstas is not None:
            if self.checkfirstas == "true":
                self.updates_cmd.append("check-first-as")
            else:
                self.updates_cmd.append("undo rcheck-first-as")

        if self.confedidnumber:
            self.updates_cmd.append(
                "confederation id %s " %
                self.confedidnumber)

        if self.confednonstanded is not None:
            if self.confednonstanded == "true":
                self.updates_cmd.append("confederation nonstandard")
            else:
                self.updates_cmd.append("undo confederation nonstandard")

        if self.gracefulrestart is not None:
            if self.gracefulrestart == "true":
                self.updates_cmd.append("graceful-restart")
            else:
                self.updates_cmd.append("undo graceful-restart")

        if self.grpeerreset is not None:
            if self.grpeerreset == "true":
                self.updates_cmd.append("graceful-restart peer-reset")
            else:
                self.updates_cmd.append("undo graceful-restart peer-reset")

        if self.isshutdown is not None:
            if self.isshutdown == "true":
                self.updates_cmd.append("shutdown")
            else:
                self.updates_cmd.append("undo shutdown")

        if self.keepallroutes is not None:
            if self.keepallroutes == "true":
                self.updates_cmd.append("keep-all-routes")
            else:
                self.updates_cmd.append("undo keep-all-routes")

        if self.timewaitforrib:
            self.updates_cmd.append(
                "graceful-restart timer wait-for-rib %s " %
                self.timewaitforrib)

        if self.restarttime:
            self.updates_cmd.append(
                "graceful-restart timer restart %s " %
                self.restarttime)

        if self.suppressinterval:
            self.updates_cmd.append(
                "nexthop recursive-lookup restrain suppress-interval %s " %
                self.suppressinterval)

        if self.holdinterval:
            self.updates_cmd.append(
                "nexthop recursive-lookup restrain hold-interval %s " %
                self.holdinterval)

        if self.clearinterval:
            self.updates_cmd.append(
                "nexthop recursive-lookup restrain clear-interval %s " %
                self.clearinterval)

    def create_process(self):
        # """Create l3vpn process"""

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge bgp process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete bgp  process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_BGP_SITE_HEAD % NE_COMMON_XML_OPERATION_DELETE
        # Body process
        xml_str = constr_leaf_value(xml_str, "bgpEnable", self.bgpenable)
        xml_str = constr_leaf_value(xml_str, "asNumber", self.asnumber)
        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_BGP_SITE_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        self.updates_cmd.append("undo bgp %s" % self.asnumber)
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.site_info = self.get_vrf_dict()
        self.get_proposed()
        self.get_existing()
        # deal present or absent
        if self.state == "present":
            if not self.site_info:
                # create bgp process
                self.create_process()
            else:
                # merge bgp process
                self.merge_process()
        elif self.state == "absent":
            # if self.site_info:
                # # remove bgp process
            self.delete_process()
            # else:
            # self.module.fail_json(msg='Error: BGP site does not exist')
        # elif self.state == "query":
            # # 查询输出
            # if not self.site_info:
            # self.module.fail_json(msg='Error: BGP site does not exist')

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
        asnumber=dict(required=False, type='str'),
        bgpenable=dict(required=False, choices=['true', 'false']),
        aspathlimit=dict(required=False, type='int'),
        bgpridautosel=dict(required=False, choices=['true', 'false']),
        checkfirstas=dict(required=False, choices=['true', 'false']),
        confedidnumber=dict(required=False, type='str'),
        confednonstanded=dict(required=False, choices=['true', 'false']),
        gracefulrestart=dict(required=False, choices=['true', 'false']),
        grpeerreset=dict(required=False, choices=['true', 'false']),
        isshutdown=dict(required=False, choices=['true', 'false']),
        keepallroutes=dict(required=False, choices=['true', 'false']),
        timewaitforrib=dict(required=False, type='int'),
        restarttime=dict(required=False, type='int'),
        suppressinterval=dict(required=False, type='int'),
        holdinterval=dict(required=False, type='int'),
        clearinterval=dict(required=False, type='int'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = BgpSite(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
