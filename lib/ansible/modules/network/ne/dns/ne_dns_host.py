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
module: ne_dns_host
version_added: "2.6"
short_description: Manages DNS host configuration on HUAWEI netengine switches.
description:
    - Manages DNS host configurations on HUAWEI netengine switches.
author:
    - Lee (@netengine-Ansible)
options:
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent','query']
    vrf_name:
        description:
            - VPN name. The value is a string of 1 to 31 case-sensitive characters.
        required: true
        default: null
    host_name:
        description:
            - Host name. The value is a string of 1 to 255 case-sensitive characters.
        required: true
        default: null
    host_address:
        description:
            - The address of host. When host_type is "ipv4-host", the value is IPv4 address in dotted decimal notation.
               When host_type is "ipv6-host", the value is IPv6 address in the format of X:X:X:X:X:X:X:X.
        required: true
        default: null
    host_type:
        description:
            - Host type.
        required: true
        default: null
'''

EXAMPLES = '''

- name: ne_test DNS host test
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

  - name: "Config DNS IPv4 host"
    ne_dns_host:
      state: present
      vrf_name: vpna
      host_name: huawei
      host_address: 1.1.1.1
      host_type: ipv4-host
      provider: "{{ cli }}"

  - name: "Config DNS IPv6 host"
    ne_dns_host:
      state: present
      vrf_name: vpna
      host_name: huawei
      host_address: 1::1
      host_type: ipv6-host
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
    sample: {"vrf_name": "vpna", "host_name": "huawei", "host_address": "1.1.1.1", state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"vrf_name": ["vpna"], "host_name": ["huawei"], "host_address": ["1.1.1.1"]}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"vrf_name": ["vpna"], "host_name": ["huawei"], "host_address": ["1.1.1.1"]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["ip host huawei 1.1.1.1 vpn-instance vpna"]
