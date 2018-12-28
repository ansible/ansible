# coding=utf-8
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

from ansible.module_utils.network.ne.ne import execute_nc_action_yang, ne_argument_spec
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
module: ne_dns_action
version_added: "2.6"
short_description: Manages DNS data clearance on HUAWEI netengine switches.
description:
    - Manages DNS data clearance on HUAWEI netengine switches.
author:
    - Lee (@netengine-Ansible)
options:
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['absent']
    vrf_name:
        description:
            - VPN name. The value is a string of 1 to 31 case-sensitive characters.
        required: false
        default: null
    reset_type:
        description:
            -  Type of DNS data.
        required: true
        default: null
        choices: ['ipv4-dynamic-host','ipv6-dynamic-host','packet']
'''

EXAMPLES = '''

- name: ne_test DNS data clear test
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

  - name: "Clear DNS IPv4 host"
    ne_dns_action:
      state: present
      vrf_name: vpna
      reset_type: ipv4-dynamic-host
      provider: "{{ cli }}"

  - name: "Clear Dns IPv6 host"
    ne_dns_action:
      state: present
      vrf_name: vpnb
      reset_type: ipv6-dynamic-host
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
    sample: {"vrf_name": "vpna", "reset_type": "ipv4-dynamic-host", state": "present"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["reset dns dynamic-host vpn-instance vpna"]
'''


SUCCESS = """success"""
FAILED = """failed"""

NE_DNS_RESET_IPV4_HOST = """
    <dns:clearIpv4Host xmlns:dns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dns:vrfName>%s</dns:vrfName>
    </dns:clearIpv4Host>
"""

NE_DNS_RESET_IPV6_HOST = """
    <dns:clearIpv6Host xmlns:dns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dns:vrfName>%s</dns:vrfName>
    </dns:clearIpv6Host>
"""

NE_DNS_RESET_PKT_STAT = """
    <dns:clearPktStat xmlns:dns="http://www.huawei.com/netconf/vrp/huawei-dns"/>
"""


def check_vrf_name(self, vrf_name):
    if len(vrf_name) > 31 or len(vrf_name.replace(' ', '')) < 1:
        return FAILED
    return SUCCESS


class DnsResetHost(object):
    """ Manages DNS configuration """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # dns host config info
        self.vrf_name = self.module.params['vrf_name']
        self.reset_type = self.module.params['reset_type']

        self.state = self.module.params['state']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()

    def init_module(self):
        """init_module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_dns_ipv4_host_args(self):
        """ check_dns_ipv4_host_args """

        need_cfg = False

        vrf_name = self.vrf_name
        reset_type = self.reset_type
        if reset_type == "ipv4-dynamic-host":
            need_cfg = True

        if vrf_name:
            if check_vrf_name(self, vrf_name) == FAILED:
                self.module.fail_json(
                    msg='Error: IPv4 host vpn instance name is not in the range from 1 to 31.')

        return need_cfg

    def check_dns_ipv6_host_args(self):
        """ check_dns_ipv6_host_args """

        need_cfg = False

        vrf_name = self.vrf_name
        reset_type = self.reset_type
        if reset_type == "ipv6-dynamic-host":
            need_cfg = True

        if vrf_name:
            if check_vrf_name(self, vrf_name) == FAILED:
                self.module.fail_json(
                    msg='Error: IPv6 host vpn instance name is not in the range from 1 to 31.')

        return need_cfg

    def check_dns_reset_pkt_stat_args(self):
        """ check_dns_reset_pkt_stat_args """

        need_cfg = False

        reset_type = self.reset_type
        if reset_type == "packet":
            need_cfg = True

        return need_cfg

    def reset_dns_ipv4_host(self):
        """ reset_dns_ipv4_host """

        vrf_name = self.vrf_name

        conf_str = NE_DNS_RESET_IPV4_HOST % vrf_name

        recv_xml = execute_nc_action_yang(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Reset dns IPv4 host failed.')

        cmds = []
        if vrf_name:
            cmd = "reset dns dynamic-host vpn-instance %s" % vrf_name

        cmds.append(cmd)

        return cmds

    def reset_dns_ipv6_host(self):
        """ merge_dns_ipv6_host """

        vrf_name = self.vrf_name

        conf_str = NE_DNS_RESET_IPV6_HOST % vrf_name

        recv_xml = execute_nc_action_yang(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Reset dns IPv6 host failed.')

        cmds = []
        if vrf_name:
            cmd = "reset dns ipv6 dynamic-host vpn-instance %s" % vrf_name

        cmds.append(cmd)

        return cmds

    def reset_dns_packet_statistic(self):
        """ reset_dns_packet_statistic """

        reset_type = self.reset_type

        conf_str = NE_DNS_RESET_PKT_STAT

        recv_xml = execute_nc_action_yang(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Reset dns packet statistic failed.')

        cmds = []
        if reset_type:
            cmd = "reset dns statistics packet"

        cmds.append(cmd)

        return cmds

    def work(self):
        """worker"""

        if self.vrf_name:
            self.proposed["vrf_name"] = self.vrf_name

        if self.reset_type:
            self.proposed["reset_type"] = self.reset_type

        reset_dns_ipv4_host = self.check_dns_ipv4_host_args()
        reset_dns_ipv6_host = self.check_dns_ipv6_host_args()
        reset_dns_pkt_stat = self.check_dns_reset_pkt_stat_args()

        # reset dns ipv4 dynamic host
        if reset_dns_ipv4_host:
            cmd = self.reset_dns_ipv4_host()
            self.changed = True
            for item in cmd:
                self.updates_cmd.append(item)

        # reset dns ipv6 dynamic host
        if reset_dns_ipv6_host:
            cmd = self.reset_dns_ipv6_host()
            self.changed = True
            for item in cmd:
                self.updates_cmd.append(item)

        # reset dns packet statistic
        if reset_dns_pkt_stat:
            cmd = self.reset_dns_packet_statistic()
            self.changed = True
            for item in cmd:
                self.updates_cmd.append(item)

        # get end config
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['updates'] = self.updates_cmd

        self.module.exit_json(**self.results)


def main():
    """main"""

    argument_spec = dict(
        vrf_name=dict(required=False, type='str'),
        reset_type=dict(
            required=True,
            choices=[
                'ipv4-dynamic-host',
                'ipv6-dynamic-host',
                'packet']),

        # 在此增加其他支持参数
        state=dict(
            required=False, default='absent',
            choices=['absent'])
    )
    argument_spec.update(ne_argument_spec)
    interface = DnsResetHost(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
