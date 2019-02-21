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
module: fortios_user_radius
short_description: Configure RADIUS server entries in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify user feature and radius category.
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
    user_radius:
        description:
            - Configure RADIUS server entries.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            accounting-server:
                description:
                    - Additional accounting servers.
                suboptions:
                    id:
                        description:
                            - ID (0 - 4294967295).
                        required: true
                    port:
                        description:
                            - RADIUS accounting port number.
                    secret:
                        description:
                            - Secret key.
                    server:
                        description:
                            - Server CN domain name or IP.
                    source-ip:
                        description:
                            - Source IP address for communications to the RADIUS server.
                    status:
                        description:
                            - Status.
                        choices:
                            - enable
                            - disable
            acct-all-servers:
                description:
                    - Enable/disable sending of accounting messages to all configured servers (default = disable).
                choices:
                    - enable
                    - disable
            acct-interim-interval:
                description:
                    - Time in seconds between each accounting interim update message.
            all-usergroup:
                description:
                    - Enable/disable automatically including this RADIUS server in all user groups.
                choices:
                    - disable
                    - enable
            auth-type:
                description:
                    - Authentication methods/protocols permitted for this RADIUS server.
                choices:
                    - auto
                    - ms_chap_v2
                    - ms_chap
                    - chap
                    - pap
            class:
                description:
                    - Class attribute name(s).
                suboptions:
                    name:
                        description:
                            - Class name.
                        required: true
            h3c-compatibility:
                description:
                    - Enable/disable compatibility with the H3C, a mechanism that performs security checking for authentication.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - RADIUS server entry name.
                required: true
            nas-ip:
                description:
                    - IP address used to communicate with the RADIUS server and used as NAS-IP-Address and Called-Station-ID attributes.
            password-encoding:
                description:
                    - Password encoding.
                choices:
                    - auto
                    - ISO-8859-1
            password-renewal:
                description:
                    - Enable/disable password renewal.
                choices:
                    - enable
                    - disable
            radius-coa:
                description:
                    - Enable to allow a mechanism to change the attributes of an authentication, authorization, and accounting session after it is
                       authenticated.
                choices:
                    - enable
                    - disable
            radius-port:
                description:
                    - RADIUS service port number.
            rsso:
                description:
                    - Enable/disable RADIUS based single sign on feature.
                choices:
                    - enable
                    - disable
            rsso-context-timeout:
                description:
                    - Time in seconds before the logged out user is removed from the "user context list" of logged on users.
            rsso-endpoint-attribute:
                description:
                    - RADIUS attributes used to extract the user end point identifer from the RADIUS Start record.
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
            rsso-endpoint-block-attribute:
                description:
                    - RADIUS attributes used to block a user.
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
            rsso-ep-one-ip-only:
                description:
                    - Enable/disable the replacement of old IP addresses with new ones for the same endpoint on RADIUS accounting Start messages.
                choices:
                    - enable
                    - disable
            rsso-flush-ip-session:
                description:
                    - Enable/disable flushing user IP sessions on RADIUS accounting Stop messages.
                choices:
                    - enable
                    - disable
            rsso-log-flags:
                description:
                    - Events to log.
                choices:
                    - protocol-error
                    - profile-missing
                    - accounting-stop-missed
                    - accounting-event
                    - endpoint-block
                    - radiusd-other
                    - none
            rsso-log-period:
                description:
                    - Time interval in seconds that group event log messages will be generated for dynamic profile events.
            rsso-radius-response:
                description:
                    - Enable/disable sending RADIUS response packets after receiving Start and Stop records.
                choices:
                    - enable
                    - disable
            rsso-radius-server-port:
                description:
                    - UDP port to listen on for RADIUS Start and Stop records.
            rsso-secret:
                description:
                    - RADIUS secret used by the RADIUS accounting server.
            rsso-validate-request-secret:
                description:
                    - Enable/disable validating the RADIUS request shared secret in the Start or End record.
                choices:
                    - enable
                    - disable
            secondary-secret:
                description:
                    - Secret key to access the secondary server.
            secondary-server:
                description:
                    - Secondary RADIUS CN domain name or IP.
            secret:
                description:
                    - Pre-shared secret key used to access the primary RADIUS server.
            server:
                description:
                    - Primary RADIUS server CN domain name or IP address.
            source-ip:
                description:
                    - Source IP address for communications to the RADIUS server.
            sso-attribute:
                description:
                    - RADIUS attribute that contains the profile group name to be extracted from the RADIUS Start record.
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
            sso-attribute-key:
                description:
                    - Key prefix for SSO group value in the SSO attribute.
            sso-attribute-value-override:
                description:
                    - Enable/disable override old attribute value with new value for the same endpoint.
                choices:
                    - enable
                    - disable
            tertiary-secret:
                description:
                    - Secret key to access the tertiary server.
            tertiary-server:
                description:
                    - Tertiary RADIUS CN domain name or IP.
            timeout:
                description:
                    - Time in seconds between re-sending authentication requests.
            use-management-vdom:
                description:
                    - Enable/disable using management VDOM to send requests.
                choices:
                    - enable
                    - disable
            username-case-sensitive:
                description:
                    - Enable/disable case sensitive user names.
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
  - name: Configure RADIUS server entries.
    fortios_user_radius:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      user_radius:
        state: "present"
        accounting-server:
         -
            id:  "4"
            port: "5"
            secret: "<your_own_value>"
            server: "192.168.100.40"
            source-ip: "84.230.14.43"
            status: "enable"
        acct-all-servers: "enable"
        acct-interim-interval: "11"
        all-usergroup: "disable"
        auth-type: "auto"
        class:
         -
            name: "default_name_15"
        h3c-compatibility: "enable"
        name: "default_name_17"
        nas-ip: "<your_own_value>"
        password-encoding: "auto"
        password-renewal: "enable"
        radius-coa: "enable"
        radius-port: "22"
        rsso: "enable"
        rsso-context-timeout: "24"
        rsso-endpoint-attribute: "User-Name"
        rsso-endpoint-block-attribute: "User-Name"
        rsso-ep-one-ip-only: "enable"
        rsso-flush-ip-session: "enable"
        rsso-log-flags: "protocol-error"
        rsso-log-period: "30"
        rsso-radius-response: "enable"
        rsso-radius-server-port: "32"
        rsso-secret: "<your_own_value>"
        rsso-validate-request-secret: "enable"
        secondary-secret: "<your_own_value>"
        secondary-server: "<your_own_value>"
        secret: "<your_own_value>"
        server: "192.168.100.40"
        source-ip: "84.230.14.43"
        sso-attribute: "User-Name"
        sso-attribute-key: "<your_own_value>"
        sso-attribute-value-override: "enable"
        tertiary-secret: "<your_own_value>"
        tertiary-server: "<your_own_value>"
        timeout: "45"
        use-management-vdom: "enable"
        username-case-sensitive: "enable"
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


