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
module: ne_dns_global
version_added: "2.6"
short_description: Manages DNS global configuration on HUAWEI netengine switches.
description:
    - Manages DNS global configurations on HUAWEI netengine switches.
author:
    - Lee (@netengine-Ansible)
options:
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent','query']
    dns_enable:
        description:
            - Dns enable flag.
        required: false
        default: false
        choices: ['true','false']
    interval_time:
        description:
            - The amount of time to wait for a response to a DNS query.
              The value is an integer ranging from 1 to 10.
        required: false
        default: null
    try_number:
        description:
            - Specifies the number of times to retry sending DNS queries.
              The value is an integer ranging from 1 to 3.
        required: false
        default: null
    config_type:
        description:
            - Type of DNS configuration.
        required: true
        default: all
        choices: ['dns_enable', 'interval_time', 'try_number']
'''

EXAMPLES = '''

- name: ne_test DNS test
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

  - name: "Enable DNS"
    ne_dns_global:
      state: present
      dns_enable: true
      config_type: dns_enable
      provider: "{{ cli }}"

  - name: "Disable DNS"
    ne_dns_global:
      state: absent
      dns_enable: false
      config_type: dns_enable
      provider: "{{ cli }}"

  - name: "Config DNS timeout"
    ne_dns_global:
      state: present
      interval_time: 3
      config_type: interval_time
      provider: "{{ cli }}"

  - name: "Config DNS try number"
    ne_dns_global:
      state: present
      try_number: 1
      config_type: interval_time
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
    sample: {"dns_enable": "false", "config_type": "dns_enable", state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"dns_enable": ["true"]}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"dns_enable": ["true"]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["dns resolve"]
