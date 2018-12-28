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
module: ne_dns_server
version_added: "2.6"
short_description: Manages DNS server configuration on HUAWEI netengine switches.
description:
    - Manages DNS server configurations on HUAWEI netengine switches.
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
        required: false
        default: null
    address:
        description:
            - Address of the DNS server.
              The value maye be IPv4 address in dotted decimal notation or IPv6 address in the format of X:X:X:X:X:X:X:X.
        required: false
        default: null
    sequence_num:
        description:
            - Sequence Number. The value is an integer data type.
        required: false
        default: null
    domain:
        description:
            - Domain name. The value is a string of 1 to 255 case-sensitive characters, without spaces.
              It is a combination of letters, numbers, periods (.), hyphens (-), or underlines (_), and contains at least one letter or number.
        required: false
        default: null
    config_type:
        description:
            - Type of DNS configuration.
        required: true
        default: null
        choices: ['ipv4-source','ipv6-source','domain','ipv4-destination','ipv6-destination']
'''

EXAMPLES = '''

- name: ne_test DNS server test
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

  - name: "Config DNS server IPv4 source"
    ne_dns_server:
      state: present
      vrf_name: vpna
      address: 1.1.1.1
      config_type: ipv4-source
      provider: "{{ cli }}"

  - name: "Config DNS server IPv6 source"
    ne_dns_server:
      state: present
      vrf_name: vpna
      address: 1::1
      config_type: ipv6-source
      provider: "{{ cli }}"

  - name: "Config DNS server domain"
    ne_dns_server:
      state: present
      vrf_name: vpna
      domain: huawei
      config_type: domain
      provider: "{{ cli }}"

  - name: "Config DNS server IPv4 destination"
    ne_dns_server:
      state: present
      vrf_name: vpna
      sequence_num: 1
      address: 1.1.1.1
      config_type: ipv4-destination
      provider: "{{ cli }}"

  - name: "Config DNS server IPv6 destination"
    ne_dns_server:
      state: present
      vrf_name: vpna
      sequence_num: 1
      address: 1::1
      config_type: ipv6-destination
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
    sample: {"vrf_name": "vpna", "address": "1.1.1.1", "config_type": "ipv4-source", state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"vrf_name": ["vpna"], "address": ["1.1.1.1"]}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"vrf_name": ["vpna"], "address": ["1.1.1.1"]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["dns server source-ip vpn-instance vpna  1.1.1.1"]
