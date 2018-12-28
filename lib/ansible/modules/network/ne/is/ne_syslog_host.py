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

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'syslog'}

DOCUMENTATION = '''
---
module: syslog_host
version_added: "2.6"
short_description: Manages SYSLOG server configuration on HUAWEI router.
description:
    - Manages SYSLOG host on HUAWEI router.
author:

options:
    operation:
        description:
            - Ansible operation.
        required: true
        default: null
        choices: ['create', 'delete']
    ipType:
        description:
            - Log server address type, IPv4 or IPv6.
        required: true
        default: null
        choices: ['ipv4', 'ipv6']
    vrfName:
        description:
            - Log server address, IPv4 or IPv6 type.
        required: true
        default: null
    serverIp:
        description:
            - VPN name on a log server.
        required: true
        default: null
    isDefaultVpn:
        description:
            - Use the default VPN or not.
        required: false
        default: null
        choices: ['true', 'false']
    vrfName:
        description:
            - VPN name on a log server.
        required: false
        default: null
    level:
        description:
            - Level of logs saved on a log server.
        required: false
        default: null
        choices: ['emergencies', 'alert', 'critical', 'error', 'warning', 'notification', 'informational', 'debugging']
    serverPort:
        description:
            - Number of a port recving logs.
        required: false
        default: null
    facility:
        description:
            - Log record tool.
        required: false
        default: null
        choices: ['local0', 'local1', 'local2', 'local3', 'local4', 'local5', 'local6', 'local7']
    timestamp:
        description:
            - Log server timestamp.
        required: false
        default: null
        choices: ['UTC', 'localtime']
    transportMode:
        description:
            - Transport mode.
        required: false
        default: null
        choices: ['tcp', 'udp']
    sslPolicyName:
        description:
            - SSL policy name.
        required: false
        default: null
    sourceIP:
        description:
            - Syslog source IP address.
        required: false
        default: null
'''

EXAMPLES = '''

- name: syslog server test
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    yang:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      operation: create or delete

  tasks:

  - name: "Create a syslog server"
    syslog_host:
      operation: create
      ipType: ipv4
      serverIp: 1.1.1.1
      isDefaultVpn: true
      vrfName: _public_

  - name: "Delete a syslog server"
    syslog_host:
      operation: delete
      ipType: ipv4
      serverIp: 1.1.1.1
      isDefaultVpn: true
      vrfName: _public_
'''

RETURN = '''
    "changed": true,
    "invocation": {
        "module_args": {
            "facility": null,
            "host": "10.252.8.172",
            "ipType": "ipv4",
            "isDefaultVpn": "true",
            "level": null,
            "operation": "create",
            "password": "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER",
            "port": 20022,
            "provider": null,
            "serverIp": "1.1.1.1",
            "serverPort": null,
            "sourceIP": null,
            "sslPolicyName": null,
            "timeout": null,
            "timestamp": null,
            "transport": null,
            "transportMode": null,
            "use_ssl": null,
            "username": "root123",
            "validate_certs": null,
            "vrfName": "_public_"
        }
    },
    "response": "OK"
'''


SYSLOG_SERVER_CFG_HEAD = """
<config>
    <syslog xmlns="http://www.huawei.com/netconf/vrp/huawei-syslog">
        <syslogServers>
            <syslogServer>
"""

SYSLOG_SERVER_DELCFG_HEAD = """
<config>
    <syslog xmlns="http://www.huawei.com/netconf/vrp/huawei-syslog">
        <syslogServers>
            <syslogServer nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SYSLOG_SERVER_CONF_TAIL = """
        </syslogServer>
    </syslogServers>
  </syslog>