def filter_user_radius_data(json):
    option_list = ['accounting-server', 'acct-all-servers', 'acct-interim-interval',
                   'all-usergroup', 'auth-type', 'class',
                   'h3c-compatibility', 'name', 'nas-ip',
                   'password-encoding', 'password-renewal', 'radius-coa',
                   'radius-port', 'rsso', 'rsso-context-timeout',
                   'rsso-endpoint-attribute', 'rsso-endpoint-block-attribute', 'rsso-ep-one-ip-only',
                   'rsso-flush-ip-session', 'rsso-log-flags', 'rsso-log-period',
                   'rsso-radius-response', 'rsso-radius-server-port', 'rsso-secret',
                   'rsso-validate-request-secret', 'secondary-secret', 'secondary-server',
                   'secret', 'server', 'source-ip',
                   'sso-attribute', 'sso-attribute-key', 'sso-attribute-value-override',
                   'tertiary-secret', 'tertiary-server', 'timeout',
                   'use-management-vdom', 'username-case-sensitive']
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


def user_radius(data, fos):
    vdom = data['vdom']
    user_radius_data = data['user_radius']
    flattened_data = flatten_multilists_attributes(user_radius_data)
    filtered_data = filter_user_radius_data(flattened_data)
    if user_radius_data['state'] == "present":
        return fos.set('user',
                       'radius',
                       data=filtered_data,
                       vdom=vdom)

    elif user_radius_data['state'] == "absent":
        return fos.delete('user',
                          'radius',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_user(data, fos):
    login(data)

    if data['user_radius']:
        resp = user_radius(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "user_radius": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "accounting-server": {"required": False, "type": "list",
                                      "options": {
                                          "id": {"required": True, "type": "int"},
                                          "port": {"required": False, "type": "int"},
                                          "secret": {"required": False, "type": "str"},
                                          "server": {"required": False, "type": "str"},
                                          "source-ip": {"required": False, "type": "str"},
                                          "status": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]}
                                      }},
                "acct-all-servers": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "acct-interim-interval": {"required": False, "type": "int"},
                "all-usergroup": {"required": False, "type": "str",
                                  "choices": ["disable", "enable"]},
                "auth-type": {"required": False, "type": "str",
                              "choices": ["auto", "ms_chap_v2", "ms_chap",
                                          "chap", "pap"]},
                "class": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }},
                "h3c-compatibility": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "nas-ip": {"required": False, "type": "str"},
                "password-encoding": {"required": False, "type": "str",
                                      "choices": ["auto", "ISO-8859-1"]},
                "password-renewal": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "radius-coa": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "radius-port": {"required": False, "type": "int"},
                "rsso": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "rsso-context-timeout": {"required": False, "type": "int"},
                "rsso-endpoint-attribute": {"required": False, "type": "str",
                                            "choices": ["User-Name", "NAS-IP-Address", "Framed-IP-Address",
                                                        "Framed-IP-Netmask", "Filter-Id", "Login-IP-Host",
                                                        "Reply-Message", "Callback-Number", "Callback-Id",
                                                        "Framed-Route", "Framed-IPX-Network", "Class",
                                                        "Called-Station-Id", "Calling-Station-Id", "NAS-Identifier",
                                                        "Proxy-State", "Login-LAT-Service", "Login-LAT-Node",
                                                        "Login-LAT-Group", "Framed-AppleTalk-Zone", "Acct-Session-Id",
                                                        "Acct-Multi-Session-Id"]},
                "rsso-endpoint-block-attribute": {"required": False, "type": "str",
                                                  "choices": ["User-Name", "NAS-IP-Address", "Framed-IP-Address",
                                                              "Framed-IP-Netmask", "Filter-Id", "Login-IP-Host",
                                                              "Reply-Message", "Callback-Number", "Callback-Id",
                                                              "Framed-Route", "Framed-IPX-Network", "Class",
                                                              "Called-Station-Id", "Calling-Station-Id", "NAS-Identifier",
                                                              "Proxy-State", "Login-LAT-Service", "Login-LAT-Node",
                                                              "Login-LAT-Group", "Framed-AppleTalk-Zone", "Acct-Session-Id",
                                                              "Acct-Multi-Session-Id"]},
                "rsso-ep-one-ip-only": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "rsso-flush-ip-session": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "rsso-log-flags": {"required": False, "type": "str",
                                   "choices": ["protocol-error", "profile-missing", "accounting-stop-missed",
                                               "accounting-event", "endpoint-block", "radiusd-other",
                                               "none"]},
                "rsso-log-period": {"required": False, "type": "int"},
                "rsso-radius-response": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "rsso-radius-server-port": {"required": False, "type": "int"},
                "rsso-secret": {"required": False, "type": "str"},
                "rsso-validate-request-secret": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "secondary-secret": {"required": False, "type": "str"},
                "secondary-server": {"required": False, "type": "str"},
                "secret": {"required": False, "type": "str"},
                "server": {"required": False, "type": "str"},
                "source-ip": {"required": False, "type": "str"},
                "sso-attribute": {"required": False, "type": "str",
                                  "choices": ["User-Name", "NAS-IP-Address", "Framed-IP-Address",
                                              "Framed-IP-Netmask", "Filter-Id", "Login-IP-Host",
                                              "Reply-Message", "Callback-Number", "Callback-Id",
                                              "Framed-Route", "Framed-IPX-Network", "Class",
                                              "Called-Station-Id", "Calling-Station-Id", "NAS-Identifier",
                                              "Proxy-State", "Login-LAT-Service", "Login-LAT-Node",
                                              "Login-LAT-Group", "Framed-AppleTalk-Zone", "Acct-Session-Id",
                                              "Acct-Multi-Session-Id"]},
                "sso-attribute-key": {"required": False, "type": "str"},
                "sso-attribute-value-override": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "tertiary-secret": {"required": False, "type": "str"},
                "tertiary-server": {"required": False, "type": "str"},
                "timeout": {"required": False, "type": "int"},
                "use-management-vdom": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "username-case-sensitive": {"required": False, "type": "str",
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

    is_error, has_changed, result = fortios_user(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
