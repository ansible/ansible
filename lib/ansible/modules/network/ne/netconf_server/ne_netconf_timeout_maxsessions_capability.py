#!/usr/bin/python
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
# GNU General Public License for more detai++++++++ls.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = '''
---
module: netconfc_connection_config
version_added: "2.6"
description:
    - Set the NETCONF connection for remote.
author: Wangqijun (@netengine-Ansible)

options:
    operation:
        description:
            - Ansible operation.
        required: true
        default: null
        choices: ['create', 'delete', 'get']
    timeoutMin:
        description:
            - Minute of timeout time.
        required: false
        default: 10
    timeoutSec:
        description:
            - Second of timeout time.
        required: false
        default: 0
    maxSessions:
        description:
            - Max number of sessions.
        required: false
        default: 5
    showContent:
        description:
            - Max number of sessions.
        required: false
        choices:['capability','timeout','maxsessions']
        default: null
    deleteContent:
        description:
            - Max number of sessions.
        required: false
        choices:['timeout','maxsessions']
        default: null
'''

EXAMPLES = '''

- name: netconf maxsessons timeout capability
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    yang:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      operation: create or delete or get

  tasks:

  - name: "Display capability"
    netconf_timeout_maxsessions_capability:
      operation: get
      showContent: capability

  - name: "Display timeout"
    netconf_timeout_maxsessions_capability:
      operation: get
      showContent: timeout

  - name: "Display maxsessions"
    netconf_timeout_maxsessions_capability:
      operation: get
      showContent: maxsessions

  - name: "Set maxsessions"
    netconf_timeout_maxsessions_capability:
      operation: create
      maxSessions: 15

  - name: "Set timeout"
    netconf_timeout_maxsessions_capability:
      operation: create
      timeoutMin: 20
      timeoutSec: 20

  - name: "Delete maxsessions"
    netconf_timeout_maxsessions_capability:
      operation: delete
      deleteContent: maxsessions

  - name: "Delete timeout"
    netconf_timeout_maxsessions_capability:
      operation: delete
      deleteContent: timeout
'''


netconf_timeout_maxsessions_spec = {
    'timeoutMin': dict(type='int'),
    'timeoutSec': dict(type='int'),
    'maxSessions': dict(type='int'),
    'showContent': dict(choices=['capability', 'timeout', 'maxsessions']),
    'deleteContent': dict(choices=['timeout', 'maxsessions'])
}

NETCONF_TIMEOUTANDMAXSESSIONS_HEAD = """
<config>
  <sshs xmlns="http://www.huawei.com/netconf/vrp/huawei-sshs">
    <sshNcaVtyCfg>
"""

NETCONF_TIMEOUTANDMAXSESSIONS_HEAD_DEL = """
<config>
  <sshs xmlns="http://www.huawei.com/netconf/vrp/huawei-sshs">
    <sshNcaVtyCfg nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

NETCONF_TIMEOUTANDMAXSESSIONS_TAIL = """
    </sshNcaVtyCfg>
  </sshs>
</config>
"""

NETCONF_TIMEOUTMIN = """
      <timeoutMin>%d</timeoutMin>
"""

NETCONF_TIMEOUTMIN_DEL = """
      <timeoutMin nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%d</timeoutMin>
"""

NETCONF_TIMEOUTSEC = """
      <timeoutSec>%d</timeoutSec>
"""

NETCONF_TIMEOUTSEC_DEL = """
      <timeoutSec nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%d</timeoutSec>
"""

NETCONF_MAXSESSIONS = """
      <maxSessions>%d</maxSessions>
"""

NETCONF_MAXSESSIONS_DEL = """
      <maxSessions nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%d</maxSessions>
"""

GET_SSHNCAVTYCFG_MAXSESSIONS_GETCONFIG = """
  <filter type="subtree">
    <sshs:sshs xmlns:sshs="http://www.huawei.com/netconf/vrp/huawei-sshs">
      <sshs:sshNcaVtyCfg>
        <sshs:maxSessions/>
      </sshs:sshNcaVtyCfg>
    </sshs:sshs>
  </filter>
"""

GET_SSHNCAVTYCFG_TIMEOUT_GETCONFIG = """
  <filter type="subtree">
    <sshs:sshs xmlns:sshs="http://www.huawei.com/netconf/vrp/huawei-sshs">
      <sshs:sshNcaVtyCfg>
        <sshs:timeoutMin/>
        <sshs:timeoutSec/>
      </sshs:sshNcaVtyCfg>
    </sshs:sshs>
  </filter>
"""

GET_CAPABILITY_ALL_GETCONFIG = """
<filter type="subtree">
  <netconf:netconf xmlns:netconf="http://www.huawei.com/netconf/vrp/huawei-netconf">
    <netconf:netconfCapabilitys>
      <netconf:netconfCapability/>
    </netconf:netconfCapabilitys>
  </netconf:netconf>
</filter>
"""


class SettimeAndmaxsession(object):
    """
     Netconf set timeidle and max sessions
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.timeoutMin = self.module.params['timeoutMin']
        self.timeoutSec = self.module.params['timeoutSec']
        self.maxSessions = self.module.params['maxSessions']
        self.showContent = self.module.params['showContent']
        self.deleteContent = self.module.params['deleteContent']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def xml_make(self):
        TimeoutAndMaxsessions_xml = ''
        TimeoutAndMaxsessions_xml += NETCONF_TIMEOUTANDMAXSESSIONS_HEAD
        if self.operation == 'create':
            if self.timeoutMin or self.timeoutMin == '':
                TimeoutAndMaxsessions_xml += NETCONF_TIMEOUTMIN % self.timeoutMin

            if self.timeoutSec or self.timeoutSec == '':
                TimeoutAndMaxsessions_xml += NETCONF_TIMEOUTSEC % self.timeoutSec

            if self.maxSessions or self.maxSessions == '':
                TimeoutAndMaxsessions_xml += NETCONF_MAXSESSIONS % self.maxSessions

        if self.operation == 'delete':
            if self.deleteContent == 'timeout':
                TimeoutAndMaxsessions_xml += NETCONF_TIMEOUTMIN % 10
                TimeoutAndMaxsessions_xml += NETCONF_TIMEOUTSEC % 0
            if self.deleteContent == 'maxsessions':
                TimeoutAndMaxsessions_xml += NETCONF_MAXSESSIONS % 5

        TimeoutAndMaxsessions_xml += NETCONF_TIMEOUTANDMAXSESSIONS_TAIL

        return TimeoutAndMaxsessions_xml

    def run(self):
        if self.operation == 'get':
            if self.showContent == 'timeout':
                recv_xml = get_nc_config(
                    self.module, GET_SSHNCAVTYCFG_TIMEOUT_GETCONFIG)
            elif self.showContent == 'maxsessions':
                recv_xml = get_nc_config(
                    self.module, GET_SSHNCAVTYCFG_MAXSESSIONS_GETCONFIG)
            elif self.showContent == 'capability':
                recv_xml = get_nc_config(
                    self.module, GET_CAPABILITY_ALL_GETCONFIG)
        else:
            TimeoutAndMaxsessions_xml = self.xml_make()
            recv_xml = set_nc_config(self.module, TimeoutAndMaxsessions_xml)
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        operation=dict(choices=['create', 'delete', 'get'])
    )
    argument_spec.update(ne_argument_spec)
    argument_spec.update(netconf_timeout_maxsessions_spec)

    timeidle_maxsessions_setting = SettimeAndmaxsession(argument_spec)
    timeidle_maxsessions_setting.run()


if __name__ == '__main__':
    main()
