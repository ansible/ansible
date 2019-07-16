#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2018 Fortinet, Inc.
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
module: fortios_firewall_vip46
short_description: Configure IPv4 to IPv6 virtual IPs in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and vip46 category.
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
        default: false
    firewall_vip46:
        description:
            - Configure IPv4 to IPv6 virtual IPs.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            arp-reply:
                description:
                    - Enable ARP reply.
                choices:
                    - disable
                    - enable
            color:
                description:
                    - Color of icon on the GUI.
            comment:
                description:
                    - Comment.
            extip:
                description:
                    - Start-external-IP [-end-external-IP].
            extport:
                description:
                    - External service port.
            id:
                description:
                    - Custom defined id.
            ldb-method:
                description:
                    - Load balance method.
                choices:
                    - static
                    - round-robin
                    - weighted
                    - least-session
                    - least-rtt
                    - first-alive
            mappedip:
                description:
                    - Start-mapped-IP [-end mapped-IP].
            mappedport:
                description:
                    - Mapped service port.
            monitor:
                description:
                    - Health monitors.
                suboptions:
                    name:
                        description:
                            - Health monitor name. Source firewall.ldb-monitor.name.
                        required: true
            name:
                description:
                    - VIP46 name.
                required: true
            portforward:
                description:
                    - Enable port forwarding.
                choices:
                    - disable
                    - enable
            protocol:
                description:
                    - Mapped port protocol.
                choices:
                    - tcp
                    - udp
            realservers:
                description:
                    - Real servers.
                suboptions:
                    client-ip:
                        description:
                            - Restrict server to a client IP in this range.
                    healthcheck:
                        description:
                            - Per server health check.
                        choices:
                            - disable
                            - enable
                            - vip
                    holddown-interval:
                        description:
                            - Hold down interval.
                    id:
                        description:
                            - Real server ID.
                        required: true
                    ip:
                        description:
                            - Mapped server IPv6.
                    max-connections:
                        description:
                            - Maximum number of connections allowed to server.
                    monitor:
                        description:
                            - Health monitors. Source firewall.ldb-monitor.name.
                    port:
                        description:
                            - Mapped server port.
                    status:
                        description:
                            - Server administrative status.
                        choices:
                            - active
                            - standby
                            - disable
                    weight:
                        description:
                            - weight
            server-type:
                description:
                    - Server type.
                choices:
                    - http
                    - tcp
                    - udp
                    - ip
            src-filter:
                description:
                    - Source IP filter (x.x.x.x/x).
                suboptions:
                    range:
                        description:
                            - Src-filter range.
                        required: true
            type:
                description:
                    - "VIP type: static NAT or server load balance."
                choices:
                    - static-nat
                    - server-load-balance
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPv4 to IPv6 virtual IPs.
    fortios_firewall_vip46:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_vip46:
        state: "present"
        arp-reply: "disable"
        color: "4"
        comment: "Comment."
        extip: "<your_own_value>"
        extport: "<your_own_value>"
        id:  "8"
        ldb-method: "static"
        mappedip: "<your_own_value>"
        mappedport: "<your_own_value>"
        monitor:
         -
            name: "default_name_13 (source firewall.ldb-monitor.name)"
        name: "default_name_14"
        portforward: "disable"
        protocol: "tcp"
        realservers:
         -
            client-ip: "<your_own_value>"
            healthcheck: "disable"
            holddown-interval: "20"
            id:  "21"
            ip: "<your_own_value>"
            max-connections: "23"
            monitor: "<your_own_value> (source firewall.ldb-monitor.name)"
            port: "25"
            status: "active"
            weight: "27"
        server-type: "http"
        src-filter:
         -
            range: "<your_own_value>"
        type: "static-nat"
        uuid: "<your_own_value>"
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
  sample: "key1"
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


def filter_firewall_vip46_data(json):
    option_list = ['arp-reply', 'color', 'comment',
                   'extip', 'extport', 'id',
                   'ldb-method', 'mappedip', 'mappedport',
                   'monitor', 'name', 'portforward',
                   'protocol', 'realservers', 'server-type',
                   'src-filter', 'type', 'uuid']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_vip46(data, fos):
    vdom = data['vdom']
    firewall_vip46_data = data['firewall_vip46']
    filtered_data = filter_firewall_vip46_data(firewall_vip46_data)
    if firewall_vip46_data['state'] == "present":
        return fos.set('firewall',
                       'vip46',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_vip46_data['state'] == "absent":
        return fos.delete('firewall',
                          'vip46',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_vip46']
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
        "https": {"required": False, "type": "bool", "default": "False"},
        "firewall_vip46": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "arp-reply": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "color": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "extip": {"required": False, "type": "str"},
                "extport": {"required": False, "type": "str"},
                "id": {"required": False, "type": "int"},
                "ldb-method": {"required": False, "type": "str",
                               "choices": ["static", "round-robin", "weighted",
                                           "least-session", "least-rtt", "first-alive"]},
                "mappedip": {"required": False, "type": "str"},
                "mappedport": {"required": False, "type": "str"},
                "monitor": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "name": {"required": True, "type": "str"},
                "portforward": {"required": False, "type": "str",
                                "choices": ["disable", "enable"]},
                "protocol": {"required": False, "type": "str",
                             "choices": ["tcp", "udp"]},
                "realservers": {"required": False, "type": "list",
                                "options": {
                                    "client-ip": {"required": False, "type": "str"},
                                    "healthcheck": {"required": False, "type": "str",
                                                    "choices": ["disable", "enable", "vip"]},
                                    "holddown-interval": {"required": False, "type": "int"},
                                    "id": {"required": True, "type": "int"},
                                    "ip": {"required": False, "type": "str"},
                                    "max-connections": {"required": False, "type": "int"},
                                    "monitor": {"required": False, "type": "str"},
                                    "port": {"required": False, "type": "int"},
                                    "status": {"required": False, "type": "str",
                                               "choices": ["active", "standby", "disable"]},
                                    "weight": {"required": False, "type": "int"}
                                }},
                "server-type": {"required": False, "type": "str",
                                "choices": ["http", "tcp", "udp",
                                            "ip"]},
                "src-filter": {"required": False, "type": "list",
                               "options": {
                                   "range": {"required": True, "type": "str"}
                               }},
                "type": {"required": False, "type": "str",
                         "choices": ["static-nat", "server-load-balance"]},
                "uuid": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
