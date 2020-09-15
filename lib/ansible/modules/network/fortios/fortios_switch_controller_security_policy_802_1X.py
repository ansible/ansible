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

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_switch_controller_security_policy_802_1X
short_description: Configure 802.1x MAC Authentication Bypass (MAB) policies in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify switch_controller_security_policy feature and 802_1X category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.9"
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
            - FortiOS or FortiGate IP address.
        type: str
        required: false
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: false
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
    state:
        description:
            - Indicates whether to create or remove the object.
        type: str
        required: true
        choices:
            - present
            - absent
    switch_controller_security_policy_802_1X:
        description:
            - Configure 802.1x MAC Authentication Bypass (MAB) policies.
        default: null
        type: dict
        suboptions:
            auth_fail_vlan:
                description:
                    - Enable to allow limited access to clients that cannot authenticate.
                type: str
                choices:
                    - disable
                    - enable
            auth_fail_vlan_id:
                description:
                    - VLAN ID on which authentication failed. Source system.interface.name.
                type: str
            auth_fail_vlanid:
                description:
                    - VLAN ID on which authentication failed.
                type: int
            eap_passthru:
                description:
                    - Enable/disable EAP pass-through mode, allowing protocols (such as LLDP) to pass through ports for more flexible authentication.
                type: str
                choices:
                    - disable
                    - enable
            guest_auth_delay:
                description:
                    - Guest authentication delay (1 - 900  sec).
                type: int
            guest_vlan:
                description:
                    - Enable the guest VLAN feature to allow limited access to non-802.1X-compliant clients.
                type: str
                choices:
                    - disable
                    - enable
            guest_vlan_id:
                description:
                    - Guest VLAN name. Source system.interface.name.
                type: str
            guest_vlanid:
                description:
                    - Guest VLAN ID.
                type: int
            mac_auth_bypass:
                description:
                    - Enable/disable MAB for this policy.
                type: str
                choices:
                    - disable
                    - enable
            name:
                description:
                    - Policy name.
                required: true
                type: str
            open_auth:
                description:
                    - Enable/disable open authentication for this policy.
                type: str
                choices:
                    - disable
                    - enable
            policy_type:
                description:
                    - Policy type.
                type: str
                choices:
                    - 802.1X
            radius_timeout_overwrite:
                description:
                    - Enable to override the global RADIUS session timeout.
                type: str
                choices:
                    - disable
                    - enable
            security_mode:
                description:
                    - Port or MAC based 802.1X security mode.
                type: str
                choices:
                    - 802.1X
                    - 802.1X-mac-based
            user_group:
                description:
                    - Name of user-group to assign to this MAC Authentication Bypass (MAB) policy.
                type: list
                suboptions:
                    name:
                        description:
                            - Group name. Source user.group.name.
                        required: true
                        type: str
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
   ssl_verify: "False"
  tasks:
  - name: Configure 802.1x MAC Authentication Bypass (MAB) policies.
    fortios_switch_controller_security_policy_802_1X:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      switch_controller_security_policy_802_1X:
        auth_fail_vlan: "disable"
        auth_fail_vlan_id: "<your_own_value> (source system.interface.name)"
        auth_fail_vlanid: "5"
        eap_passthru: "disable"
        guest_auth_delay: "7"
        guest_vlan: "disable"
        guest_vlan_id: "<your_own_value> (source system.interface.name)"
        guest_vlanid: "10"
        mac_auth_bypass: "disable"
        name: "default_name_12"
        open_auth: "disable"
        policy_type: "802.1X"
        radius_timeout_overwrite: "disable"
        security_mode: "802.1X"
        user_group:
         -
            name: "default_name_18 (source user.group.name)"
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
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortios.fortios import FortiOSHandler
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def filter_switch_controller_security_policy_802_1X_data(json):
    option_list = ['auth_fail_vlan', 'auth_fail_vlan_id', 'auth_fail_vlanid',
                   'eap_passthru', 'guest_auth_delay', 'guest_vlan',
                   'guest_vlan_id', 'guest_vlanid', 'mac_auth_bypass',
                   'name', 'open_auth', 'policy_type',
                   'radius_timeout_overwrite', 'security_mode', 'user_group']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def underscore_to_hyphen(data):
    if isinstance(data, list):
        for elem in data:
            elem = underscore_to_hyphen(elem)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k.replace('_', '-')] = underscore_to_hyphen(v)
        data = new_data

    return data


def switch_controller_security_policy_802_1X(data, fos):
    vdom = data['vdom']
    state = data['state']
    switch_controller_security_policy_802_1X_data = data['switch_controller_security_policy_802_1X']
    filtered_data = underscore_to_hyphen(filter_switch_controller_security_policy_802_1X_data(switch_controller_security_policy_802_1X_data))

    if state == "present":
        return fos.set('switch-controller.security-policy',
                       '802-1X',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('switch-controller.security-policy',
                          '802-1X',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_switch_controller_security_policy(data, fos):

    if data['switch_controller_security_policy_802_1X']:
        resp = switch_controller_security_policy_802_1X(data, fos)

    return not is_successful_status(resp), \
        resp['status'] == "success", \
        resp


def main():
    fields = {
        "host": {"required": False, "type": "str"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "default": "", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": True},
        "state": {"required": True, "type": "str",
                  "choices": ["present", "absent"]},
        "switch_controller_security_policy_802_1X": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "auth_fail_vlan": {"required": False, "type": "str",
                                   "choices": ["disable", "enable"]},
                "auth_fail_vlan_id": {"required": False, "type": "str"},
                "auth_fail_vlanid": {"required": False, "type": "int"},
                "eap_passthru": {"required": False, "type": "str",
                                 "choices": ["disable", "enable"]},
                "guest_auth_delay": {"required": False, "type": "int"},
                "guest_vlan": {"required": False, "type": "str",
                               "choices": ["disable", "enable"]},
                "guest_vlan_id": {"required": False, "type": "str"},
                "guest_vlanid": {"required": False, "type": "int"},
                "mac_auth_bypass": {"required": False, "type": "str",
                                    "choices": ["disable", "enable"]},
                "name": {"required": True, "type": "str"},
                "open_auth": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "policy_type": {"required": False, "type": "str",
                                "choices": ["802.1X"]},
                "radius_timeout_overwrite": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                "security_mode": {"required": False, "type": "str",
                                  "choices": ["802.1X", "802.1X-mac-based"]},
                "user_group": {"required": False, "type": "list",
                               "options": {
                                   "name": {"required": True, "type": "str"}
                               }}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_switch_controller_security_policy(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_switch_controller_security_policy(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
