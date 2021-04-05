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
module: fortios_user_radius
short_description: Configure RADIUS server entries in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify user feature and radius category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
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
        version_added: 2.9
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    user_radius:
        description:
            - Configure RADIUS server entries.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            accounting_server:
                description:
                    - Additional accounting servers.
                type: list
                suboptions:
                    id:
                        description:
                            - ID (0 - 4294967295).
                        required: true
                        type: int
                    port:
                        description:
                            - RADIUS accounting port number.
                        type: int
                    secret:
                        description:
                            - Secret key.
                        type: str
                    server:
                        description:
                            - name_str or ip_str Server CN domain name or IP.
                        type: str
                    source_ip:
                        description:
                            - Source IP address for communications to the RADIUS server.
                        type: str
                    status:
                        description:
                            - Status.
                        type: str
                        choices:
                            - enable
                            - disable
            acct_all_servers:
                description:
                    - Enable/disable sending of accounting messages to all configured servers.
                type: str
                choices:
                    - enable
                    - disable
            acct_interim_interval:
                description:
                    - Time in seconds between each accounting interim update message.
                type: int
            all_usergroup:
                description:
                    - Enable/disable automatically including this RADIUS server in all user groups.
                type: str
                choices:
                    - disable
                    - enable
            auth_type:
                description:
                    - Authentication methods/protocols permitted for this RADIUS server.
                type: str
                choices:
                    - auto
                    - ms_chap_v2
                    - ms_chap
                    - chap
                    - pap
            class:
                description:
                    - Class attribute name(s).
                type: list
                suboptions:
                    name:
                        description:
                            - Class name.
                        required: true
                        type: str
            h3c_compatibility:
                description:
                    - Enable/disable compatibility with the H3C, a mechanism that performs security checking for authentication.
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - RADIUS server entry name.
                required: true
                type: str
            nas_ip:
                description:
                    - IP address used to communicate with the RADIUS server and used as NAS-IP-Address and Called-Station-ID attributes.
                type: str
            password_encoding:
                description:
                    - Password encoding.
                type: str
                choices:
                    - auto
                    - ISO-8859-1
            password_renewal:
                description:
                    - Enable/disable password renewal.
                type: str
                choices:
                    - enable
                    - disable
            radius_coa:
                description:
                    - Enable to allow a mechanism to change the attributes of an authentication, authorization, and accounting session after it is
                       authenticated.
                type: str
                choices:
                    - enable
                    - disable
            radius_port:
                description:
                    - RADIUS service port number.
                type: int
            rsso:
                description:
                    - Enable/disable RADIUS based single sign on feature.
                type: str
                choices:
                    - enable
                    - disable
            rsso_context_timeout:
                description:
                    - Time in seconds before the logged out user is removed from the "user context list" of logged on users.
                type: int
            rsso_endpoint_attribute:
                description:
                    - RADIUS attributes used to extract the user end point identifier from the RADIUS Start record.
                type: str
                choices:
                    - User-Name
                    - NAS-IP-Address
                    - Framed-IP-Address
                    - Framed-IP-Netmask
                    - Filter-Id
                    - Login-IP-Host
                    - Reply-Message
                    - Callback-Number
                    - Callback-Id
                    - Framed-Route
                    - Framed-IPX-Network
                    - Class
                    - Called-Station-Id
                    - Calling-Station-Id
                    - NAS-Identifier
                    - Proxy-State
                    - Login-LAT-Service
                    - Login-LAT-Node
                    - Login-LAT-Group
                    - Framed-AppleTalk-Zone
                    - Acct-Session-Id
                    - Acct-Multi-Session-Id
            rsso_endpoint_block_attribute:
                description:
                    - RADIUS attributes used to block a user.
                type: str
                choices:
                    - User-Name
                    - NAS-IP-Address
                    - Framed-IP-Address
                    - Framed-IP-Netmask
                    - Filter-Id
                    - Login-IP-Host
                    - Reply-Message
                    - Callback-Number
                    - Callback-Id
                    - Framed-Route
                    - Framed-IPX-Network
                    - Class
                    - Called-Station-Id
                    - Calling-Station-Id
                    - NAS-Identifier
                    - Proxy-State
                    - Login-LAT-Service
                    - Login-LAT-Node
                    - Login-LAT-Group
                    - Framed-AppleTalk-Zone
                    - Acct-Session-Id
                    - Acct-Multi-Session-Id
            rsso_ep_one_ip_only:
                description:
                    - Enable/disable the replacement of old IP addresses with new ones for the same endpoint on RADIUS accounting Start messages.
                type: str
                choices:
                    - enable
                    - disable
            rsso_flush_ip_session:
                description:
                    - Enable/disable flushing user IP sessions on RADIUS accounting Stop messages.
                type: str
                choices:
                    - enable
                    - disable
            rsso_log_flags:
                description:
                    - Events to log.
                type: str
                choices:
                    - protocol-error
                    - profile-missing
                    - accounting-stop-missed
                    - accounting-event
                    - endpoint-block
                    - radiusd-other
                    - none
            rsso_log_period:
                description:
                    - Time interval in seconds that group event log messages will be generated for dynamic profile events.
                type: int
            rsso_radius_response:
                description:
                    - Enable/disable sending RADIUS response packets after receiving Start and Stop records.
                type: str
                choices:
                    - enable
                    - disable
            rsso_radius_server_port:
                description:
                    - UDP port to listen on for RADIUS Start and Stop records.
                type: int
            rsso_secret:
                description:
                    - RADIUS secret used by the RADIUS accounting server.
                type: str
            rsso_validate_request_secret:
                description:
                    - Enable/disable validating the RADIUS request shared secret in the Start or End record.
                type: str
                choices:
                    - enable
                    - disable
            secondary_secret:
                description:
                    - Secret key to access the secondary server.
                type: str
            secondary_server:
                description:
                    - name_str or ip_str secondary RADIUS CN domain name or IP.
                type: str
            secret:
                description:
                    - Pre-shared secret key used to access the primary RADIUS server.
                type: str
            server:
                description:
                    - Primary RADIUS server CN domain name or IP address.
                type: str
            source_ip:
                description:
                    - Source IP address for communications to the RADIUS server.
                type: str
            sso_attribute:
                description:
                    - RADIUS attribute that contains the profile group name to be extracted from the RADIUS Start record.
                type: str
                choices:
                    - User-Name
                    - NAS-IP-Address
                    - Framed-IP-Address
                    - Framed-IP-Netmask
                    - Filter-Id
                    - Login-IP-Host
                    - Reply-Message
                    - Callback-Number
                    - Callback-Id
                    - Framed-Route
                    - Framed-IPX-Network
                    - Class
                    - Called-Station-Id
                    - Calling-Station-Id
                    - NAS-Identifier
                    - Proxy-State
                    - Login-LAT-Service
                    - Login-LAT-Node
                    - Login-LAT-Group
                    - Framed-AppleTalk-Zone
                    - Acct-Session-Id
                    - Acct-Multi-Session-Id
            sso_attribute_key:
                description:
                    - Key prefix for SSO group value in the SSO attribute.
                type: str
            sso_attribute_value_override:
                description:
                    - Enable/disable override old attribute value with new value for the same endpoint.
                type: str
                choices:
                    - enable
                    - disable
            tertiary_secret:
                description:
                    - Secret key to access the tertiary server.
                type: str
            tertiary_server:
                description:
                    - name_str or ip_str tertiary RADIUS CN domain name or IP.
                type: str
            timeout:
                description:
                    - Time in seconds between re-sending authentication requests.
                type: int
            use_management_vdom:
                description:
                    - Enable/disable using management VDOM to send requests.
                type: str
                choices:
                    - enable
                    - disable
            username_case_sensitive:
                description:
                    - Enable/disable case sensitive user names.
                type: str
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
   ssl_verify: "False"
  tasks:
  - name: Configure RADIUS server entries.
    fortios_user_radius:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      user_radius:
        accounting_server:
         -
            id:  "4"
            port: "5"
            secret: "<your_own_value>"
            server: "192.168.100.40"
            source_ip: "84.230.14.43"
            status: "enable"
        acct_all_servers: "enable"
        acct_interim_interval: "11"
        all_usergroup: "disable"
        auth_type: "auto"
        class:
         -
            name: "default_name_15"
        h3c_compatibility: "enable"
        name: "default_name_17"
        nas_ip: "<your_own_value>"
        password_encoding: "auto"
        password_renewal: "enable"
        radius_coa: "enable"
        radius_port: "22"
        rsso: "enable"
        rsso_context_timeout: "24"
        rsso_endpoint_attribute: "User-Name"
        rsso_endpoint_block_attribute: "User-Name"
        rsso_ep_one_ip_only: "enable"
        rsso_flush_ip_session: "enable"
        rsso_log_flags: "protocol-error"
        rsso_log_period: "30"
        rsso_radius_response: "enable"
        rsso_radius_server_port: "32"
        rsso_secret: "<your_own_value>"
        rsso_validate_request_secret: "enable"
        secondary_secret: "<your_own_value>"
        secondary_server: "<your_own_value>"
        secret: "<your_own_value>"
        server: "192.168.100.40"
        source_ip: "84.230.14.43"
        sso_attribute: "User-Name"
        sso_attribute_key: "<your_own_value>"
        sso_attribute_value_override: "enable"
        tertiary_secret: "<your_own_value>"
        tertiary_server: "<your_own_value>"
        timeout: "45"
        use_management_vdom: "enable"
        username_case_sensitive: "enable"
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