'''


SUCCESS = """success"""
FAILED = """failed"""

# get dns server ipv4  source info
NE_GET_DNS_SERVER_SOURCE_IPV4_HEADER = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsSrcIps>
          <dnsSrcIp>
"""
NE_GET_DNS_SERVER_SOURCE_IPV4_TAIL = """
          </dnsSrcIp>
        </dnsSrcIps>
      </dns>
    </filter>
"""

# merge dns server ipv4  source info
NE_MERGE_DNS_SERVER_SOURCE_IPV4_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsSrcIps>
          <dnsSrcIp xc:operation="merge">
"""
NE_MERGE_DNS_SERVER_SOURCE_IPV4_TAIL = """
          </dnsSrcIp>
        </dnsSrcIps>
      </dns>
    </config>
"""

# create dns server ipv4  source info
NE_CREATE_DNS_SERVER_SOURCE_IPV4_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsSrcIps>
          <dnsSrcIp xc:operation="create">
"""
NE_CREATE_DNS_SERVER_SOURCE_IPV4_TAIL = """
          </dnsSrcIp>
        </dnsSrcIps>
      </dns>
    </config>
"""

# delete dns server ipv4  source info
NE_DELETE_DNS_SERVER_SOURCE_IPV4_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsSrcIps>
          <dnsSrcIp xc:operation="delete">
"""
NE_DELETE_DNS_SERVER_SOURCE_IPV4_TAIL = """
          </dnsSrcIp>
        </dnsSrcIps>
      </dns>
    </config>
"""

# get dns server ipv6  source info
NE_GET_DNS_SERVER_SOURCE_IPV6_HEADER = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsSrcIpv6s>
          <dnsSrcIpv6>
"""
NE_GET_DNS_SERVER_SOURCE_IPV6_TAIL = """
          </dnsSrcIpv6>
        </dnsSrcIpv6s>
      </dns>
    </filter>
"""

# merge dns server ipv6  source info
NE_MERGE_DNS_SERVER_SOURCE_IPV6_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsSrcIpv6s>
          <dnsSrcIpv6 xc:operation="merge">
"""
NE_MERGE_DNS_SERVER_SOURCE_IPV6_TAIL = """
          </dnsSrcIpv6>
        </dnsSrcIpv6s>
      </dns>
    </config>
"""

# create dns server ipv6  source info
NE_CREATE_DNS_SERVER_SOURCE_IPV6_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsSrcIpv6s>
          <dnsSrcIpv6 xc:operation="create">
"""
NE_CREATE_DNS_SERVER_SOURCE_IPV6_TAIL = """
          </dnsSrcIpv6>
        </dnsSrcIpv6s>
      </dns>
    </config>
"""

# delete dns server ipv6  source info
NE_DELETE_DNS_SERVER_SOURCE_IPV6_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsSrcIpv6s>
          <dnsSrcIpv6 xc:operation="delete">
"""
NE_DELETE_DNS_SERVER_SOURCE_IPV6_TAIL = """
          </dnsSrcIpv6>
        </dnsSrcIpv6s>
      </dns>
    </config>
"""

# get dns domain info
NE_GET_DNS_DOMAIN_HEADER = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsDomains>
          <dnsDomain>
"""
NE_GET_DNS_DOMAIN_TAIL = """
          </dnsDomain>
        </dnsDomains>
      </dns>
    </filter>
"""

# merge dns domain info
NE_MERGE_DNS_DOMAIN_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsDomains>
          <dnsDomain xc:operation="merge">
"""
NE_MERGE_DNS_DOMAIN_TAIL = """
          </dnsDomain>
        </dnsDomains>
      </dns>
    </config>
"""

# create dns domain info
NE_CREATE_DNS_DOMAIN_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsDomains>
          <dnsDomain xc:operation="create">
"""
NE_CREATE_DNS_DOMAIN_TAIL = """
          </dnsDomain>
        </dnsDomains>
      </dns>
    </config>
"""

# delete dns domain info
NE_DELETE_DNS_DOMAIN_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsDomains>
          <dnsDomain xc:operation="delete">
"""
NE_DELETE_DNS_DOMAIN_TAIL = """
          </dnsDomain>
        </dnsDomains>
      </dns>
    </config>
"""

# get dns server ipv4 destination info
NE_GET_DNS_SERVER_IPV4_HEADER = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv4Servers>
          <dnsIpv4Server>
"""
NE_GET_DNS_SERVER_IPV4_TAIL = """
          </dnsIpv4Server>
        </dnsIpv4Servers>
      </dns>
    </filter>
"""

# merge dns server ipv4 destination info
NE_MERGE_DNS_SERVER_IPV4_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv4Servers>
          <dnsIpv4Server xc:operation="merge">
"""
NE_MERGE_DNS_SERVER_IPV4_TAIL = """
          </dnsIpv4Server>
        </dnsIpv4Servers>
      </dns>
    </config>
"""

# create dns server ipv4 destination info
NE_CREATE_DNS_SERVER_IPV4_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv4Servers>
          <dnsIpv4Server xc:operation="create">
"""
NE_CREATE_DNS_SERVER_IPV4_TAIL = """
          </dnsIpv4Server>
        </dnsIpv4Servers>
      </dns>
    </config>
"""

# delete dns server ipv4 destination info
NE_DELETE_DNS_SERVER_IPV4_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv4Servers>
          <dnsIpv4Server xc:operation="delete">
"""
NE_DELETE_DNS_SERVER_IPV4_TAIL = """
          </dnsIpv4Server>
        </dnsIpv4Servers>
      </dns>
    </config>
"""

# get dns server ipv6 destination info
NE_GET_DNS_SERVER_IPV6_HEADER = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv6Servers>
          <dnsIpv6Server>
"""
NE_GET_DNS_SERVER_IPV6_TAIL = """
          </dnsIpv6Server>
        </dnsIpv6Servers>
      </dns>
    </filter>
"""

# merge dns server ipv6 destination info
NE_MERGE_DNS_SERVER_IPV6_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv6Servers>
          <dnsIpv6Server xc:operation="merge">
"""
NE_MERGE_DNS_SERVER_IPV6_TAIL = """
          </dnsIpv6Server>
        </dnsIpv6Servers>
      </dns>
    </config>
"""

# create dns server ipv6 destination info
NE_CREATE_DNS_SERVER_IPV6_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv6Servers>
          <dnsIpv6Server xc:operation="create">
"""
NE_CREATE_DNS_SERVER_IPV6_TAIL = """
          </dnsIpv6Server>
        </dnsIpv6Servers>
      </dns>
    </config>
"""

# delete dns server ipv6 destination info
NE_DELETE_DNS_SERVER_IPV6_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsIpv6Servers>
          <dnsIpv6Server xc:operation="delete">
"""
NE_DELETE_DNS_SERVER_IPV6_TAIL = """
          </dnsIpv6Server>
        </dnsIpv6Servers>
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


def check_domain_name(self, domain):
    if len(domain) > 63 or len(domain.replace(' ', '')) < 1:
        return FAILED
    return SUCCESS


class DnsServer(object):
    """ Manages DNS configuration """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # dns server config info
        self.vrf_name = self.module.params['vrf_name']
        self.address = self.module.params['address']
        self.domain = self.module.params['domain']
        self.sequence_num = self.module.params['sequence_num']
        self.interface_name = self.module.params['interface_name']
        self.config_type = self.module.params['config_type']

        self.state = self.module.params['state']

        # dns global info
        self.dnsServer_info = dict()

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

    def check_dns_server_source_ipv4_args(self):
        """ check_dns_server_source_ipv4_args """

        need_cfg = False

        vrf_name = self.vrf_name
        address = self.address

        if not vrf_name:
            self.module.fail_json(
                msg='Error: The source IPv4 vpn instance name is valid.')

        if not address:
            self.module.fail_json(
                msg='Error: The source IPv4 address %s is invalid.')

        if vrf_name and address:
            if check_vrf_name(self, vrf_name) == FAILED:
                self.module.fail_json(
                    msg='Error: The source IPv4 vpn instance name is not in the range from 1 to 31.')

            if check_ipv4_address(self, address) == FAILED:
                self.module.fail_json(
                    msg='Error: The source IPv4 address %s is invalid.' % address)

            need_cfg = True

        return need_cfg

    def check_dns_server_source_ipv6_args(self):
        """ check_dns_server_source_ipv6_args """

        need_cfg = False

        vrf_name = self.vrf_name
        address = self.address

        if not vrf_name:
            self.module.fail_json(
                msg='Error: The source IPv6 vpn instance name is valid.')

        if not address:
            self.module.fail_json(
                msg='Error: The source IPv6 address %s is invalid.')

        if vrf_name and address:
            if check_vrf_name(self, vrf_name) == FAILED:
                self.module.fail_json(
                    msg='Error: The source IPv6 vpn instance name  is not in the range from 1 to 31.')

            if check_ipv6_address(self, address) == FAILED:
                self.module.fail_json(
                    msg='Error: The source IPv6 address %s is invalid.' % address)

            need_cfg = True

        return need_cfg

    def check_dns_domain_args(self):
        """ check_dns_domain_args """

        need_cfg = False

        vrf_name = self.vrf_name
        domain = self.domain

        if not vrf_name:
            self.module.fail_json(
                msg='Error: The domain vpn instance name is valid.')

        if not domain:
            self.module.fail_json(
                msg='Error: The domain name is valid.')

        if vrf_name and domain:
            if check_domain_name(self, domain) == FAILED:
                self.module.fail_json(
                    msg='Error: The domain name is not in the range from 1 to 63.')

            need_cfg = True

        return need_cfg

    def check_dns_server_ipv4_args(self):
        """ check_dns_server_ipv4_args """

        need_cfg = False

        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address
        if not vrf_name:
            self.module.fail_json(
                msg='Error: The server IPv4 vpn instance name is invalid.')

        if not sequence_num:
            self.module.fail_json(
                msg='Error: The server sequence num is invalid.')

        if not address:
            self.module.fail_json(
                msg='Error: The server IPv4 address is invalid.')

        if vrf_name and sequence_num and address:
            if check_vrf_name(self, vrf_name) == FAILED:
                self.module.fail_json(
                    msg='Error: The server IPv4 vpn instance name  is not in the range from 1 to 31.')

            if check_ipv4_address(self, address) == FAILED:
                self.module.fail_json(
                    msg='Error: The server IPv4 address %s is invalid.' % address)

            need_cfg = True

        return need_cfg

    def check_dns_server_ipv6_args(self):
        """ check_dns_server_ipv6_args """

        need_cfg = False
        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address

        if not vrf_name:
            self.module.fail_json(
                msg='Error: The server IPv6 vpn instance name is invalid.')

        if not sequence_num:
            self.module.fail_json(
                msg='Error: The server sequence num is invalid.')

        if not address:
            self.module.fail_json(
                msg='Error: The server IPv6 address is invalid.')

        if vrf_name and sequence_num and address:
            if check_vrf_name(self, vrf_name) == FAILED:
                self.module.fail_json(
                    msg='Error: The server IPv6 vpn instance name  is not in the range from 1 to 31.')

            if check_ipv6_address(self, address) == FAILED:
                self.module.fail_json(
                    msg='Error: The server IPv6 address %s is invalid.' % address)

            need_cfg = True

        return need_cfg

    def get_dns_server_source_ipv4(self):
        """ get_dns_server_source_ipv4 """

        conf_str = NE_GET_DNS_SERVER_SOURCE_IPV4_HEADER

        vrf_name = self.vrf_name
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if address:
            conf_str += "<sourceIpv4Addr>%s</sourceIpv4Addr>" % address

        conf_str += NE_GET_DNS_SERVER_SOURCE_IPV4_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<vrfName>(.*)</vrfName>.*\s*<sourceIpv4Addr>(.*)</sourceIpv4Addr>.*\s*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_dns_server_source_ipv4(self):
        """ merge_dns_server_source_ipv4 """

        conf_str = NE_MERGE_DNS_SERVER_SOURCE_IPV4_HEADER

        vrf_name = self.vrf_name
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if address:
            conf_str += "<sourceIpv4Addr>%s</sourceIpv4Addr>" % address

        conf_str += NE_MERGE_DNS_SERVER_SOURCE_IPV4_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Merge dns server IPv4 source failed.')

        cmds = []
        if vrf_name and address:
            cmd = "dns server source-ip vpn-instance %s %s" % (
                vrf_name, address)

        cmds.append(cmd)

        return cmds

    def create_dns_server_source_ipv4(self):
        """ create_dns_server_source_ipv4 """

        conf_str = NE_CREATE_DNS_SERVER_SOURCE_IPV4_HEADER

        vrf_name = self.vrf_name
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if address:
            conf_str += "<sourceIpv4Addr>%s</sourceIpv4Addr>" % address

        conf_str += NE_CREATE_DNS_SERVER_SOURCE_IPV4_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Create dns server IPv4 source failed.')

        cmds = []
        if vrf_name and address:
            cmd = "dns server source-ip vpn-instance %s %s" % (
                vrf_name, address)

        cmds.append(cmd)

        return cmds

    def delete_dns_server_source_ipv4(self):
        """ delete_dns_server_source_ipv4 """

        conf_str = NE_DELETE_DNS_SERVER_SOURCE_IPV4_HEADER

        vrf_name = self.vrf_name
        address = self.address
        if vrf_name and address:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name
            conf_str += "<sourceIpv4Addr>%s</sourceIpv4Addr>" % address

        conf_str += NE_DELETE_DNS_SERVER_SOURCE_IPV4_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Delete dns server IPv4 source failed.')

        cmds = []
        cmd = "undo dns server source-ip vpn-instance %s %s" % (
            vrf_name, address)
        cmds.append(cmd)

        return cmds

    def get_dns_server_source_ipv6(self):
        """ get_dns_server_source_ipv6 """

        conf_str = NE_GET_DNS_SERVER_SOURCE_IPV6_HEADER

        vrf_name = self.vrf_name
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if address:
            conf_str += "<sourceIpv6Addr>%s</sourceIpv6Addr>" % address

        conf_str += NE_GET_DNS_SERVER_SOURCE_IPV6_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<vrfName>(.*)</vrfName>.*\s*<sourceIpv6Addr>(.*)</sourceIpv6Addr>.*\s*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_dns_server_source_ipv6(self):
        """ merge_dns_server_source_ipv6 """

        conf_str = NE_MERGE_DNS_SERVER_SOURCE_IPV6_HEADER

        vrf_name = self.vrf_name
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if address:
            conf_str += "<sourceIpv6Addr>%s</sourceIpv6Addr>" % address

        conf_str += NE_MERGE_DNS_SERVER_SOURCE_IPV6_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Merge dns server IPv6 source failed.')

        cmds = []
        if vrf_name and address:
            cmd = "dns server ipv6 source-ip vpn-instance %s %s" % (
                vrf_name, address)

        cmds.append(cmd)

        return cmds

    def create_dns_server_source_ipv6(self):
        """ create_dns_server_source_ipv4 """

        conf_str = NE_CREATE_DNS_SERVER_SOURCE_IPV6_HEADER

        vrf_name = self.vrf_name
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if address:
            conf_str += "<sourceIpv6Addr>%s</sourceIpv6Addr>" % address

        conf_str += NE_CREATE_DNS_SERVER_SOURCE_IPV6_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Create dns server IPv6 source failed.')

        cmds = []
        if vrf_name and address:
            cmd = "dns server ipv6 source-ip vpn-instance %s %s" % (
                vrf_name, address)

        cmds.append(cmd)

        return cmds

    def delete_dns_server_source_ipv6(self):
        """ delete_dns_server_source_ipv6 """

        conf_str = NE_DELETE_DNS_SERVER_SOURCE_IPV6_HEADER

        vrf_name = self.vrf_name
        address = self.address
        if vrf_name and address:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name
            conf_str += "<sourceIpv6Addr>%s</sourceIpv6Addr>" % address

        conf_str += NE_DELETE_DNS_SERVER_SOURCE_IPV6_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(
                msg='Error: Delete dns server IPv6 source failed.')

        cmds = []
        cmd = "undo dns server ipv6 source-ip vpn-instance %s %s" % (
            vrf_name, address)
        cmds.append(cmd)

        return cmds

    def get_dns_server_domain(self):
        """ get_dns_server_domain """

        conf_str = NE_GET_DNS_DOMAIN_HEADER

        vrf_name = self.vrf_name
        domain = self.domain
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if domain:
            conf_str += "<domain>%s</domain>" % domain

        conf_str += NE_GET_DNS_DOMAIN_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<vrfName>(.*)</vrfName>.*\s*<domain>(.*)</domain>.*\s*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_dns_server_domain(self):
        """ merge_dns_server_domain """

        conf_str = NE_MERGE_DNS_DOMAIN_HEADER

        vrf_name = self.vrf_name
        domain = self.domain
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if domain:
            conf_str += "<domain>%s</domain>" % domain

        conf_str += NE_MERGE_DNS_DOMAIN_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge dns domain failed.')

        cmds = []
        if vrf_name and domain:
            cmd = "dns domain %s vpn-instance %s" % (domain, vrf_name)

        cmds.append(cmd)

        return cmds

    def create_dns_server_domain(self):
        """ create_dns_server_domain """

        conf_str = NE_CREATE_DNS_DOMAIN_HEADER

        vrf_name = self.vrf_name
        domain = self.domain
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if domain:
            conf_str += "<domain>%s</domain>" % domain

        conf_str += NE_CREATE_DNS_DOMAIN_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Create dns domain failed.')

        cmds = []
        if vrf_name and domain:
            cmd = "dns domain %s vpn-instance %s" % (domain, vrf_name)

        cmds.append(cmd)

        return cmds

    def delete_dns_server_domain(self):
        """ delete_dns_server_domain """

        conf_str = NE_DELETE_DNS_DOMAIN_HEADER

        vrf_name = self.vrf_name
        domain = self.domain
        if vrf_name and domain:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name
            conf_str += "<domain>%s</domain>" % domain

        conf_str += NE_DELETE_DNS_DOMAIN_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete dns domain failed.')

        cmds = []
        cmd = "undo dns domain %s vpn-instance %s" % (domain, vrf_name)
        cmds.append(cmd)

        return cmds

    def get_dns_server_ipv4(self):
        """ get_dns_server_ipv4 """

        conf_str = NE_GET_DNS_SERVER_IPV4_HEADER

        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if sequence_num:
            conf_str += "<seqNo>%s</seqNo>" % sequence_num

        if address:
            conf_str += "<ipv4Addr>%s</ipv4Addr>" % address

        conf_str += NE_GET_DNS_SERVER_IPV4_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<vrfName>(.*)</vrfName>.*\s*<seqNo>(.*)</seqNo>.*\s*<ipv4Addr>(.*)</ipv4Addr>.*\s*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_dns_server_ipv4(self):
        """ merge_dns_server_ipv4 """

        conf_str = NE_MERGE_DNS_SERVER_IPV4_HEADER

        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if sequence_num:
            conf_str += "<seqNo>%s</seqNo>" % sequence_num

        if address:
            conf_str += "<ipv4Addr>%s</ipv4Addr>" % address

        conf_str += NE_MERGE_DNS_SERVER_IPV4_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge dns IPv4 server failed.')

        cmds = []
        if vrf_name and address:
            cmd = "dns server %s vpn-instance %s" % (address, vrf_name)

        cmds.append(cmd)

        return cmds

    def create_dns_server_ipv4(self):
        """ create_dns_server_ipv4 """

        conf_str = NE_CREATE_DNS_SERVER_IPV4_HEADER

        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if sequence_num:
            conf_str += "<seqNo>%s</seqNo>" % sequence_num

        if address:
            conf_str += "<ipv4Addr>%s</ipv4Addr>" % address

        conf_str += NE_CREATE_DNS_SERVER_IPV4_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Create dns IPv4 server failed.')

        cmds = []
        if vrf_name and address:
            cmd = "dns server %s vpn-instance %s" % (address, vrf_name)

        cmds.append(cmd)

        return cmds

    def delete_dns_server_ipv4(self):
        """ delete_dns_server_ipv4 """

        conf_str = NE_DELETE_DNS_SERVER_IPV4_HEADER

        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address
        if vrf_name and sequence_num and address:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name
            conf_str += "<seqNo>%s</seqNo>" % sequence_num
            conf_str += "<ipv4Addr>%s</ipv4Addr>" % address

        conf_str += NE_DELETE_DNS_SERVER_IPV4_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete dns IPv4 server failed.')

        cmds = []
        cmd = "undo dns server %s vpn-instance %s" % (address, vrf_name)
        cmds.append(cmd)

        return cmds

    def get_dns_server_ipv6(self):
        """ get_dns_server_ipv4 """

        conf_str = NE_GET_DNS_SERVER_IPV6_HEADER
        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if sequence_num:
            conf_str += "<seqNo>%s</seqNo>" % sequence_num

        if address:
            conf_str += "<ipv6Addr>%s</ipv6Addr>" % address

        conf_str += "<ifName></ifName>"
        conf_str += NE_GET_DNS_SERVER_IPV6_TAIL

        xml_str = get_nc_config(self.module, conf_str)
        result = dict()

        if "<data/>" in xml_str:
            return result

        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-dns"', "")

        root = ElementTree.fromstring(xml_str)
        server_inst = root.find("dns/dnsIpv6Servers/dnsIpv6Server")

        # if server_inst is not None:
        if len(server_inst) != 0:
            for inst in server_inst:
                if inst.tag in ["vrfName",
                                "seqNo",
                                "ipv6Addr",
                                "ifName"]:
                    result[inst.tag] = inst.text

        return result

    def merge_dns_server_ipv6(self):
        """ merge_dns_server_ipv6 """

        conf_str = NE_MERGE_DNS_SERVER_IPV6_HEADER

        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address
        interface_name = self.interface_name
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if sequence_num:
            conf_str += "<seqNo>%s</seqNo>" % sequence_num

        if address:
            conf_str += "<ipv6Addr>%s</ipv6Addr>" % address

        if interface_name:
            conf_str += "<ifName>%s</ifName>" % interface_name

        conf_str += NE_MERGE_DNS_SERVER_IPV6_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge dns IPv6 server failed.')

        cmds = []
        cmd = "dns server ipv6 %s " % address

        if interface_name:
            cmd += "%s " % interface_name

        cmd += "vpn-instance %s " % vrf_name

        cmds.append(cmd)

        return cmds

    def create_dns_server_ipv6(self):
        """ create_dns_server_ipv4 """

        conf_str = NE_CREATE_DNS_SERVER_IPV6_HEADER

        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address
        interface_name = self.interface_name
        if vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name

        if sequence_num:
            conf_str += "<seqNo>%s</seqNo>" % sequence_num

        if address:
            conf_str += "<ipv6Addr>%s</ipv6Addr>" % address

        if interface_name:
            conf_str += "<ifName>%s</ifName>" % interface_name

        conf_str += NE_CREATE_DNS_SERVER_IPV6_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Create dns IPv6 server failed.')

        cmds = []
        if vrf_name and address:
            cmd = "dns server ipv6 %s vpn-instance %s" % (address, vrf_name)

        cmds.append(cmd)

        return cmds

    def delete_dns_server_ipv6(self):
        """ delete_dns_server_domain """

        conf_str = NE_DELETE_DNS_SERVER_IPV6_HEADER

        vrf_name = self.vrf_name
        sequence_num = self.sequence_num
        address = self.address
        if vrf_name and sequence_num and address:
            conf_str += "<vrfName>%s</vrfName>" % vrf_name
            conf_str += "<seqNo>%s</seqNo>" % sequence_num
            conf_str += "<ipv6Addr>%s</ipv6Addr>" % address

        conf_str += NE_DELETE_DNS_SERVER_IPV6_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete dns IPv6 server failed.')

        cmds = []
        cmd = "undo dns server ipv6 %s vpn-instance %s" % (address, vrf_name)
        cmds.append(cmd)

        return cmds

    def work(self):
        """worker"""

        if self.vrf_name:
            self.proposed["vrf_name"] = self.vrf_name

        if self.address:
            self.proposed["address"] = self.address

        if self.domain:
            self.proposed["domain"] = self.domain

        if self.sequence_num:
            self.proposed["sequence_num"] = self.sequence_num

        if self.interface_name:
            self.proposed["interface_name"] = self.interface_name

        if self.config_type:
            self.proposed["config_type"] = self.config_type

        config_dns_server_source_ipv4 = False
        config_dns_server_source_ipv6 = False
        config_dns_domain = False
        config_dns_server_ipv4 = False
        config_dns_server_ipv6 = False

        if self.config_type == "ipv4-source":
            config_dns_server_source_ipv4 = self.check_dns_server_source_ipv4_args()

        if self.config_type == "ipv6-source":
            config_dns_server_source_ipv6 = self.check_dns_server_source_ipv6_args()

        if self.config_type == "domain":
            config_dns_domain = self.check_dns_domain_args()

        if self.config_type == "ipv4-destination":
            config_dns_server_ipv4 = self.check_dns_server_ipv4_args()

        if self.config_type == "ipv6-destination":
            config_dns_server_ipv6 = self.check_dns_server_ipv6_args()

        # proc dns server ipv4 source config
        if config_dns_server_source_ipv4:
            dns_server_source_ipv4_exist = self.get_dns_server_source_ipv4()
            if len(dns_server_source_ipv4_exist) > 0:
                self.existing["vrf_name"] = dns_server_source_ipv4_exist[0][0]
                self.existing["address"] = dns_server_source_ipv4_exist[0][1]

            if self.state == "present":
                if len(dns_server_source_ipv4_exist) > 0:
                    cmd = self.merge_dns_server_source_ipv4()
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    cmd = self.create_dns_server_source_ipv4()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)

            elif self.state == "absent":
                if len(dns_server_source_ipv4_exist) > 0:
                    cmd = self.delete_dns_server_source_ipv4()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    self.module.fail_json(
                        msg='Error: Dns server IPv4 source does not exist.')

            elif self.state == "query":
                pass

            dns_dns_server_source_ipv4_state = self.get_dns_server_source_ipv4()
            if len(dns_dns_server_source_ipv4_state) > 0:
                self.end_state["vrf_name"] = dns_dns_server_source_ipv4_state[0][0]
                self.end_state["address"] = dns_dns_server_source_ipv4_state[0][1]

        # proc dns server ipv6 source config
        if config_dns_server_source_ipv6:
            dns_server_source_ipv6_exist = self.get_dns_server_source_ipv6()
            if len(dns_server_source_ipv6_exist) > 0:
                self.existing["vrf_name"] = dns_server_source_ipv6_exist[0][0]
                self.existing["address"] = dns_server_source_ipv6_exist[0][1]

            if self.state == "present":
                if len(dns_server_source_ipv6_exist) > 0:
                    cmd = self.merge_dns_server_source_ipv6()
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    cmd = self.create_dns_server_source_ipv6()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)

            elif self.state == "absent":
                if len(dns_server_source_ipv6_exist) > 0:
                    cmd = self.delete_dns_server_source_ipv6()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    self.module.fail_json(
                        msg='Error: Dns server IPv6 source does not exist.')

            elif self.state == "query":
                pass

            dns_server_source_ipv6_state = self.get_dns_server_source_ipv6()
            if len(dns_server_source_ipv6_state) > 0:
                self.end_state["vrf_name"] = dns_server_source_ipv6_state[0][0]
                self.end_state["address"] = dns_server_source_ipv6_state[0][1]

        # proc dns domain config
        if config_dns_domain:
            dns_domain_exist = self.get_dns_server_domain()
            if len(dns_domain_exist) > 0:
                self.existing["vrf_name"] = dns_domain_exist[0][0]
                self.existing["domain"] = dns_domain_exist[0][1]

            if self.state == "present":
                if len(dns_domain_exist) > 0:
                    cmd = self.merge_dns_server_domain()
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    cmd = self.create_dns_server_domain()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)

            elif self.state == "absent":
                if len(dns_domain_exist) > 0:
                    cmd = self.delete_dns_server_domain()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    self.module.fail_json(
                        msg='Error: Dns domain does not exist.')

            elif self.state == "query":
                pass

            dns_domain_state = self.get_dns_server_domain()
            if len(dns_domain_state) > 0:
                self.end_state["vrf_name"] = dns_domain_state[0][0]
                self.end_state["domain"] = dns_domain_state[0][1]

        # proc dns ipv4 server config
        if config_dns_server_ipv4:
            dns_server_ipv4_exist = self.get_dns_server_ipv4()
            if len(dns_server_ipv4_exist) > 0:
                self.existing["vrf_name"] = dns_server_ipv4_exist[0][0]
                self.existing["sequence_num"] = dns_server_ipv4_exist[0][1]
                self.existing["address"] = dns_server_ipv4_exist[0][2]

            if self.state == "present":
                if len(dns_server_ipv4_exist) > 0:
                    cmd = self.merge_dns_server_ipv4()
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    cmd = self.create_dns_server_ipv4()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)

            elif self.state == "absent":
                if len(dns_server_ipv4_exist) > 0:
                    cmd = self.delete_dns_server_ipv4()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    self.module.fail_json(
                        msg='Error: Dns IPv4 server does not exist.')

            elif self.state == "query":
                pass

            dns_server_ipv4_state = self.get_dns_server_ipv4()
            if len(dns_server_ipv4_state) > 0:
                self.end_state["vrf_name"] = dns_server_ipv4_state[0][0]
                self.end_state["sequence_num"] = dns_server_ipv4_state[0][1]
                self.end_state["address"] = dns_server_ipv4_state[0][2]

        # proc dns ipv6 server config
        if config_dns_server_ipv6:
            dns_server_ipv6_exist = self.get_dns_server_ipv6()
            if len(dns_server_ipv6_exist) > 0:
                self.existing = copy.deepcopy(dns_server_ipv6_exist)

            if self.state == "present":
                if len(dns_server_ipv6_exist) > 0:
                    cmd = self.merge_dns_server_ipv6()
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    cmd = self.create_dns_server_ipv6()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)

            elif self.state == "absent":
                if len(dns_server_ipv6_exist) > 0:
                    cmd = self.delete_dns_server_ipv6()
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)
                else:
                    self.module.fail_json(
                        msg='Error: Dns IPv6 server does not exist.')

            elif self.state == "query":
                pass

            dns_server_ipv6_state = self.get_dns_server_ipv6()
            if len(dns_server_ipv6_state) > 0:
                self.end_state = copy.deepcopy(dns_server_ipv6_state)

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
        vrf_name=dict(required=False, type='str'),
        address=dict(required=False, type='str'),
        domain=dict(required=False, type='str'),
        sequence_num=dict(required=False, type='str'),
        interface_name=dict(required=False, type='str'),
        config_type=dict(required=True,
                         choices=['ipv4-source', 'ipv6-source', 'domain', 'ipv4-destination', 'ipv6-destination']),

        # 在此增加其他支持参数
        state=dict(
            required=False, default='present',
            choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = DnsServer(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
