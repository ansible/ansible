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
from xml.etree import ElementTree
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'syslog'}

DOCUMENTATION = '''
---
module: syslog_host_getconfig
version_added: "2.6"
short_description: Get configurations of SYSLOG server on HUAWEI router.
description:
    - Get configurations of SYSLOG server on HUAWEI router.
author:

options:
    operation:
        description:
            - Ansible operation.
        required: false
        default: null
        choices: ['create', 'delete', '']
    ipType:
        description:
            - Log server address type, IPv4 or IPv6.
        required: false
        default: null
        choices: ['ipv4', 'ipv6', '']
    serverIp:
        description:
            - Log server address, IPv4 or IPv6 type.
        required: false
        default: null
    vrfName:
        description:
            - Log server address, IPv4 or IPv6 type.
        required: false
        default: null
    isDefaultVpn:
        description:
            - Use the default VPN or not.
        required: false
        default: null
        choices: ['true', 'false', '']
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
        choices: ['local0', 'local1', 'local2', 'local3', 'local4', 'local5', 'local6', 'local7', '']
    timestamp:
        description:
            - Log server timestamp.
        required: false
        default: null
        choices: ['UTC', 'localtime', '']
    transportMode:
        description:
            - Transport mode.
        required: false
        default: null
        choices: ['tcp', 'udp', '']
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

  tasks:

  - name: "Get syslog server config"
    syslog_host_getconfig:

  - name: "Get syslog server config filtered by server IP"
    syslog_host_getconfig:
      serverIP: "1.1.1.1"

  - name: "Get syslog server config filtered by server IP"
    syslog_host_getconfig:
      serverIP: ""
'''

RETURN = '''
localhost | SUCCESS => {
    "changed": false,
    "invocation": {
        "module_args": {
            "facility": null,
            "host": "10.252.8.172",
            "ipType": null,
            "isDefaultVpn": null,
            "level": null,
            "password": "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER",
            "port": 20022,
            "provider": null,
            "serverIp": "10.40.41.33",
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
            "vrfName": null
        }
    },
    "response": [
        {
            "syslog_server": [
                {
                    "facility": "local7",
                    "ipType": "ipv4",
                    "isDefaultVpn": "true",
                    "level": "debugging",
                    "serverIp": "10.40.41.33",
                    "serverPort": "514",
                    "sourceIP": "0.0.0.0",
                    "timestamp": "UTC",
                    "transportMode": "udp",
                    "vrfName": "_public_"
                }
            ]
        }
    ]
}
'''


SYSLOG_SERVER_GET_HEAD = """
  <filter type="subtree">
    <syslog:syslog xmlns:syslog="http://www.huawei.com/netconf/vrp/huawei-syslog">
      <syslog:syslogServers>
        <syslog:syslogServer>
"""

SYSLOG_SERVER_GET_TAIL = """
        </syslog:syslogServer>
      </syslog:syslogServers>
    </syslog:syslog>
  </filter>
"""

syslog_server_get_filed = {
    'ipType': """
      <syslog:ipType>%s</syslog:ipType>""",

    'serverIp': """
      <syslog:serverIp>%s</syslog:serverIp>""",

    'isDefaultVpn': """
      <syslog:isDefaultVpn>%s</syslog:isDefaultVpn>""",

    'vrfName': """
      <syslog:vrfName>%s</syslog:vrfName>""",

    'level': """
      <syslog:level>%s</syslog:level>""",

    'serverPort': """
      <syslog:serverPort>%s</syslog:serverPort>""",

    'facility': """
      <syslog:facility>%s</syslog:facility>""",

    'timestamp': """
      <syslog:timestamp>%s</syslog:timestamp>""",

    'transportMode': """
      <syslog:transportMode>%s</syslog:transportMode>""",

    'sslPolicyName': """
      <syslog:sslPolicyName>%s</syslog:sslPolicyName>""",

    'sourceIP': """
      <syslog:sourceIP>%s</syslog:sourceIP>"""
}

