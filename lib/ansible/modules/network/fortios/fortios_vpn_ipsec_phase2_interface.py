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
module: fortios_vpn_ipsec_phase2_interface
short_description: Configure VPN autokey tunnel in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify vpn_ipsec feature and phase2_interface category.
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
    vpn_ipsec_phase2_interface:
        description:
            - Configure VPN autokey tunnel.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            add-route:
                description:
                    - Enable/disable automatic route addition.
                choices:
                    - phase1
                    - enable
                    - disable
            auto-discovery-forwarder:
                description:
                    - Enable/disable forwarding short-cut messages.
                choices:
                    - phase1
                    - enable
                    - disable
            auto-discovery-sender:
                description:
                    - Enable/disable sending short-cut messages.
                choices:
                    - phase1
                    - enable
                    - disable
            auto-negotiate:
                description:
                    - Enable/disable IPsec SA auto-negotiation.
                choices:
                    - enable
                    - disable
            comments:
                description:
                    - Comment.
            dhcp-ipsec:
                description:
                    - Enable/disable DHCP-IPsec.
                choices:
                    - enable
                    - disable
            dhgrp:
                description:
                    - Phase2 DH group.
                choices:
                    - 1
                    - 2
                    - 5
                    - 14
                    - 15
                    - 16
                    - 17
                    - 18
                    - 19
                    - 20
                    - 21
                    - 27
                    - 28
                    - 29
                    - 30
                    - 31
            dst-addr-type:
                description:
                    - Remote proxy ID type.
                choices:
                    - subnet
                    - range
                    - ip
                    - name
                    - subnet6
                    - range6
                    - ip6
                    - name6
            dst-end-ip:
                description:
                    - Remote proxy ID IPv4 end.
            dst-end-ip6:
                description:
                    - Remote proxy ID IPv6 end.
            dst-name:
                description:
                    - Remote proxy ID name. Source firewall.address.name firewall.addrgrp.name.
            dst-name6:
                description:
                    - Remote proxy ID name. Source firewall.address6.name firewall.addrgrp6.name.
            dst-port:
                description:
                    - Quick mode destination port (1 - 65535 or 0 for all).
            dst-start-ip:
                description:
                    - Remote proxy ID IPv4 start.
            dst-start-ip6:
                description:
                    - Remote proxy ID IPv6 start.
            dst-subnet:
                description:
                    - Remote proxy ID IPv4 subnet.
            dst-subnet6:
                description:
                    - Remote proxy ID IPv6 subnet.
            encapsulation:
                description:
                    - ESP encapsulation mode.
                choices:
                    - tunnel-mode
                    - transport-mode
            keepalive:
                description:
                    - Enable/disable keep alive.
                choices:
                    - enable
                    - disable
            keylife-type:
                description:
                    - Keylife type.
                choices:
                    - seconds
                    - kbs
                    - both
            keylifekbs:
                description:
                    - Phase2 key life in number of bytes of traffic (5120 - 4294967295).
            keylifeseconds:
                description:
                    - Phase2 key life in time in seconds (120 - 172800).
            l2tp:
                description:
                    - Enable/disable L2TP over IPsec.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - IPsec tunnel name.
                required: true
            pfs:
                description:
                    - Enable/disable PFS feature.
                choices:
                    - enable
                    - disable
            phase1name:
                description:
                    - Phase 1 determines the options required for phase 2. Source vpn.ipsec.phase1-interface.name.
            proposal:
                description:
                    - Phase2 proposal.
                choices:
                    - null-md5
                    - null-sha1
                    - null-sha256
                    - null-sha384
                    - null-sha512
                    - des-null
                    - des-md5
                    - des-sha1
                    - des-sha256
                    - des-sha384
                    - des-sha512
            protocol:
                description:
                    - Quick mode protocol selector (1 - 255 or 0 for all).
            replay:
                description:
                    - Enable/disable replay detection.
                choices:
                    - enable
                    - disable
            route-overlap:
                description:
                    - Action for overlapping routes.
                choices:
                    - use-old
                    - use-new
                    - allow
            single-source:
                description:
                    - Enable/disable single source IP restriction.
                choices:
                    - enable
                    - disable
            src-addr-type:
                description:
                    - Local proxy ID type.
                choices:
                    - subnet
                    - range
                    - ip
                    - name
                    - subnet6
                    - range6
                    - ip6
                    - name6
            src-end-ip:
                description:
                    - Local proxy ID end.
            src-end-ip6:
                description:
                    - Local proxy ID IPv6 end.
            src-name:
                description:
                    - Local proxy ID name. Source firewall.address.name firewall.addrgrp.name.
            src-name6:
                description:
                    - Local proxy ID name. Source firewall.address6.name firewall.addrgrp6.name.
            src-port:
                description:
                    - Quick mode source port (1 - 65535 or 0 for all).
            src-start-ip:
                description:
                    - Local proxy ID start.
            src-start-ip6:
                description:
                    - Local proxy ID IPv6 start.
            src-subnet:
                description:
                    - Local proxy ID subnet.
            src-subnet6:
                description:
                    - Local proxy ID IPv6 subnet.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure VPN autokey tunnel.
    fortios_vpn_ipsec_phase2_interface:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      vpn_ipsec_phase2_interface:
        state: "present"
        add-route: "phase1"
        auto-discovery-forwarder: "phase1"
        auto-discovery-sender: "phase1"
        auto-negotiate: "enable"
        comments: "<your_own_value>"
        dhcp-ipsec: "enable"
        dhgrp: "1"
        dst-addr-type: "subnet"
        dst-end-ip: "<your_own_value>"
        dst-end-ip6: "<your_own_value>"
        dst-name: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
        dst-name6: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
        dst-port: "15"
        dst-start-ip: "<your_own_value>"
        dst-start-ip6: "<your_own_value>"
        dst-subnet: "<your_own_value>"
        dst-subnet6: "<your_own_value>"
        encapsulation: "tunnel-mode"
        keepalive: "enable"
        keylife-type: "seconds"
        keylifekbs: "23"
        keylifeseconds: "24"
        l2tp: "enable"
        name: "default_name_26"
        pfs: "enable"
        phase1name: "<your_own_value> (source vpn.ipsec.phase1-interface.name)"
        proposal: "null-md5"
        protocol: "30"
        replay: "enable"
        route-overlap: "use-old"
        single-source: "enable"
        src-addr-type: "subnet"
        src-end-ip: "<your_own_value>"
        src-end-ip6: "<your_own_value>"
        src-name: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
        src-name6: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
        src-port: "39"
        src-start-ip: "<your_own_value>"
        src-start-ip6: "<your_own_value>"
        src-subnet: "<your_own_value>"
        src-subnet6: "<your_own_value>"
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


