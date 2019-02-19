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
module: fortios_firewall_service_custom
short_description: Configure custom services in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall_service feature and custom category.
      Examples includes all options and need to be adjusted to datasources before usage.
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
            - FortiOS or FortiGate ip adress.
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
    firewall_service_custom:
        description:
            - Configure custom services.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            app-category:
                description:
                    - Application category ID.
                suboptions:
                    id:
                        description:
                            - Application category id.
                        required: true
            app-service-type:
                description:
                    - Application service type.
                choices:
                    - disable
                    - app-id
                    - app-category
            application:
                description:
                    - Application ID.
                suboptions:
                    id:
                        description:
                            - Application id.
                        required: true
            category:
                description:
                    - Service category. Source firewall.service.category.name.
            check-reset-range:
                description:
                    - Configure the type of ICMP error message verification.
                choices:
                    - disable
                    - strict
                    - default
            color:
                description:
                    - Color of icon on the GUI.
            comment:
                description:
                    - Comment.
            fqdn:
                description:
                    - Fully qualified domain name.
            helper:
                description:
                    - Helper name.
                choices:
                    - auto
                    - disable
                    - ftp
                    - tftp
                    - ras
                    - h323
                    - tns
                    - mms
                    - sip
                    - pptp
                    - rtsp
                    - dns-udp
                    - dns-tcp
                    - pmap
                    - rsh
                    - dcerpc
                    - mgcp
                    - gtp-c
                    - gtp-u
                    - gtp-b
            icmpcode:
                description:
                    - ICMP code.
            icmptype:
                description:
                    - ICMP type.
            iprange:
                description:
                    - Start and end of the IP range associated with service.
            name:
                description:
                    - Custom service name.
                required: true
            protocol:
                description:
                    - Protocol type based on IANA numbers.
                choices:
                    - TCP/UDP/SCTP
                    - ICMP
                    - ICMP6
                    - IP
                    - HTTP
                    - FTP
                    - CONNECT
                    - SOCKS-TCP
                    - SOCKS-UDP
                    - ALL
            protocol-number:
                description:
                    - IP protocol number.
            proxy:
                description:
                    - Enable/disable web proxy service.
                choices:
                    - enable
                    - disable
            sctp-portrange:
                description:
                    - Multiple SCTP port ranges.
            session-ttl:
                description:
                    - Session TTL (300 - 604800, 0 = default).
            tcp-halfclose-timer:
                description:
                    - Wait time to close a TCP session waiting for an unanswered FIN packet (1 - 86400 sec, 0 = default).
            tcp-halfopen-timer:
                description:
                    - Wait time to close a TCP session waiting for an unanswered open session packet (1 - 86400 sec, 0 = default).
            tcp-portrange:
                description:
                    - Multiple TCP port ranges.
            tcp-timewait-timer:
                description:
                    - Set the length of the TCP TIME-WAIT state in seconds (1 - 300 sec, 0 = default).
            udp-idle-timer:
                description:
                    - UDP half close timeout (0 - 86400 sec, 0 = default).
            udp-portrange:
                description:
                    - Multiple UDP port ranges.
            visibility:
                description:
                    - Enable/disable the visibility of the service on the GUI.
                choices:
                    - enable
                    - disable
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure custom services.
    fortios_firewall_service_custom:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_service_custom:
        state: "present"
        app-category:
         -
            id:  "4"
        app-service-type: "disable"
        application:
         -
            id:  "7"
        category: "<your_own_value> (source firewall.service.category.name)"
        check-reset-range: "disable"
        color: "10"
        comment: "Comment."
        fqdn: "<your_own_value>"
        helper: "auto"
        icmpcode: "14"
        icmptype: "15"
        iprange: "<your_own_value>"
        name: "default_name_17"
        protocol: "TCP/UDP/SCTP"
        protocol-number: "19"
        proxy: "enable"
        sctp-portrange: "<your_own_value>"
        session-ttl: "22"
        tcp-halfclose-timer: "23"
        tcp-halfopen-timer: "24"
        tcp-portrange: "<your_own_value>"
        tcp-timewait-timer: "26"
        udp-idle-timer: "27"
        udp-portrange: "<your_own_value>"
        visibility: "enable"
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


def filter_firewall_service_custom_data(json):
    option_list = ['app-category', 'app-service-type', 'application',
                   'category', 'check-reset-range', 'color',
                   'comment', 'fqdn', 'helper',
                   'icmpcode', 'icmptype', 'iprange',
                   'name', 'protocol', 'protocol-number',
                   'proxy', 'sctp-portrange', 'session-ttl',
                   'tcp-halfclose-timer', 'tcp-halfopen-timer', 'tcp-portrange',
                   'tcp-timewait-timer', 'udp-idle-timer', 'udp-portrange',
                   'visibility']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_service_custom(data, fos):
    vdom = data['vdom']
    firewall_service_custom_data = data['firewall_service_custom']
    filtered_data = filter_firewall_service_custom_data(firewall_service_custom_data)
    if firewall_service_custom_data['state'] == "present":
        return fos.set('firewall.service',
                       'custom',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_service_custom_data['state'] == "absent":
        return fos.delete('firewall.service',
                          'custom',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall_service(data, fos):
    login(data)

    methodlist = ['firewall_service_custom']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "firewall_service_custom": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "app-category": {"required": False, "type": "list",
                                 "options": {
                                     "id": {"required": True, "type": "int"}
                                 }},
                "app-service-type": {"required": False, "type": "str",
                                     "choices": ["disable", "app-id", "app-category"]},
                "application": {"required": False, "type": "list",
                                "options": {
                                    "id": {"required": True, "type": "int"}
                                }},
                "category": {"required": False, "type": "str"},
                "check-reset-range": {"required": False, "type": "str",
                                      "choices": ["disable", "strict", "default"]},
                "color": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "fqdn": {"required": False, "type": "str"},
                "helper": {"required": False, "type": "str",
                           "choices": ["auto", "disable", "ftp",
                                       "tftp", "ras", "h323",
                                       "tns", "mms", "sip",
                                       "pptp", "rtsp", "dns-udp",
                                       "dns-tcp", "pmap", "rsh",
                                       "dcerpc", "mgcp", "gtp-c",
                                       "gtp-u", "gtp-b"]},
                "icmpcode": {"required": False, "type": "int"},
                "icmptype": {"required": False, "type": "int"},
                "iprange": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "protocol": {"required": False, "type": "str",
                             "choices": ["TCP/UDP/SCTP", "ICMP", "ICMP6",
                                         "IP", "HTTP", "FTP",
                                         "CONNECT", "SOCKS-TCP", "SOCKS-UDP",
                                         "ALL"]},
                "protocol-number": {"required": False, "type": "int"},
                "proxy": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "sctp-portrange": {"required": False, "type": "str"},
                "session-ttl": {"required": False, "type": "int"},
                "tcp-halfclose-timer": {"required": False, "type": "int"},
                "tcp-halfopen-timer": {"required": False, "type": "int"},
                "tcp-portrange": {"required": False, "type": "str"},
                "tcp-timewait-timer": {"required": False, "type": "int"},
                "udp-idle-timer": {"required": False, "type": "int"},
                "udp-portrange": {"required": False, "type": "str"},
                "visibility": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]}

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

    is_error, has_changed, result = fortios_firewall_service(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
