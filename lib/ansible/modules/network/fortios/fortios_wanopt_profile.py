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
module: fortios_wanopt_profile
short_description: Configure WAN optimization profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wanopt feature and profile category.
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
    wanopt_profile:
        description:
            - Configure WAN optimization profiles.
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
            auth_group:
                description:
                    - Optionally add an authentication group to restrict access to the WAN Optimization tunnel to peers in the authentication group. Source
                       wanopt.auth-group.name.
                type: str
            cifs:
                description:
                    - Enable/disable CIFS (Windows sharing) WAN Optimization and configure CIFS WAN Optimization features.
                type: dict
                suboptions:
                    byte_caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        type: str
                        choices:
                            - enable
                            - disable
                    log_traffic:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for CIFS. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                        type: int
                    prefer_chunking:
                        description:
                            - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
                        type: str
                        choices:
                            - dynamic
                            - fix
                    secure_tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        type: str
                        choices:
                            - enable
                            - disable
                    tunnel_sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        type: str
                        choices:
                            - private
                            - shared
                            - express-shared
            comments:
                description:
                    - Comment.
                type: str
            ftp:
                description:
                    - Enable/disable FTP WAN Optimization and configure FTP WAN Optimization features.
                type: dict
                suboptions:
                    byte_caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        type: str
                        choices:
                            - enable
                            - disable
                    log_traffic:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for FTP. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                        type: int
                    prefer_chunking:
                        description:
                            - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
                        type: str
                        choices:
                            - dynamic
                            - fix
                    secure_tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        type: str
                        choices:
                            - enable
                            - disable
                    tunnel_sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        type: str
                        choices:
                            - private
                            - shared
                            - express-shared
            http:
                description:
                    - Enable/disable HTTP WAN Optimization and configure HTTP WAN Optimization features.
                type: dict
                suboptions:
                    byte_caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        type: str
                        choices:
                            - enable
                            - disable
                    log_traffic:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for HTTP. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                        type: int
                    prefer_chunking:
                        description:
                            - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
                        type: str
                        choices:
                            - dynamic
                            - fix
                    secure_tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        type: str
                        choices:
                            - enable
                            - disable
                    ssl:
                        description:
                            - Enable/disable SSL/TLS offloading (hardware acceleration) for HTTPS traffic in this tunnel.
                        type: str
                        choices:
                            - enable
                            - disable
                    ssl_port:
                        description:
                            - Port on which to expect HTTPS traffic for SSL/TLS offloading.
                        type: int
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        type: str
                        choices:
                            - enable
                            - disable
                    tunnel_non_http:
                        description:
                            - Configure how to process non-HTTP traffic when a profile configured for HTTP traffic accepts a non-HTTP session. Can occur if an
                               application sends non-HTTP traffic using an HTTP destination port.
                        type: str
                        choices:
                            - enable
                            - disable
                    tunnel_sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        type: str
                        choices:
                            - private
                            - shared
                            - express-shared
                    unknown_http_version:
                        description:
                            - How to handle HTTP sessions that do not comply with HTTP 0.9, 1.0, or 1.1.
                        type: str
                        choices:
                            - reject
                            - tunnel
                            - best-effort
            mapi:
                description:
                    - Enable/disable MAPI email WAN Optimization and configure MAPI WAN Optimization features.
                type: dict
                suboptions:
                    byte_caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        type: str
                        choices:
                            - enable
                            - disable
                    log_traffic:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for MAPI. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                        type: int
                    secure_tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        type: str
                        choices:
                            - enable
                            - disable
                    tunnel_sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        type: str
                        choices:
                            - private
                            - shared
                            - express-shared
            name:
                description:
                    - Profile name.
                required: true
                type: str
            tcp:
                description:
                    - Enable/disable TCP WAN Optimization and configure TCP WAN Optimization features.
                type: dict
                suboptions:
                    byte_caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        type: str
                        choices:
                            - enable
                            - disable
                    byte_caching_opt:
                        description:
                            - Select whether TCP byte-caching uses system memory only or both memory and disk space.
                        type: str
                        choices:
                            - mem-only
                            - mem-disk
                    log_traffic:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for TCP. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                        type: str
                    secure_tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        type: str
                        choices:
                            - enable
                            - disable
                    ssl:
                        description:
                            - Enable/disable SSL/TLS offloading.
                        type: str
                        choices:
                            - enable
                            - disable
                    ssl_port:
                        description:
                            - Port on which to expect HTTPS traffic for SSL/TLS offloading.
                        type: int
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        type: str
                        choices:
                            - enable
                            - disable
                    tunnel_sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        type: str
                        choices:
                            - private
                            - shared
                            - express-shared
            transparent:
                description:
                    - Enable/disable transparent mode.
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
  - name: Configure WAN optimization profiles.
    fortios_wanopt_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      wanopt_profile:
        auth_group: "<your_own_value> (source wanopt.auth-group.name)"
        cifs:
            byte_caching: "enable"
            log_traffic: "enable"
            port: "7"
            prefer_chunking: "dynamic"
            secure_tunnel: "enable"
            status: "enable"
            tunnel_sharing: "private"
        comments: "<your_own_value>"
        ftp:
            byte_caching: "enable"
            log_traffic: "enable"
            port: "16"
            prefer_chunking: "dynamic"
            secure_tunnel: "enable"
            status: "enable"
            tunnel_sharing: "private"
        http:
            byte_caching: "enable"
            log_traffic: "enable"
            port: "24"
            prefer_chunking: "dynamic"
            secure_tunnel: "enable"
            ssl: "enable"
            ssl_port: "28"
            status: "enable"
            tunnel_non_http: "enable"
            tunnel_sharing: "private"
            unknown_http_version: "reject"
        mapi:
            byte_caching: "enable"
            log_traffic: "enable"
            port: "36"
            secure_tunnel: "enable"
            status: "enable"
            tunnel_sharing: "private"
        name: "default_name_40"
        tcp:
            byte_caching: "enable"
            byte_caching_opt: "mem-only"
            log_traffic: "enable"
            port: "<your_own_value>"
            secure_tunnel: "enable"
            ssl: "enable"
            ssl_port: "48"
            status: "enable"
            tunnel_sharing: "private"
        transparent: "enable"
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