</config>
"""

syslog_server_cfg_filed = {
    'ipType': """
      <ipType>%s</ipType>""",

    'serverIp': """
      <serverIp>%s</serverIp>""",

    'isDefaultVpn': """
      <isDefaultVpn>%s</isDefaultVpn>""",

    'vrfName': """
      <vrfName>%s</vrfName>""",

    'level': """
      <level>%s</level>""",

    'serverPort': """
      <serverPort>%s</serverPort>""",

    'facility': """
      <facility>%s</facility>""",

    'timestamp': """
      <timestamp>%s</timestamp>""",

    'transportMode': """
      <transportMode>%s</transportMode>""",

    'sslPolicyName': """
      <sslPolicyName>%s</sslPolicyName>""",

    'sourceIP': """
      <sourceIP>%s</sourceIP>"""
}

syslog_server_cfg_del_filed = {
    'ipType': """
      <ipType nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ipType>""",

    'serverIp': """
      <serverIp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</serverIp>""",

    'isDefaultVpn': """
      <isDefaultVpn nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</isDefaultVpn>""",

    'vrfName': """
      <vrfName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</vrfName>""",

    'level': """
      <level nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</level>""",

    'serverPort': """
      <serverPort nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</serverPort>""",

    'facility': """
      <facility nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</facility>""",

    'timestamp': """
      <timestamp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</timestamp>""",

    'transportMode': """
      <transportMode nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</transportMode>""",

    'sslPolicyName': """
      <sslPolicyName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</sslPolicyName>""",

    'sourceIP': """
      <sourceIP nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</sourceIP>"""
}

syslog_server_argument_spec = {
    'ipType': dict(choices=['ipv4', 'ipv6']),
    'serverIp': dict(type='str'),
    'isDefaultVpn': dict(choices=['true', 'false']),
    'vrfName': dict(type='str'),
    'level': dict(choices=['emergencies', 'alert', 'critical', 'error', 'warning', 'notification', 'informational', 'debugging']),
    'serverPort': dict(type='str'),
    'facility': dict(choices=['local0', 'local1', 'local2', 'local3', 'local4', 'local5', 'local6', 'local7']),
    'timestamp': dict(choices=['UTC', 'localtime']),
    'transportMode': dict(choices=['tcp', 'udp']),
    'sslPolicyName': dict(type='str'),
    'sourceIP': dict(type='str')
}


def config_param_exist(arg):
    if arg or arg == '':
        return True
    return False


class SyslogServer(object):
    """
    Syslog server management
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    # Generate config or delete xml string
    def syslog_server_config_str(self):
        syslog_server_cfg_str = ''

        if self.operation == 'create':
            syslog_server_cfg_str += SYSLOG_SERVER_CFG_HEAD

            # k is the key of input param, v is the value of input param
            for k, v in self.module.params.items():
                if config_param_exist(v):
                    if k in syslog_server_cfg_filed:  # if the send filed is exist of the key
                        syslog_server_cfg_str += syslog_server_cfg_filed[k] % v

        elif self.operation == 'delete':
            syslog_server_cfg_str += SYSLOG_SERVER_DELCFG_HEAD

            # k is the key of input param, v is the value of input param
            for k, v in self.module.params.items():
                if config_param_exist(v):
                    if k in syslog_server_cfg_del_filed:  # if the send filed is exist of the key
                        syslog_server_cfg_str += syslog_server_cfg_del_filed[k] % v

        syslog_server_cfg_str += SYSLOG_SERVER_CONF_TAIL

        return syslog_server_cfg_str

    # send config xml string
    def syslog_server_config(self):
        return set_nc_config(self.module, self.syslog_server_config_str())


def main():
    """ main function """

    argument_spec = dict(
        operation=dict(choices=['create', 'delete'], default='create')
    )

    argument_spec.update(ne_argument_spec)
    argument_spec.update(syslog_server_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    results = dict()

    syslog_server_obj = SyslogServer(argument_spec)
    result = syslog_server_obj.syslog_server_config()

    if "<ok/>" not in result:
        results['changed'] = False
        results['response'] = result
    else:
        results['changed'] = True
        results['response'] = 'OK'

    module.exit_json(**results)


if __name__ == '__main__':
    main()