'''


SUCCESS = """success"""
FAILED = """failed"""

# get dns server ipv4  source info
NE_GET_DNS_IPV4_HOST_HEADER = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv4Hosts>
          <dnsIpv4Host>
"""
NE_GET_DNS_IPV4_HOST_TAIL = """
          </dnsIpv4Host>
        </dnsIpv4Hosts>
      </dns>
    </filter>
"""

# merge dns server ipv4  source info
NE_MERGE_DNS_IPV4_HOST_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv4Hosts>
          <dnsIpv4Host xc:operation="merge">
"""
NE_MERGE_DNS_IPV4_HOST_TAIL = """
          </dnsIpv4Host>
        </dnsIpv4Hosts>
      </dns>
    </config>
"""

# create dns server ipv4  source info
NE_CREATE_DNS_IPV4_HOST_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv4Hosts>
          <dnsIpv4Host xc:operation="create">
"""
NE_CREATE_DNS_IPV4_HOST_TAIL = """
          </dnsIpv4Host>
        </dnsIpv4Hosts>
      </dns>
    </config>
"""

# delete dns server ipv4  source info
NE_DELETE_DNS_IPV4_HOST_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv4Hosts>
          <dnsIpv4Host xc:operation="delete">
"""
NE_DELETE_DNS_IPV4_HOST_TAIL = """
          </dnsIpv4Host>
        </dnsIpv4Hosts>
      </dns>
    </config>
"""

# get dns server ipv6  source info
NE_GET_DNS_IPV6_HOST_HEADER = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv6Hosts>
          <dnsIpv6Host>
"""
NE_GET_DNS_IPV6_HOST_TAIL = """
          </dnsIpv6Host>
        </dnsIpv6Hosts>
      </dns>
    </filter>
"""

# merge dns server ipv6  source info
NE_MERGE_DNS_IPV6_HOST_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv6Hosts>
          <dnsIpv6Host xc:operation="merge">
"""
NE_MERGE_DNS_IPV6_HOST_TAIL = """
          </dnsIpv6Host>
        </dnsIpv6Hosts>
      </dns>
    </config>
"""

# create dns server ipv6  source info
NE_CREATE_DNS_IPV6_HOST_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv6Hosts>
          <dnsIpv6Host xc:operation="create">
"""
NE_CREATE_DNS_IPV6_HOST_TAIL = """
          </dnsIpv6Host>
        </dnsIpv6Hosts>
      </dns>
    </config>
"""

# delete dns server ipv6  source info
NE_DELETE_DNS_IPV6_HOST_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv6Hosts>
          <dnsIpv6Host xc:operation="delete">
"""
NE_DELETE_DNS_IPV6_HOST_TAIL = """
          </dnsIpv6Host>
        </dnsIpv6Hosts>
      </dns>
    </config>
"""


def check_ipv4_address(self, ipv4_address):
    address = ipv4_address.strip().split('.')

    if len(address) != 4:
        return FAILED

    for i in range(4):
        address[i] = int(address[i])

        if address[i] <= 255 and address[i] >= 0:
            pass
        else:
            return FAILED
    return SUCCESS


def check_ipv6_address(self, ipv6_address):
    return SUCCESS


def check_vrf_name(self, vrf_name):
    if len(vrf_name) > 31 or len(vrf_name.replace(' ', '')) < 1:
        return FAILED
    return SUCCESS


def check_host_name(self, host_name):
    if len(host_name) > 255 or len(host_name.replace(' ', '')) < 1:
        return FAILED
    return SUCCESS


class DnsHost(object):
    """ Manages DNS configuration """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # dns host config info
        self.vrf_name = self.module.params['vrf_name']
        self.host_name = self.module.params['host_name']
        self.host_address = self.module.params['host_address']
        self.host_type = self.module.params['host_type']

        self.state = self.module.params['state']

        # dns global info
        self.dnsHost_info = dict()

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

    def check_dns_ipv4_host_args(self):
        """ check_dns_ipv4_host_args """

        need_cfg = False

        vrf_name = self.vrf_name
        host_name = self.host_name
        host_address = self.host_address

        if not vrf_name:
            self.module.fail_json(
                msg='Error: IPv4 host vpn instance name is invalid.')

        if not host_name:
            self.module.fail_json(
                msg='Error: The IPv4 host name is invalid.')

        if not host_address:
            self.module.fail_json(
                msg='Error: The IPv4 host address is invalid.')

        if vrf_name and host_name and host_address:
            if check_vrf_name(self, vrf_name) == FAILED:
                self.module.fail_json(
                    msg='Error: IPv4 host vpn instance name  is not in the range from 1 to 31.')

            if check_host_name(self, host_name) == FAILED:
                self.module.fail_json(
                    msg='Error: The IPv4 host name %s is invalid.' % host_name)

            if check_ipv4_address(self, host_address) == FAILED:
                self.module.fail_json(
                    msg='Error: The IPv4 host address %s is invalid.' % host_address)

            need_cfg = True

        return need_cfg

    def check_dns_ipv6_host_args(self):
        """ check_dns_ipv6_host_args """

        need_cfg = False

        vrf_name = self.vrf_name
        host_name = self.host_name
        host_address = self.host_address

        if not vrf_name:
            self.module.fail_json(
                msg='Error: IPv6 host vpn instance name is invalid.')

        if not host_name:
            self.module.fail_json(
                msg='Error: The IPv6 host name is invalid.')

        if not host_address:
            self.module.fail_json(
                msg='Error: The IPv6 host address is invalid.')

        if vrf_name and host_name and host_address:
            if check_vrf_name(self, vrf_name) == FAILED:
                self.module.fail_json(
                    msg='Error:  IPv6 host vpn instance name  is not in the range from 1 to 31.')

            if check_host_name(self, host_name) == FAILED:
                self.module.fail_json(
                    msg='Error: The IPv6 host name %s is invalid.' % host_name)

            if check_ipv6_address(self, host_address) == FAILED:
                self.module.fail_json(
                    msg='Error: The IPv6 host address %s is invalid.' % host_address)

            need_cfg = True

        return need_cfg

    def get_dns_ipv4_host(self):
        """ get_dns_ipv4_host """

        conf_str = NE_GET_DNS_IPV4_HOST_HEADER

        vrf_name = self.vrf_name
        host_name = self.host_name
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if host_name:
            conf_str += "<host>%s</host>" % host_name

        conf_str += NE_GET_DNS_IPV4_HOST_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<vrfName>(.*)</vrfName>.*\s*<host>(.*)</host>.*\s*<ipv4Addr>(.*)</ipv4Addr>.*\s*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_dns_ipv4_host(self):
        """ merge_dns_ipv4_host """

        conf_str = NE_MERGE_DNS_IPV4_HOST_HEADER

        vrf_name = self.vrf_name
        host_name = self.host_name
        host_address = self.host_address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if host_name:
            conf_str += "<host>%s</host>" % host_name

        if host_address:
            conf_str += "<ipv4Addr>%s</ipv4Addr>" % host_address

        conf_str += NE_MERGE_DNS_IPV4_HOST_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge dns IPv4 host failed.')

        cmds = []
        if vrf_name and host_name and host_address:
            cmd = "ip host %s %s vpn-instance %s" % (
                host_name, host_address, vrf_name)

        cmds.append(cmd)

        return cmds

    def create_dns_ipv4_host(self):
        """ create_dns_ipv4_host """

        conf_str = NE_CREATE_DNS_IPV4_HOST_HEADER

        vrf_name = self.vrf_name
        host_name = self.host_name
        host_address = self.host_address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if host_name:
            conf_str += "<host>%s</host>" % host_name

        if host_address:
            conf_str += "<ipv4Addr>%s</ipv4Addr>" % host_address

        conf_str += NE_CREATE_DNS_IPV4_HOST_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Create dns IPv4 host failed.')

        cmds = []
        if host_name and host_address and vrf_name:
            cmd = "ip host %s %s vpn-instance %s" % (
                host_name, host_address, vrf_name)

        cmds.append(cmd)

        return cmds

    def delete_dns_ipv4_host(self):
        """ delete_dns_ipv4_host """

        conf_str = NE_DELETE_DNS_IPV4_HOST_HEADER

        vrf_name = self.vrf_name
        host_name = self.host_name
        host_address = self.host_address
        if vrf_name and host_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name
            conf_str += "<host>%s</host>" % host_name

        conf_str += NE_DELETE_DNS_IPV4_HOST_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete dns IPv4 hoste failed.')

        cmds = []
        cmd = "undo ip host %s " % host_name
        if host_address:
            cmd += "%s " % host_address

        cmd += "vpn-instance %s" % vrf_name
        cmds.append(cmd)

        return cmds

    def get_dns_ipv6_host(self):
        """ get_dns_ipv6_host """

        conf_str = NE_GET_DNS_IPV6_HOST_HEADER

        vrf_name = self.vrf_name
        host_name = self.host_name
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if host_name:
            conf_str += "<host>%s</host>" % host_name

        conf_str += NE_GET_DNS_IPV6_HOST_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<vrfName>(.*)</vrfName>.*\s*<host>(.*)</host>.*\s*<ipv6Addr>(.*)</ipv6Addr>.*\s*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_dns_ipv6_host(self):
        """ merge_dns_ipv6_host """

        conf_str = NE_MERGE_DNS_IPV6_HOST_HEADER

        vrf_name = self.vrf_name
        host_name = self.host_name
        host_address = self.host_address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if host_name:
            conf_str += "<host>%s</host>" % host_name

        if host_address:
            conf_str += "<ipv6Addr>%s</ipv6Addr>" % host_address

        conf_str += NE_MERGE_DNS_IPV6_HOST_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge dns IPv6 host failed.')

        cmds = []
        if vrf_name and host_name and host_address:
            cmd = "ipv6 host %s %s vpn-instance %s" % (
                vrf_name, host_name, host_address)

        cmds.append(cmd)

        return cmds

    def create_dns_ipv6_host(self):
        """ create_dns_ipv6_host """

        conf_str = NE_CREATE_DNS_IPV6_HOST_HEADER

        vrf_name = self.vrf_name
        host_name = self.host_name
        host_address = self.host_address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if host_name:
            conf_str += "<host>%s</host>" % host_name

        if host_address:
            conf_str += "<ipv6Addr>%s</ipv6Addr>" % host_address

        conf_str += NE_CREATE_DNS_IPV6_HOST_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Create dns IPv6 host failed.')

        cmds = []
        if vrf_name and host_name and host_address:
            cmd = "ipv6 host %s %s vpn-instance %s" % (
                host_address, host_name, vrf_name)

        cmds.append(cmd)

        return cmds

    def delete_dns_ipv6_host(self):
        """ delete_dns_ipv6_host """

        conf_str = NE_DELETE_DNS_IPV6_HOST_HEADER

        vrf_name = self.vrf_name
        host_name = self.host_name
        host_address = self.host_address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if host_name:
            conf_str += "<host>%s</host>" % host_name

        conf_str += NE_DELETE_DNS_IPV6_HOST_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete dns IPv6 host failed.')

        cmds = []
        cmd = "undo ipv6 host %s " % host_name
        if host_address:
            cmd += "%s " % host_address

        cmd += "vpn-instance %s" % vrf_name
        cmds.append(cmd)

        return cmds

    def work(self):
        """worker"""

        if self.vrf_name:
            self.proposed["vrf_name"] = self.vrf_name

        if self.host_name:
            self.proposed["host_name"] = self.host_name

        if self.host_address:
            self.proposed["host_address"] = self.host_address

        if self.vrf_name:
            self.proposed["vrf_name"] = self.vrf_name

        if self.host_name:
            self.proposed["host_name"] = self.host_name

        if self.host_address:
            self.proposed["host_address"] = self.host_address

        config_dns_ipv4_host = False
        config_dns_ipv6_host = False
        if self.host_type == "ipv4-host":
            config_dns_ipv4_host = self.check_dns_ipv4_host_args()

        if self.host_type == "ipv6-host":
            config_dns_ipv6_host = self.check_dns_ipv6_host_args()

        # proc dns ipv4 host config
        if config_dns_ipv4_host:
            dns_ipv4_host_exist = self.get_dns_ipv4_host()
            if len(dns_ipv4_host_exist) > 0:
                self.existing["vrf_name"] = dns_ipv4_host_exist[0][0]
                self.existing["host_name"] = dns_ipv4_host_exist[0][1]
                self.existing["host_address"] = dns_ipv4_host_exist[0][1]

            if self.state == "present":
                if len(dns_ipv4_host_exist) > 0:
                    cmd = self.merge_dns_ipv4_host()
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    cmd = self.create_dns_ipv4_host()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)

            elif self.state == "absent":
                if len(dns_ipv4_host_exist) > 0:
                    cmd = self.delete_dns_ipv4_host()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    self.module.fail_json(
                        msg='Error: Dns IPv4 host does not exist.')

            elif self.state == "query":
                pass

            dns_dns_ipv4_host_state = self.get_dns_ipv4_host()
            if len(dns_dns_ipv4_host_state) > 0:
                self.end_state["vrf_name"] = dns_dns_ipv4_host_state[0][0]
                self.end_state["host_name"] = dns_dns_ipv4_host_state[0][1]
                self.end_state["host_address"] = dns_dns_ipv4_host_state[0][2]

        # proc dns server ipv6 source config
        if config_dns_ipv6_host:
            dns_ipv6_host_exist = self.get_dns_ipv6_host()
            if len(dns_ipv6_host_exist) > 0:
                self.existing["vrf_name"] = dns_ipv6_host_exist[0][0]
                self.existing["host_name"] = dns_ipv6_host_exist[0][1]
                self.existing["host_address"] = dns_ipv6_host_exist[0][2]

            if self.state == "present":
                if len(dns_ipv6_host_exist) > 0:
                    cmd = self.merge_dns_ipv6_host()
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    cmd = self.create_dns_ipv6_host()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)

            elif self.state == "absent":
                if len(dns_ipv6_host_exist) > 0:
                    cmd = self.delete_dns_ipv6_host()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    self.module.fail_json(
                        msg='Error: Dns IPv6 host does not exist.')

            elif self.state == "query":
                pass

            dns_ipv6_host_state = self.get_dns_ipv6_host()
            if len(dns_ipv6_host_state) > 0:
                self.end_state["vrf_name"] = dns_ipv6_host_state[0][0]
                self.end_state["host_name"] = dns_ipv6_host_state[0][1]
                self.end_state["host_address"] = dns_ipv6_host_state[0][1]

        # get end config
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        self.results['updates'] = self.updates_cmd

        self.module.exit_json(**self.results)


def main():
    """main"""

    argument_spec = dict(
        vrf_name=dict(required=True, type='str'),
        host_name=dict(required=True, type='str'),
        host_address=dict(required=True, type='str'),
        host_type=dict(required=True, choices=['ipv4-host', 'ipv6-host']),

        # 在此增加其他支持参数
        state=dict(
            required=False, default='present',
            choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = DnsHost(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