def filter_wanopt_profile_data(json):
    option_list = ['auth_group', 'cifs', 'comments',
                   'ftp', 'http', 'mapi',
                   'name', 'tcp', 'transparent']
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


def wanopt_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['wanopt_profile'] and data['wanopt_profile']:
        state = data['wanopt_profile']['state']
    else:
        state = True
    wanopt_profile_data = data['wanopt_profile']
    filtered_data = underscore_to_hyphen(filter_wanopt_profile_data(wanopt_profile_data))

    if state == "present":
        return fos.set('wanopt',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('wanopt',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wanopt(data, fos):

    if data['wanopt_profile']:
        resp = wanopt_profile(data, fos)

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
        "wanopt_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "auth_group": {"required": False, "type": "str"},
                "cifs": {"required": False, "type": "dict",
                         "options": {
                             "byte_caching": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                             "log_traffic": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "port": {"required": False, "type": "int"},
                             "prefer_chunking": {"required": False, "type": "str",
                                                 "choices": ["dynamic", "fix"]},
                             "secure_tunnel": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "tunnel_sharing": {"required": False, "type": "str",
                                                "choices": ["private", "shared", "express-shared"]}
                         }},
                "comments": {"required": False, "type": "str"},
                "ftp": {"required": False, "type": "dict",
                        "options": {
                            "byte_caching": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                            "log_traffic": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                            "port": {"required": False, "type": "int"},
                            "prefer_chunking": {"required": False, "type": "str",
                                                "choices": ["dynamic", "fix"]},
                            "secure_tunnel": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                            "status": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                            "tunnel_sharing": {"required": False, "type": "str",
                                               "choices": ["private", "shared", "express-shared"]}
                        }},
                "http": {"required": False, "type": "dict",
                         "options": {
                             "byte_caching": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                             "log_traffic": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "port": {"required": False, "type": "int"},
                             "prefer_chunking": {"required": False, "type": "str",
                                                 "choices": ["dynamic", "fix"]},
                             "secure_tunnel": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                             "ssl": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                             "ssl_port": {"required": False, "type": "int"},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "tunnel_non_http": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                             "tunnel_sharing": {"required": False, "type": "str",
                                                "choices": ["private", "shared", "express-shared"]},
                             "unknown_http_version": {"required": False, "type": "str",
                                                      "choices": ["reject", "tunnel", "best-effort"]}
                         }},
                "mapi": {"required": False, "type": "dict",
                         "options": {
                             "byte_caching": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                             "log_traffic": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "port": {"required": False, "type": "int"},
                             "secure_tunnel": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "tunnel_sharing": {"required": False, "type": "str",
                                                "choices": ["private", "shared", "express-shared"]}
                         }},
                "name": {"required": True, "type": "str"},
                "tcp": {"required": False, "type": "dict",
                        "options": {
                            "byte_caching": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                            "byte_caching_opt": {"required": False, "type": "str",
                                                 "choices": ["mem-only", "mem-disk"]},
                            "log_traffic": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                            "port": {"required": False, "type": "str"},
                            "secure_tunnel": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                            "ssl": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                            "ssl_port": {"required": False, "type": "int"},
                            "status": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                            "tunnel_sharing": {"required": False, "type": "str",
                                               "choices": ["private", "shared", "express-shared"]}
                        }},
                "transparent": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_wanopt(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_wanopt(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
