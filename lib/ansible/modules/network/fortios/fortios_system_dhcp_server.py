#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_system_dhcp_server
short_description: Configure DHCP servers in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify system_dhcp feature and server category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
version_added: "2.8"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
       description:
            - FortiOS or FortiGate ip address.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: true
    system_dhcp_server:
        description:
            - Configure DHCP servers.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            auto-configuration:
                description:
                    - Enable/disable auto configuration.
                choices:
                    - disable
                    - enable
            conflicted-ip-timeout:
                description:
                    - Time in seconds to wait after a conflicted IP address is removed from the DHCP range before it can be reused.
            ddns-auth:
                description:
                    - DDNS authentication mode.
                choices:
                    - disable
                    - tsig
            ddns-key:
                description:
                    - DDNS update key (base 64 encoding).
            ddns-keyname:
                description:
                    - DDNS update key name.
            ddns-server-ip:
                description:
                    - DDNS server IP.
            ddns-ttl:
                description:
                    - TTL.
            ddns-update:
                description:
                    - Enable/disable DDNS update for DHCP.
                choices:
                    - disable
                    - enable
            ddns-update-override:
                description:
                    - Enable/disable DDNS update override for DHCP.
                choices:
                    - disable
                    - enable
            ddns-zone:
                description:
                    - Zone of your domain name (ex. DDNS.com).
            default-gateway:
                description:
                    - Default gateway IP address assigned by the DHCP server.
            dns-server1:
                description:
                    - DNS server 1.
            dns-server2:
                description:
                    - DNS server 2.
            dns-server3:
                description:
                    - DNS server 3.
            dns-service:
                description:
                    - Options for assigning DNS servers to DHCP clients.
                choices:
                    - local
                    - default
                    - specify
            domain:
                description:
                    - Domain name suffix for the IP addresses that the DHCP server assigns to clients.
            exclude-range:
                description:
                    - Exclude one or more ranges of IP addresses from being assigned to clients.
                suboptions:
                    end-ip:
                        description:
                            - End of IP range.
                    id:
                        description:
                            - ID.
                        required: true
                    start-ip:
                        description:
                            - Start of IP range.
            filename:
                description:
                    - Name of the boot file on the TFTP server.
            forticlient-on-net-status:
                description:
                    - Enable/disable FortiClient-On-Net service for this DHCP server.
                choices:
                    - disable
                    - enable
            id:
                description:
                    - ID.
                required: true
            interface:
                description:
                    - DHCP server can assign IP configurations to clients connected to this interface. Source system.interface.name.
            ip-mode:
                description:
                    - Method used to assign client IP.
                choices:
                    - range
                    - usrgrp
            ip-range:
                description:
                    - DHCP IP range configuration.
                suboptions:
                    end-ip:
                        description:
                            - End of IP range.
                    id:
                        description:
                            - ID.
                        required: true
                    start-ip:
                        description:
                            - Start of IP range.
            ipsec-lease-hold:
                description:
                    - DHCP over IPsec leases expire this many seconds after tunnel down (0 to disable forced-expiry).
            lease-time:
                description:
                    - Lease time in seconds, 0 means unlimited.
            mac-acl-default-action:
                description:
                    - MAC access control default action (allow or block assigning IP settings).
                choices:
                    - assign
                    - block
            netmask:
                description:
                    - Netmask assigned by the DHCP server.
            next-server:
                description:
                    - IP address of a server (for example, a TFTP sever) that DHCP clients can download a boot file from.
            ntp-server1:
                description:
                    - NTP server 1.
            ntp-server2:
                description:
                    - NTP server 2.
            ntp-server3:
                description:
                    - NTP server 3.
            ntp-service:
                description:
                    - Options for assigning Network Time Protocol (NTP) servers to DHCP clients.
                choices:
                    - local
                    - default
                    - specify
            options:
                description:
                    - DHCP options.
                suboptions:
                    code:
                        description:
                            - DHCP option code.
                    id:
                        description:
                            - ID.
                        required: true
                    ip:
                        description:
                            - DHCP option IPs.
                    type:
                        description:
                            - DHCP option type.
                        choices:
                            - hex
                            - string
                            - ip
                    value:
                        description:
                            - DHCP option value.
            reserved-address:
                description:
                    - Options for the DHCP server to assign IP settings to specific MAC addresses.
                suboptions:
                    action:
                        description:
                            - Options for the DHCP server to configure the client with the reserved MAC address.
                        choices:
                            - assign
                            - block
                            - reserved
                    description:
                        description:
                            - Description.
                    id:
                        description:
                            - ID.
                        required: true
                    ip:
                        description:
                            - IP address to be reserved for the MAC address.
                    mac:
                        description:
                            - MAC address of the client that will get the reserved IP address.
            server-type:
                description:
                    - DHCP server can be a normal DHCP server or an IPsec DHCP server.
                choices:
                    - regular
                    - ipsec
            status:
                description:
                    - Enable/disable this DHCP configuration.
                choices:
                    - disable
                    - enable
            tftp-server:
                description:
                    - One or more hostnames or IP addresses of the TFTP servers in quotes separated by spaces.
                suboptions:
                    tftp-server:
                        description:
                            - TFTP server.
                        required: true
            timezone:
                description:
                    - Select the time zone to be assigned to DHCP clients.
                choices:
                    - 01
                    - 02
                    - 03
                    - 04
                    - 05
                    - 81
                    - 06
                    - 07
                    - 08
                    - 09
                    - 10
                    - 11
                    - 12
                    - 13
                    - 74
                    - 14
                    - 77
                    - 15
                    - 87
                    - 16
                    - 17
                    - 18
                    - 19
                    - 20
                    - 75
                    - 21
                    - 22
                    - 23
                    - 24
                    - 80
                    - 79
                    - 25
                    - 26
                    - 27
                    - 28
                    - 78
                    - 29
                    - 30
                    - 31
                    - 32
                    - 33
                    - 34
                    - 35
                    - 36
                    - 37
                    - 38
                    - 83
                    - 84
                    - 40
                    - 85
                    - 41
                    - 42
                    - 43
                    - 39
                    - 44
                    - 46
                    - 47
                    - 51
                    - 48
                    - 45
                    - 49
                    - 50
                    - 52
                    - 53
                    - 54
                    - 55
                    - 56
                    - 57
                    - 58
                    - 59
                    - 60
                    - 62
                    - 63
                    - 61
                    - 64
                    - 65
                    - 66
                    - 67
                    - 68
                    - 69
                    - 70
                    - 71
                    - 72
                    - 00
                    - 82
                    - 73
                    - 86
                    - 76
            timezone-option:
                description:
                    - Options for the DHCP server to set the client's time zone.
                choices:
                    - disable
                    - default
                    - specify
            vci-match:
                description:
                    - Enable/disable vendor class identifier (VCI) matching. When enabled only DHCP requests with a matching VCI are served.
                choices:
                    - disable
                    - enable
            vci-string:
                description:
                    - One or more VCI strings in quotes separated by spaces.
                suboptions:
                    vci-string:
                        description:
                            - VCI strings.
                        required: true
            wifi-ac1:
                description:
                    - WiFi Access Controller 1 IP address (DHCP option 138, RFC 5417).
            wifi-ac2:
                description:
                    - WiFi Access Controller 2 IP address (DHCP option 138, RFC 5417).
            wifi-ac3:
                description:
                    - WiFi Access Controller 3 IP address (DHCP option 138, RFC 5417).
            wins-server1:
                description:
                    - WINS server 1.
            wins-server2:
                description:
                    - WINS server 2.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure DHCP servers.
    fortios_system_dhcp_server:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_dhcp_server:
        state: "present"
        auto-configuration: "disable"
        conflicted-ip-timeout: "4"
        ddns-auth: "disable"
        ddns-key: "<your_own_value>"
        ddns-keyname: "<your_own_value>"
        ddns-server-ip: "<your_own_value>"
        ddns-ttl: "9"
        ddns-update: "disable"
        ddns-update-override: "disable"
        ddns-zone: "<your_own_value>"
        default-gateway: "<your_own_value>"
        dns-server1: "<your_own_value>"
        dns-server2: "<your_own_value>"
        dns-server3: "<your_own_value>"
        dns-service: "local"
        domain: "<your_own_value>"
        exclude-range:
         -
            end-ip: "<your_own_value>"
            id:  "21"
            start-ip: "<your_own_value>"
        filename: "<your_own_value>"
        forticlient-on-net-status: "disable"
        id:  "25"
        interface: "<your_own_value> (source system.interface.name)"
        ip-mode: "range"
        ip-range:
         -
            end-ip: "<your_own_value>"
            id:  "30"
            start-ip: "<your_own_value>"
        ipsec-lease-hold: "32"
        lease-time: "33"
        mac-acl-default-action: "assign"
        netmask: "<your_own_value>"
        next-server: "<your_own_value>"
        ntp-server1: "<your_own_value>"
        ntp-server2: "<your_own_value>"
        ntp-server3: "<your_own_value>"
        ntp-service: "local"
        options:
         -
            code: "42"
            id:  "43"
            ip: "<your_own_value>"
            type: "hex"
            value: "<your_own_value>"
        reserved-address:
         -
            action: "assign"
            description: "<your_own_value>"
            id:  "50"
            ip: "<your_own_value>"
            mac: "<your_own_value>"
        server-type: "regular"
        status: "disable"
        tftp-server:
         -
            tftp-server: "<your_own_value>"
        timezone: "01"
        timezone-option: "disable"
        vci-match: "disable"
        vci-string:
         -
            vci-string: "<your_own_value>"
        wifi-ac1: "<your_own_value>"
        wifi-ac2: "<your_own_value>"
        wifi-ac3: "<your_own_value>"
        wins-server1: "<your_own_value>"
        wins-server2: "<your_own_value>"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "id"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_system_dhcp_server_data(json):
    option_list = ['auto-configuration', 'conflicted-ip-timeout', 'ddns-auth',
                   'ddns-key', 'ddns-keyname', 'ddns-server-ip',
                   'ddns-ttl', 'ddns-update', 'ddns-update-override',
                   'ddns-zone', 'default-gateway', 'dns-server1',
                   'dns-server2', 'dns-server3', 'dns-service',
                   'domain', 'exclude-range', 'filename',
                   'forticlient-on-net-status', 'id', 'interface',
                   'ip-mode', 'ip-range', 'ipsec-lease-hold',
                   'lease-time', 'mac-acl-default-action', 'netmask',
                   'next-server', 'ntp-server1', 'ntp-server2',
                   'ntp-server3', 'ntp-service', 'options',
                   'reserved-address', 'server-type', 'status',
                   'tftp-server', 'timezone', 'timezone-option',
                   'vci-match', 'vci-string', 'wifi-ac1',
                   'wifi-ac2', 'wifi-ac3', 'wins-server1',
                   'wins-server2']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def system_dhcp_server(data, fos):
    vdom = data['vdom']
    system_dhcp_server_data = data['system_dhcp_server']
    flattened_data = flatten_multilists_attributes(system_dhcp_server_data)
    filtered_data = filter_system_dhcp_server_data(flattened_data)
    if system_dhcp_server_data['state'] == "present":
        return fos.set('system.dhcp',
                       'server',
                       data=filtered_data,
                       vdom=vdom)

    elif system_dhcp_server_data['state'] == "absent":
        return fos.delete('system.dhcp',
                          'server',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def fortios_system_dhcp(data, fos):
    login(data)

    if data['system_dhcp_server']:
        resp = system_dhcp_server(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "system_dhcp_server": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "auto-configuration": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                "conflicted-ip-timeout": {"required": False, "type": "int"},
                "ddns-auth": {"required": False, "type": "str",
                              "choices": ["disable", "tsig"]},
                "ddns-key": {"required": False, "type": "str"},
                "ddns-keyname": {"required": False, "type": "str"},
                "ddns-server-ip": {"required": False, "type": "str"},
                "ddns-ttl": {"required": False, "type": "int"},
                "ddns-update": {"required": False, "type": "str",
                                "choices": ["disable", "enable"]},
                "ddns-update-override": {"required": False, "type": "str",
                                         "choices": ["disable", "enable"]},
                "ddns-zone": {"required": False, "type": "str"},
                "default-gateway": {"required": False, "type": "str"},
                "dns-server1": {"required": False, "type": "str"},
                "dns-server2": {"required": False, "type": "str"},
                "dns-server3": {"required": False, "type": "str"},
                "dns-service": {"required": False, "type": "str",
                                "choices": ["local", "default", "specify"]},
                "domain": {"required": False, "type": "str"},
                "exclude-range": {"required": False, "type": "list",
                                  "options": {
                                      "end-ip": {"required": False, "type": "str"},
                                      "id": {"required": True, "type": "int"},
                                      "start-ip": {"required": False, "type": "str"}
                                  }},
                "filename": {"required": False, "type": "str"},
                "forticlient-on-net-status": {"required": False, "type": "str",
                                              "choices": ["disable", "enable"]},
                "id": {"required": True, "type": "int"},
                "interface": {"required": False, "type": "str"},
                "ip-mode": {"required": False, "type": "str",
                            "choices": ["range", "usrgrp"]},
                "ip-range": {"required": False, "type": "list",
                             "options": {
                                 "end-ip": {"required": False, "type": "str"},
                                 "id": {"required": True, "type": "int"},
                                 "start-ip": {"required": False, "type": "str"}
                             }},
                "ipsec-lease-hold": {"required": False, "type": "int"},
                "lease-time": {"required": False, "type": "int"},
                "mac-acl-default-action": {"required": False, "type": "str",
                                           "choices": ["assign", "block"]},
                "netmask": {"required": False, "type": "str"},
                "next-server": {"required": False, "type": "str"},
                "ntp-server1": {"required": False, "type": "str"},
                "ntp-server2": {"required": False, "type": "str"},
                "ntp-server3": {"required": False, "type": "str"},
                "ntp-service": {"required": False, "type": "str",
                                "choices": ["local", "default", "specify"]},
                "options": {"required": False, "type": "list",
                            "options": {
                                "code": {"required": False, "type": "int"},
                                "id": {"required": True, "type": "int"},
                                "ip": {"required": False, "type": "str"},
                                "type": {"required": False, "type": "str",
                                         "choices": ["hex", "string", "ip"]},
                                "value": {"required": False, "type": "str"}
                            }},
                "reserved-address": {"required": False, "type": "list",
                                     "options": {
                                         "action": {"required": False, "type": "str",
                                                    "choices": ["assign", "block", "reserved"]},
                                         "description": {"required": False, "type": "str"},
                                         "id": {"required": True, "type": "int"},
                                         "ip": {"required": False, "type": "str"},
                                         "mac": {"required": False, "type": "str"}
                                     }},
                "server-type": {"required": False, "type": "str",
                                "choices": ["regular", "ipsec"]},
                "status": {"required": False, "type": "str",
                           "choices": ["disable", "enable"]},
                "tftp-server": {"required": False, "type": "list",
                                "options": {
                                    "tftp-server": {"required": True, "type": "str"}
                                }},
                "timezone": {"required": False, "type": "str",
                             "choices": ["01", "02", "03",
                                         "04", "05", "81",
                                         "06", "07", "08",
                                         "09", "10", "11",
                                         "12", "13", "74",
                                         "14", "77", "15",
                                         "87", "16", "17",
                                         "18", "19", "20",
                                         "75", "21", "22",
                                         "23", "24", "80",
                                         "79", "25", "26",
                                         "27", "28", "78",
                                         "29", "30", "31",
                                         "32", "33", "34",
                                         "35", "36", "37",
                                         "38", "83", "84",
                                         "40", "85", "41",
                                         "42", "43", "39",
                                         "44", "46", "47",
                                         "51", "48", "45",
                                         "49", "50", "52",
                                         "53", "54", "55",
                                         "56", "57", "58",
                                         "59", "60", "62",
                                         "63", "61", "64",
                                         "65", "66", "67",
                                         "68", "69", "70",
                                         "71", "72", "00",
                                         "82", "73", "86",
                                         "76"]},
                "timezone-option": {"required": False, "type": "str",
                                    "choices": ["disable", "default", "specify"]},
                "vci-match": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "vci-string": {"required": False, "type": "list",
                               "options": {
                                   "vci-string": {"required": True, "type": "str"}
                               }},
                "wifi-ac1": {"required": False, "type": "str"},
                "wifi-ac2": {"required": False, "type": "str"},
                "wifi-ac3": {"required": False, "type": "str"},
                "wins-server1": {"required": False, "type": "str"},
                "wins-server2": {"required": False, "type": "str"}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_system_dhcp(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