def filter_user_radius_data(json):
    option_list = ['accounting_server', 'acct_all_servers', 'acct_interim_interval',
                   'all_usergroup', 'auth_type', 'class',
                   'h3c_compatibility', 'name', 'nas_ip',
                   'password_encoding', 'password_renewal', 'radius_coa',
                   'radius_port', 'rsso', 'rsso_context_timeout',
                   'rsso_endpoint_attribute', 'rsso_endpoint_block_attribute', 'rsso_ep_one_ip_only',
                   'rsso_flush_ip_session', 'rsso_log_flags', 'rsso_log_period',
                   'rsso_radius_response', 'rsso_radius_server_port', 'rsso_secret',
                   'rsso_validate_request_secret', 'secondary_secret', 'secondary_server',
                   'secret', 'server', 'source_ip',
                   'sso_attribute', 'sso_attribute_key', 'sso_attribute_value_override',
                   'tertiary_secret', 'tertiary_server', 'timeout',
                   'use_management_vdom', 'username_case_sensitive']
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


def user_radius(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['user_radius'] and data['user_radius']:
        state = data['user_radius']['state']
    else:
        state = True
    user_radius_data = data['user_radius']
    filtered_data = underscore_to_hyphen(filter_user_radius_data(user_radius_data))

    if state == "present":
        return fos.set('user',
                       'radius',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('user',
                          'radius',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_user(data, fos):

    if data['user_radius']:
        resp = user_radius(data, fos)

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
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "user_radius": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "accounting_server": {"required": False, "type": "list",
                                      "options": {
                                          "id": {"required": True, "type": "int"},
                                          "port": {"required": False, "type": "int"},
                                          "secret": {"required": False, "type": "str", "no_log": True},
                                          "server": {"required": False, "type": "str"},
                                          "source_ip": {"required": False, "type": "str"},
                                          "status": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]}
                                      }},
                "acct_all_servers": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "acct_interim_interval": {"required": False, "type": "int"},
                "all_usergroup": {"required": False, "type": "str",
                                  "choices": ["disable", "enable"]},
                "auth_type": {"required": False, "type": "str",
                              "choices": ["auto", "ms_chap_v2", "ms_chap",
                                          "chap", "pap"]},
                "class": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }},
                "h3c_compatibility": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "nas_ip": {"required": False, "type": "str"},
                "password_encoding": {"required": False, "type": "str",
                                      "choices": ["auto", "ISO-8859-1"]},
                "password_renewal": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "radius_coa": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "radius_port": {"required": False, "type": "int"},
                "rsso": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "rsso_context_timeout": {"required": False, "type": "int"},
                "rsso_endpoint_attribute": {"required": False, "type": "str",
                                            "choices": ["User-Name", "NAS-IP-Address", "Framed-IP-Address",
                                                        "Framed-IP-Netmask", "Filter-Id", "Login-IP-Host",
                                                        "Reply-Message", "Callback-Number", "Callback-Id",
                                                        "Framed-Route", "Framed-IPX-Network", "Class",
                                                        "Called-Station-Id", "Calling-Station-Id", "NAS-Identifier",
                                                        "Proxy-State", "Login-LAT-Service", "Login-LAT-Node",
                                                        "Login-LAT-Group", "Framed-AppleTalk-Zone", "Acct-Session-Id",
                                                        "Acct-Multi-Session-Id"]},
                "rsso_endpoint_block_attribute": {"required": False, "type": "str",
                                                  "choices": ["User-Name", "NAS-IP-Address", "Framed-IP-Address",
                                                              "Framed-IP-Netmask", "Filter-Id", "Login-IP-Host",
                                                              "Reply-Message", "Callback-Number", "Callback-Id",
                                                              "Framed-Route", "Framed-IPX-Network", "Class",
                                                              "Called-Station-Id", "Calling-Station-Id", "NAS-Identifier",
                                                              "Proxy-State", "Login-LAT-Service", "Login-LAT-Node",
                                                              "Login-LAT-Group", "Framed-AppleTalk-Zone", "Acct-Session-Id",
                                                              "Acct-Multi-Session-Id"]},
                "rsso_ep_one_ip_only": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "rsso_flush_ip_session": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "rsso_log_flags": {"required": False, "type": "str",
                                   "choices": ["protocol-error", "profile-missing", "accounting-stop-missed",
                                               "accounting-event", "endpoint-block", "radiusd-other",
                                               "none"]},
                "rsso_log_period": {"required": False, "type": "int"},
                "rsso_radius_response": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "rsso_radius_server_port": {"required": False, "type": "int"},
                "rsso_secret": {"required": False, "type": "str", "no_log": True},
                "rsso_validate_request_secret": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "secondary_secret": {"required": False, "type": "str", "no_log": True},
                "secondary_server": {"required": False, "type": "str"},
                "secret": {"required": False, "type": "str", "no_log": True},
                "server": {"required": False, "type": "str"},
                "source_ip": {"required": False, "type": "str"},
                "sso_attribute": {"required": False, "type": "str",
                                  "choices": ["User-Name", "NAS-IP-Address", "Framed-IP-Address",
                                              "Framed-IP-Netmask", "Filter-Id", "Login-IP-Host",
                                              "Reply-Message", "Callback-Number", "Callback-Id",
                                              "Framed-Route", "Framed-IPX-Network", "Class",
                                              "Called-Station-Id", "Calling-Station-Id", "NAS-Identifier",
                                              "Proxy-State", "Login-LAT-Service", "Login-LAT-Node",
                                              "Login-LAT-Group", "Framed-AppleTalk-Zone", "Acct-Session-Id",
                                              "Acct-Multi-Session-Id"]},
                "sso_attribute_key": {"required": False, "type": "str"},
                "sso_attribute_value_override": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "tertiary_secret": {"required": False, "type": "str", "no_log": True},
                "tertiary_server": {"required": False, "type": "str"},
                "timeout": {"required": False, "type": "int"},
                "use_management_vdom": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "username_case_sensitive": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]}

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

            is_error, has_changed, result = fortios_user(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_user(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