syslog_server_get_filed_null = {
    'ipType': """
      <syslog:ipType/>""",

    'serverIp': """
      <syslog:serverIp/>""",

    'isDefaultVpn': """
      <syslog:isDefaultVpn/>""",

    'vrfName': """
      <syslog:vrfName/>""",

    'level': """
      <syslog:level/>""",

    'serverPort': """
      <syslog:serverPort/>""",

    'facility': """
      <syslog:facility/>""",

    'timestamp': """
      <syslog:timestamp/>""",

    'transportMode': """
      <syslog:transportMode/>""",

    'sslPolicyName': """
      <syslog:sslPolicyName/>""",

    'sourceIP': """
      <syslog:sourceIP/>"""
}

syslog_server_argument_spec = {
    'ipType': dict(choices=['ipv4', 'ipv6', '']),
    'serverIp': dict(type='str'),
    'isDefaultVpn': dict(choices=['true', 'false', '']),
    'vrfName': dict(type='str'),
    'level': dict(choices=['emergencies', 'alert', 'critical', 'error', 'warning', 'notification', 'informational', 'debugging', '']),
    'serverPort': dict(type='str'),
    'facility': dict(choices=['local0', 'local1', 'local2', 'local3', 'local4', 'local5', 'local6', 'local7', '']),
    'timestamp': dict(choices=['UTC', 'localtime', '']),
    'transportMode': dict(choices=['tcp', 'udp', '']),
    'sslPolicyName': dict(type='str'),
    'sourceIP': dict(type='str')
}


def config_param_exist(arg):
    if arg or arg == '':
        return True
    return False


class SyslogServerGet(object):
    """
    syslog server get class
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.results = dict()
        self.results['response'] = []

    def syslog_server_get_str(self):
        syslog_server_get_str = ''

        syslog_server_get_str += SYSLOG_SERVER_GET_HEAD

        # k is the key of input param, v is the value of input param
        for k, v in self.module.params.items():
            if k in syslog_server_get_filed:  # if the send filed is exist of the key
                if v:
                    syslog_server_get_str += syslog_server_get_filed[k] % v
                elif v == '':
                    syslog_server_get_str += syslog_server_get_filed_null[k]

        syslog_server_get_str += SYSLOG_SERVER_GET_TAIL

        return syslog_server_get_str
        # return SYSLOG_SERVER_GET

    def syslog_server_get(self):
        return get_nc_config(self.module, self.syslog_server_get_str())


def syslog_server_get_parse(xml_ret):
    xml_str = xml_ret.replace('\r', '').replace('\n', '').\
        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
        replace('xmlns=\"http://www.huawei.com/netconf/vrp/huawei-syslog"', "")

    root = ElementTree.fromstring(xml_str)
    cfg_info = root.findall("syslog/syslogServers/syslogServer")

    result = dict()
    result["syslog_server"] = []
    if cfg_info:
        for temp in cfg_info:
            tmp_dict = dict()
            for site in temp:
                if site.tag in ["ipType", "serverIp", "isDefaultVpn",
                                "vrfName", "level", "serverPort",
                                "facility", "timestamp", "transportMode",
                                "sslPolicyName", "sourceIP"]:
                    tmp_dict[site.tag] = site.text
            result["syslog_server"].append(tmp_dict)

    return result


def main():
    """ main function """

    argument_spec = dict()

    argument_spec.update(ne_argument_spec)
    argument_spec.update(syslog_server_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    results = dict()

    syslog_server_get_obj = SyslogServerGet(argument_spec)
    xml_ret = syslog_server_get_obj.syslog_server_get()

    tgt_values = dict()
    tgt_result = syslog_server_get_parse(xml_ret)
    if tgt_result:
        for item in tgt_result:
            tgt_values[item] = tgt_result[item]

    results["response"] = []
    results['response'].append(tgt_values)
    module.exit_json(**results)


if __name__ == '__main__':
    main()