'''


# get dns enable
NE_GET_DNS_ENABLE = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsGlobalCfgs>
          <dnsGlobalCfg>
            <dnsEnable></dnsEnable>
          </dnsGlobalCfg>
        </dnsGlobalCfgs>
      </dns>
    </filter>
"""

# get dns timeout
NE_GET_DNS_TIMEOUT = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsTimeouts>
          <dnsTimeout>
            <intervalTime></intervalTime>
          </dnsTimeout>
        </dnsTimeouts>
      </dns>
    </filter>
"""

# get dns try number
NE_GET_DNS_TRYNUMBER = """
    <filter type="subtree">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsTryNumbers>
          <dnsTryNumber>
            <tryNumber></tryNumber>
          </dnsTryNumber>
        </dnsTryNumbers>
      </dns>
    </filter>
"""

# merge dns enable
NE_MERGE_DNS_ENABLE_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsGlobalCfgs>
          <dnsGlobalCfg xc:operation="merge">
"""
NE_MERGE_DNS_ENABLE_TAIL = """
          </dnsGlobalCfg>
        </dnsGlobalCfgs>
      </dns>
    </config>
"""

# merge dns timeout
NE_MERGE_DNS_TIMEOUT_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsTimeouts>
          <dnsTimeout xc:operation="merge">
"""
NE_MERGE_DNS_TIMEOUT_TAIL = """
          </dnsTimeout>
        </dnsTimeouts>
      </dns>
    </config>
"""

# merge dns try number
NE_MERGE_DNS_TRYNUMBER_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsTryNumbers>
          <dnsTryNumber xc:operation="merge">
"""
NE_MERGE_DNS_TRYNUMBER_TAIL = """
          </dnsTryNumber>
        </dnsTryNumbers>
      </dns>
    </config>
"""

# create dns enable
NE_CREATE_DNS_ENABLE_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsGlobalCfgs>
          <dnsGlobalCfg xc:operation="create">
"""
NE_CREATE_DNS_ENABLE_TAIL = """
          </dnsGlobalCfg>
        </dnsGlobalCfgs>
      </dns>
    </config>
"""

# create dns timeout
NE_CREATE_DNS_TIMEOUT_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsTimeouts>
          <dnsTimeout xc:operation="create">
"""
NE_CREATE_DNS_TIMEOUT_TAIL = """
          </dnsTimeout>
        </dnsTimeouts>
      </dns>
    </config>
"""

# create dns try number
NE_CREATE_DNS_TRYNUMBER_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsTryNumbers>
          <dnsTryNumber xc:operation="create">
"""
NE_CREATE_DNS_TRYNUMBER_TAIL = """
          </dnsTryNumber>
        </dnsTryNumbers>
      </dns>
    </config>
"""


# delete dns enable
NE_DELETE_DNS_ENABLE_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsGlobalCfgs>
          <dnsGlobalCfg xc:operation="delete">
"""
NE_DELETE_DNS_ENABLE_TAIL = """
          </dnsGlobalCfg>
        </dnsGlobalCfgs>
      </dns>
    </config>
"""

# delete dns timeout
NE_DELETE_DNS_TIMEOUT_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsTimeouts>
          <dnsTimeout xc:operation="delete">
"""
NE_DELETE_DNS_TIMEOUT_TAIL = """
          </dnsTimeout>
        </dnsTimeouts>
      </dns>
    </config>
"""

# delete dns try number
NE_DELETE_DNS_TRYNUMBER_HEADER = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <dns xmlns="http://www.huawei.com/netconf/vrp/huawei-dns">
        <dnsTryNumbers>
          <dnsTryNumber xc:operation="delete">
"""
NE_DELETE_DNS_TRYNUMBER_TAIL = """
          </dnsTryNumber>
        </dnsTryNumbers>
      </dns>
    </config>
"""


class DnsGlobal(object):
    """ Manages DNS configuration """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # dns global config info
        self.dns_enable = self.module.params['dns_enable']
        self.interval_time = self.module.params['interval_time']
        self.try_number = self.module.params['try_number']
        self.state = self.module.params['state']
        self.config_type = self.module.params['config_type']

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

    def check_dns_enable_args(self):
        """ check_dns_enable_args """

        need_cfg = False

        dns_enable = self.dns_enable
        if dns_enable:
            need_cfg = True

        if self.state == "absent":
            need_cfg = True

        return need_cfg

    def check_dns_interval_time_args(self):
        """ check_dns_interval_time_args """

        need_cfg = False

        interval_time = self.interval_time
        if interval_time:
            if int(interval_time) > 10 or int(interval_time) < 1:
                self.module.fail_json(
                    msg='The value of interval_time (%s) is out of [1 - 10].' % interval_time)

            need_cfg = True

        if self.state == "absent":
            need_cfg = True

        return need_cfg

    def check_dns_try_number_args(self):
        """ check_dns_try_number_args """

        need_cfg = False

        try_number = self.try_number
        if try_number:
            if int(try_number) > 3 or int(try_number) < 1:
                self.module.fail_json(
                    msg='The value of try_number (%s) is out of [1 - 3].' % try_number)

            need_cfg = True

        if self.state == "absent":
            need_cfg = True

        return need_cfg

    def get_dns_enable(self):
        """ get_dns_enable """

        conf_str = NE_GET_DNS_ENABLE

        xml_str = get_nc_config(self.module, conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<dnsEnable>(.*)</dnsEnable>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_dns_enable(self):
        """ merge_dns_enable """

        conf_str = NE_MERGE_DNS_ENABLE_HEADER

        dns_enable = self.dns_enable
        if dns_enable:
            conf_str += "<dnsEnable>%s</dnsEnable>" % dns_enable

        conf_str += NE_MERGE_DNS_ENABLE_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge dns resolve failed.')

        cmds = []
        if dns_enable == "true":
            cmd = "dns resolve"
        else:
            cmd = "undo dns resolve"
        cmds.append(cmd)

        return cmds

    def delete_dns_enable(self):
        """ delete_dns_enable """

        conf_str = NE_DELETE_DNS_ENABLE_HEADER

        dns_enable = self.dns_enable
        if dns_enable:
            conf_str += "<dnsEnable>%s</dnsEnable>" % dns_enable

        conf_str += NE_DELETE_DNS_ENABLE_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete dns resolve failed.')

        cmds = []
        cmd = "undo dns resolve"
        cmds.append(cmd)

        return cmds

    def get_dns_timeout(self):
        """ get_dns_timeout """

        conf_str = NE_GET_DNS_TIMEOUT

        xml_str = get_nc_config(self.module, conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<intervalTime>(.*)</intervalTime>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_dns_timeout(self):
        """ merge_dns_timeout """

        conf_str = NE_MERGE_DNS_TIMEOUT_HEADER

        interval_time = self.interval_time
        if interval_time:
            conf_str += "<intervalTime>%s</intervalTime>" % interval_time

        conf_str += NE_MERGE_DNS_TIMEOUT_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge dns timeout failed.')

        cmds = []
        if interval_time:
            cmd = "dns timeout %s" % interval_time

        cmds.append(cmd)

        return cmds

    def delete_dns_timeout(self):
        """ delete_dns_timeout """

        conf_str = NE_DELETE_DNS_TIMEOUT_HEADER

        interval_time = self.interval_time
        if interval_time:
            conf_str += "<intervalTime>%s</intervalTime>" % interval_time

        conf_str += NE_DELETE_DNS_TIMEOUT_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete dns timeout failed.')

        cmds = []
        cmd = "undo dns timeout %s" % interval_time
        cmds.append(cmd)

        return cmds

    def get_dns_try_number(self):
        """ get_dns_try_number """

        conf_str = NE_GET_DNS_TRYNUMBER

        xml_str = get_nc_config(self.module, conf_str)
        result = list()

        if "<data/>" in xml_str:
            return result
        else:
            re_find = re.findall(
                r'.*<tryNumber>(.*)</tryNumber>.*', xml_str)

            if re_find:
                return re_find
            else:
                return result

    def merge_dns_try_number(self):
        """ merge_dns_try_number """

        conf_str = NE_MERGE_DNS_TRYNUMBER_HEADER

        try_number = self.try_number
        if try_number:
            conf_str += "<tryNumber>%s</tryNumber>" % try_number

        conf_str += NE_MERGE_DNS_TRYNUMBER_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge dns try number failed.')

        cmds = []
        if try_number:
            cmd = "dns try %s" % try_number

        cmds.append(cmd)

        return cmds

    def delete_dns_try_number(self):
        """ delete_dns_trynumber """

        conf_str = NE_DELETE_DNS_TRYNUMBER_HEADER

        try_number = self.try_number
        if try_number:
            conf_str += "<tryNumber>%s</tryNumber>" % try_number

        conf_str += NE_DELETE_DNS_TRYNUMBER_TAIL

        recv_xml = set_nc_config(self.module, conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete dns try number failed.')

        cmds = []
        cmd = "undo dns try %s" % try_number
        cmds.append(cmd)

        return cmds

    def work(self):
        """worker"""

        if self.dns_enable:
            self.proposed["dns_enable"] = self.dns_enable

        if self.interval_time:
            self.proposed["interval_time"] = self.interval_time

        if self.try_number:
            self.proposed["try_number"] = self.try_number

        if self.config_type and self.state == "query":
            self.proposed["config_type"] = self.config_type

        config_dns_enable = False
        config_dns_timeout = False
        config_dns_try = False
        if self.config_type == "dns_enable":
            config_dns_enable = self.check_dns_enable_args()

        if self.config_type == "interval_time":
            config_dns_timeout = self.check_dns_interval_time_args()

        if self.config_type == "try_number":
            config_dns_try = self.check_dns_try_number_args()

        # proc dns global config
        if config_dns_enable:
            dns_enable_exist = self.get_dns_enable()

            if self.state == "present":
                if len(dns_enable_exist) > 0:
                    self.existing["dns_enable"] = dns_enable_exist[0]

                if len(dns_enable_exist) > 0:
                    if self.dns_enable != dns_enable_exist[0]:
                        cmd = self.merge_dns_enable()
                        self.changed = True
                        for item in cmd:
                            self.updates_cmd.append(item)

                dns_enable_state = self.get_dns_enable()
                if len(dns_enable_state) > 0:
                    self.end_state["dns_enable"] = dns_enable_state[0]
            elif self.state == "absent":
                if len(dns_enable_exist) > 0:
                    self.existing["dns_enable"] = dns_enable_exist[0]

                cmd = self.delete_dns_enable()
                if self.existing["dns_enable"] == "true":
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)

                dns_enable_state = self.get_dns_enable()
                if len(dns_enable_state) > 0:
                    self.end_state["dns_enable"] = dns_enable_state[0]
            elif self.state == "query":
                pass

        # proc dns timeout
        if config_dns_timeout:
            dns_timeout_exist = self.get_dns_timeout()

            if self.state == "present":
                if len(dns_timeout_exist) > 0:
                    self.existing["interval_time"] = dns_timeout_exist[0]
                    if self.interval_time != dns_timeout_exist[0]:
                        cmd = self.merge_dns_timeout()
                        self.changed = True
                        for item in cmd:
                            self.updates_cmd.append(item)

                dns_timeout_state = self.get_dns_timeout()
                if len(dns_timeout_state) > 0:
                    self.end_state["interval_time"] = dns_timeout_state[0]

            elif self.state == "absent":
                if len(dns_timeout_exist) > 0:
                    self.existing["interval_time"] = dns_timeout_exist[0]

                cmd = self.delete_dns_timeout()

                dns_timeout_state = self.get_dns_timeout()
                if len(dns_timeout_state) > 0:
                    self.end_state["interval_time"] = dns_timeout_state[0]

                if self.existing["interval_time"] != 5:
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)
            elif self.state == "query":
                pass

        # proc dns try number
        if config_dns_try:
            dns_try_number_exist = self.get_dns_try_number()
            if self.state == "present":
                if len(dns_try_number_exist) > 0:
                    self.existing["try_number"] = dns_try_number_exist[0]

                if len(dns_try_number_exist) > 0:
                    if self.try_number != dns_try_number_exist[0]:
                        cmd = self.merge_dns_try_number()
                        self.changed = True
                        for item in cmd:
                            self.updates_cmd.append(item)

                dns_try_number_state = self.get_dns_try_number()
                if len(dns_try_number_state) > 0:
                    self.end_state["try_number"] = dns_try_number_state[0]
            elif self.state == "absent":
                if len(dns_try_number_exist) > 0:
                    self.existing["try_number"] = dns_try_number_exist[0]

                cmd = self.delete_dns_try_number()

                dns_try_number_state = self.get_dns_try_number()
                if len(dns_try_number_state) > 0:
                    self.end_state["try_number"] = dns_try_number_state[0]

                if self.existing["try_number"] != 2:
                    self.changed = True
                    for item in cmd:
                        self.updates_cmd.append(item)
            elif self.state == "query":
                pass

        # query dns config
        if self.state == "query":
            dns_enable_exist = self.get_dns_enable()
            dns_timeout_exist = self.get_dns_timeout()
            dns_try_number_exist = self.get_dns_try_number()
            if self.config_type == "dns_enable":
                if len(dns_enable_exist) > 0:
                    self.existing["dns_enable"] = dns_enable_exist[0]
                    self.end_state["dns_enable"] = dns_enable_exist[0]
                else:
                    self.module.fail_json(
                        msg='Error: Dns resolve config does not exist')
            elif self.config_type == "interval_time":
                if len(dns_timeout_exist) > 0:
                    self.existing["interval_time"] = dns_timeout_exist[0]
                    self.end_state["interval_time"] = dns_timeout_exist[0]
                else:
                    self.module.fail_json(
                        msg='Error: Dns timeout config does not exist')
            elif self.config_type == "try_number":
                if len(dns_try_number_exist) > 0:
                    self.existing["try_number"] = dns_try_number_exist[0]
                    self.end_state["try_number"] = dns_try_number_exist[0]

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
        dns_enable=dict(required=False, choices=['true', 'false']),
        interval_time=dict(required=False, type='str'),
        try_number=dict(required=False, type='str'),
        config_type=dict(
            required=True,
            choices=[
                'dns_enable',
                'interval_time',
                'try_number']),

        # 在此增加其他支持参数
        state=dict(
            required=False, default='present',
            choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = DnsGlobal(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
