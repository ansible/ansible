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
module: fortios_switch_controller_lldp_profile
short_description: Configure FortiSwitch LLDP profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify switch_controller feature and lldp_profile category.
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
    switch_controller_lldp_profile:
        description:
            - Configure FortiSwitch LLDP profiles.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            802.1-tlvs:
                description:
                    - Transmitted IEEE 802.1 TLVs.
                choices:
                    - port-vlan-id
            802.3-tlvs:
                description:
                    - Transmitted IEEE 802.3 TLVs.
                choices:
                    - max-frame-size
            auto-isl:
                description:
                    - Enable/disable auto inter-switch LAG.
                choices:
                    - disable
                    - enable
            auto-isl-hello-timer:
                description:
                    - Auto inter-switch LAG hello timer duration (1 - 30 sec, default = 3).
            auto-isl-port-group:
                description:
                    - Auto inter-switch LAG port group ID (0 - 9).
            auto-isl-receive-timeout:
                description:
                    - Auto inter-switch LAG timeout if no response is received (3 - 90 sec, default = 9).
            custom-tlvs:
                description:
                    - Configuration method to edit custom TLV entries.
                suboptions:
                    information-string:
                        description:
                            - Organizationally defined information string (0 - 507 hexadecimal bytes).
                    name:
                        description:
                            - TLV name (not sent).
                        required: true
                    oui:
                        description:
                            - Organizationally unique identifier (OUI), a 3-byte hexadecimal number, for this TLV.
                    subtype:
                        description:
                            - Organizationally defined subtype (0 - 255).
            med-network-policy:
                description:
                    - Configuration method to edit Media Endpoint Discovery (MED) network policy type-length-value (TLV) categories.
                suboptions:
                    dscp:
                        description:
                            - Advertised Differentiated Services Code Point (DSCP) value, a packet header value indicating the level of service requested for
                               traffic, such as high priority or best effort delivery.
                    name:
                        description:
                            - Policy type name.
                        required: true
                    priority:
                        description:
                            - Advertised Layer 2 priority (0 - 7; from lowest to highest priority).
                    status:
                        description:
                            - Enable or disable this TLV.
                        choices:
                            - disable
                            - enable
                    vlan:
                        description:
                            - ID of VLAN to advertise, if configured on port (0 - 4094, 0 = priority tag).
            med-tlvs:
                description:
                    - "Transmitted LLDP-MED TLVs (type-length-value descriptions): inventory management TLV and/or network policy TLV."
                choices:
                    - inventory-management
                    - network-policy
            name:
                description:
                    - Profile name.
                required: true
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure FortiSwitch LLDP profiles.
    fortios_switch_controller_lldp_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      switch_controller_lldp_profile:
        state: "present"
        802.1-tlvs: "port-vlan-id"
        802.3-tlvs: "max-frame-size"
        auto-isl: "disable"
        auto-isl-hello-timer: "6"
        auto-isl-port-group: "7"
        auto-isl-receive-timeout: "8"
        custom-tlvs:
         -
            information-string: "<your_own_value>"
            name: "default_name_11"
            oui: "<your_own_value>"
            subtype: "13"
        med-network-policy:
         -
            dscp: "15"
            name: "default_name_16"
            priority: "17"
            status: "disable"
            vlan: "19"
        med-tlvs: "inventory-management"
        name: "default_name_21"
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


def filter_switch_controller_lldp_profile_data(json):
    option_list = ['802.1-tlvs', '802.3-tlvs', 'auto-isl',
                   'auto-isl-hello-timer', 'auto-isl-port-group', 'auto-isl-receive-timeout',
                   'custom-tlvs', 'med-network-policy', 'med-tlvs',
                   'name']
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


def switch_controller_lldp_profile(data, fos):
    vdom = data['vdom']
    switch_controller_lldp_profile_data = data['switch_controller_lldp_profile']
    flattened_data = flatten_multilists_attributes(switch_controller_lldp_profile_data)
    filtered_data = filter_switch_controller_lldp_profile_data(flattened_data)
    if switch_controller_lldp_profile_data['state'] == "present":
        return fos.set('switch-controller',
                       'lldp-profile',
                       data=filtered_data,
                       vdom=vdom)

    elif switch_controller_lldp_profile_data['state'] == "absent":
        return fos.delete('switch-controller',
                          'lldp-profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_switch_controller(data, fos):
    login(data)

    if data['switch_controller_lldp_profile']:
        resp = switch_controller_lldp_profile(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "switch_controller_lldp_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "802.1-tlvs": {"required": False, "type": "str",
                               "choices": ["port-vlan-id"]},
                "802.3-tlvs": {"required": False, "type": "str",
                               "choices": ["max-frame-size"]},
                "auto-isl": {"required": False, "type": "str",
                             "choices": ["disable", "enable"]},
                "auto-isl-hello-timer": {"required": False, "type": "int"},
                "auto-isl-port-group": {"required": False, "type": "int"},
                "auto-isl-receive-timeout": {"required": False, "type": "int"},
                "custom-tlvs": {"required": False, "type": "list",
                                "options": {
                                    "information-string": {"required": False, "type": "str"},
                                    "name": {"required": True, "type": "str"},
                                    "oui": {"required": False, "type": "str"},
                                    "subtype": {"required": False, "type": "int"}
                                }},
                "med-network-policy": {"required": False, "type": "list",
                                       "options": {
                                           "dscp": {"required": False, "type": "int"},
                                           "name": {"required": True, "type": "str"},
                                           "priority": {"required": False, "type": "int"},
                                           "status": {"required": False, "type": "str",
                                                      "choices": ["disable", "enable"]},
                                           "vlan": {"required": False, "type": "int"}
                                       }},
                "med-tlvs": {"required": False, "type": "str",
                             "choices": ["inventory-management", "network-policy"]},
                "name": {"required": True, "type": "str"}

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

    is_error, has_changed, result = fortios_switch_controller(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