def filter_vpn_ipsec_phase2_interface_data(json):
    option_list = ['add-route', 'auto-discovery-forwarder', 'auto-discovery-sender',
                   'auto-negotiate', 'comments', 'dhcp-ipsec',
                   'dhgrp', 'dst-addr-type', 'dst-end-ip',
                   'dst-end-ip6', 'dst-name', 'dst-name6',
                   'dst-port', 'dst-start-ip', 'dst-start-ip6',
                   'dst-subnet', 'dst-subnet6', 'encapsulation',
                   'keepalive', 'keylife-type', 'keylifekbs',
                   'keylifeseconds', 'l2tp', 'name',
                   'pfs', 'phase1name', 'proposal',
                   'protocol', 'replay', 'route-overlap',
                   'single-source', 'src-addr-type', 'src-end-ip',
                   'src-end-ip6', 'src-name', 'src-name6',
                   'src-port', 'src-start-ip', 'src-start-ip6',
                   'src-subnet', 'src-subnet6']
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


def vpn_ipsec_phase2_interface(data, fos):
    vdom = data['vdom']
    vpn_ipsec_phase2_interface_data = data['vpn_ipsec_phase2_interface']
    flattened_data = flatten_multilists_attributes(vpn_ipsec_phase2_interface_data)
    filtered_data = filter_vpn_ipsec_phase2_interface_data(flattened_data)
    if vpn_ipsec_phase2_interface_data['state'] == "present":
        return fos.set('vpn.ipsec',
                       'phase2-interface',
                       data=filtered_data,
                       vdom=vdom)

    elif vpn_ipsec_phase2_interface_data['state'] == "absent":
        return fos.delete('vpn.ipsec',
                          'phase2-interface',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_vpn_ipsec(data, fos):
    login(data)

    if data['vpn_ipsec_phase2_interface']:
        resp = vpn_ipsec_phase2_interface(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "vpn_ipsec_phase2_interface": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "add-route": {"required": False, "type": "str",
                              "choices": ["phase1", "enable", "disable"]},
                "auto-discovery-forwarder": {"required": False, "type": "str",
                                             "choices": ["phase1", "enable", "disable"]},
                "auto-discovery-sender": {"required": False, "type": "str",
                                          "choices": ["phase1", "enable", "disable"]},
                "auto-negotiate": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "comments": {"required": False, "type": "str"},
                "dhcp-ipsec": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "dhgrp": {"required": False, "type": "str",
                          "choices": ["1", "2", "5",
                                      "14", "15", "16",
                                      "17", "18", "19",
                                      "20", "21", "27",
                                      "28", "29", "30",
                                      "31"]},
                "dst-addr-type": {"required": False, "type": "str",
                                  "choices": ["subnet", "range", "ip",
                                              "name", "subnet6", "range6",
                                              "ip6", "name6"]},
                "dst-end-ip": {"required": False, "type": "str"},
                "dst-end-ip6": {"required": False, "type": "str"},
                "dst-name": {"required": False, "type": "str"},
                "dst-name6": {"required": False, "type": "str"},
                "dst-port": {"required": False, "type": "int"},
                "dst-start-ip": {"required": False, "type": "str"},
                "dst-start-ip6": {"required": False, "type": "str"},
                "dst-subnet": {"required": False, "type": "str"},
                "dst-subnet6": {"required": False, "type": "str"},
                "encapsulation": {"required": False, "type": "str",
                                  "choices": ["tunnel-mode", "transport-mode"]},
                "keepalive": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "keylife-type": {"required": False, "type": "str",
                                 "choices": ["seconds", "kbs", "both"]},
                "keylifekbs": {"required": False, "type": "int"},
                "keylifeseconds": {"required": False, "type": "int"},
                "l2tp": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "pfs": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "phase1name": {"required": False, "type": "str"},
                "proposal": {"required": False, "type": "str",
                             "choices": ["null-md5", "null-sha1", "null-sha256",
                                         "null-sha384", "null-sha512", "des-null",
                                         "des-md5", "des-sha1", "des-sha256",
                                         "des-sha384", "des-sha512"]},
                "protocol": {"required": False, "type": "int"},
                "replay": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "route-overlap": {"required": False, "type": "str",
                                  "choices": ["use-old", "use-new", "allow"]},
                "single-source": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "src-addr-type": {"required": False, "type": "str",
                                  "choices": ["subnet", "range", "ip",
                                              "name", "subnet6", "range6",
                                              "ip6", "name6"]},
                "src-end-ip": {"required": False, "type": "str"},
                "src-end-ip6": {"required": False, "type": "str"},
                "src-name": {"required": False, "type": "str"},
                "src-name6": {"required": False, "type": "str"},
                "src-port": {"required": False, "type": "int"},
                "src-start-ip": {"required": False, "type": "str"},
                "src-start-ip6": {"required": False, "type": "str"},
                "src-subnet": {"required": False, "type": "str"},
                "src-subnet6": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_vpn_ipsec(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
